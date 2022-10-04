from azure.identity import AzureCliCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network.v2020_06_01.models import StorageManagementClient, NetworkSecurityGroup, SecurityRule, SecurityRuleAccess, SecurityRuleDirection, SecurityRuleProtocol
from base64 import b64encode
import re

# VAR
REGION = "westeurope"
STORAGE_REGION = "switzerlandnorth"
STORAGE_NAME = "app_g12"
SSH_KEY = "ssh-rsa ..." #This info has been removed from the file

SUBSCRIPTION_ID = 'd60cf023-6a1f-4ac0-9dc9-f611d738567d'
RESOURCE_GROUP = "app_g12"

SSH_USERNAME = "azureuser"
PASSWORD = ""

TEMPLATE_BACK = f"/subscriptions/{SUBSCRIPTION_ID}/resourceGroups/{RESOURCE_GROUP}/providers/Microsoft.Compute/images/{RESOURCE_GROUP}-BACK-image"
TEMPLATE_FRONT = f"/subscriptions/{SUBSCRIPTION_ID}/resourceGroups/{RESOURCE_GROUP}/providers/Microsoft.Compute/images/{RESOURCE_GROUP}-FRONT-image"


credential = AzureCliCredential()
compute_client = ComputeManagementClient(credential, SUBSCRIPTION_ID)
resource_client = ResourceManagementClient(credential, SUBSCRIPTION_ID)
network_client = NetworkManagementClient(credential, SUBSCRIPTION_ID)
storage_client = StorageManagementClient(credential, SUBSCRIPTION_ID)


def create_ip(ip_name):
    request = network_client.public_ip_addresses.begin_create_or_update(RESOURCE_GROUP, ip_name, {
        "location": REGION,
        "sku": { "name": "Standard" },
        "public_ip_allocation_method": "Static",
        "public_ip_address_version" : "IPV4"
    })
    ip_address_result = request.result()
    return ip_address_result

def create_network_interface(subnet_result_id, ip_address_result_id, network_security_group_id, nic_name, ip_config_name):
    request = network_client.network_interfaces.begin_create_or_update(RESOURCE_GROUP, nic_name, {
        "location": REGION,
        "ip_configurations": [ {
            "name": ip_config_name,
            "subnet": { "id": subnet_result_id },
            "public_ip_address": { "id": ip_address_result_id }
        }],
        'network_security_group':{
            'id' : network_security_group_id,
        },
    })
    network_interface_result = request.result()
    return network_interface_result

def create_virtual_machine(nic_id, vm_name, username, password, user_data=None, image_id=None):
    if user_data:
        user_data = b64encode(user_data.encode('ascii')).decode('utf-8')

    if image_id:
        image_reference = {
            "id": image_id,
        }
    else:
        image_reference = {
            "publisher": 'canonical',
            "offer": "0001-com-ubuntu-server-focal",
            "sku": "20_04-lts-gen2",
            "version": "latest",
        }
    request = compute_client.virtual_machines.begin_create_or_update(RESOURCE_GROUP, vm_name,
        {
            "location": REGION,
            "storage_profile": {
                "image_reference": image_reference,
            },
            "hardware_profile": {
                "vm_size": "Standard_B1s",
            },
            "os_profile": {
                "computer_name": vm_name,
                "admin_username": username,
                "admin_password": password,
                "custom_data": user_data,
                "linux_configuration": {
                    "disable_password_authentication": True,
                    "ssh": {
                        "public_keys": [
                            {
                                "path": f'/home/{username}/.ssh/authorized_keys',
                                "key_data": SSH_KEY
                            },
                        ],
                    },
                },
            },
            "network_profile": {
                "network_interfaces": [{
                    "id": nic_id,
                }],
            },
        }
    )
    vm_result = request.result()
    return vm_result


# Resource Group Creation
resource_group = resource_client.resource_groups.create_or_update(RESOURCE_GROUP, {
    "location": REGION
})
print(f"Creating resource group : {resource_group.name}")

# Storage account Creation
request = storage_client.storage_accounts.begin_create(RESOURCE_GROUP, STORAGE_NAME, {
    "location" : STORAGE_REGION,
    "kind": "StorageV2",
    "sku": {"name": "Standard_LRS"}
})
storage_account = request.result()
print(f"Creating storage account {storage_account.name}")
keys = storage_client.storage_accounts.list_keys(RESOURCE_GROUP, storage_account)
connection_infos = f"DefaultEndpointsProtocol=https;EndpointSuffix=core.windows.net;AccountName={storage_account};AccountKey={keys.keys[0].value}"

# Virtual Network Creation
request = network_client.virtual_networks.begin_create_or_update(RESOURCE_GROUP, f"{resource_group.name}-vnet", {
        "location": REGION,
        "address_space": { "address_prefixes": ["10.0.0.0/16"] }
    })
virtual_network = request.result()
print(f"Creating virtual network : {virtual_network.name}")

# Virtual Subnet Creation
request = network_client.subnets.begin_create_or_update(RESOURCE_GROUP, f"{resource_group.name}-vnet", f"{resource_group.name}-subnet", {
        "address_prefix": "10.0.0.0/24"
    })
virtual_subnet = request.result()
print(f"Creating virtual subnet : {virtual_subnet.name}")

# Network Security Group Creation
network_security_params = NetworkSecurityGroup(
        location=REGION,
        security_rules=[
            SecurityRule(
                name='SSH-22',
                access=SecurityRuleAccess.allow,
                destination_address_prefix='*',
                destination_port_range='22',
                direction=SecurityRuleDirection.inbound,
                priority=501,
                protocol=SecurityRuleProtocol.tcp,
                source_address_prefix='*',
                source_port_range='*',
            ),
            SecurityRule(
                name='HTTP-3000',
                access=SecurityRuleAccess.allow,
                destination_address_prefix='*',
                destination_port_range='3000',
                direction=SecurityRuleDirection.inbound,
                priority=502,
                protocol=SecurityRuleProtocol.tcp,
                source_address_prefix='*',
                source_port_range='*',
            ),
            SecurityRule(
                name='HTTP-8080',
                access=SecurityRuleAccess.allow,
                destination_address_prefix='*',
                destination_port_range='8080',
                direction=SecurityRuleDirection.inbound,
                priority=502,
                protocol=SecurityRuleProtocol.tcp,
                source_address_prefix='*',
                source_port_range='*',
            ),
        ],
    )
request = network_client.network_security_groups.begin_create_or_update(RESOURCE_GROUP, f"{resource_group.name}-security-group", parameters=network_security_params)
network_security_group = request.result()
print(f"Creating Network Security Group {network_security_group.name}")

# BACK Instance Creation
back_vm_name="BACK"
# --> BACK IP Allocation
ip_address_back = create_ip(f"{resource_group.name}-{back_vm_name}-ip")
print(f"Allocation of public IP address for {back_vm_name} : {ip_address_back.ip_address}")

# --> BACK Network Interface Creation
network_interface_back = create_network_interface(virtual_subnet.id, ip_address_back.id, network_security_group.id, f"{back_vm_name}-nic", f"{back_vm_name}-ip-config")
print(f'Creating network interface client {network_interface_back.name}')

# --> BACK VM Creation 
back_user_data = f'''
#cloud-config
runcmd:
 - echo "AZURE_STORAGE_CONNECTION_STRING={connection_infos}" > /home/{SSH_USERNAME}/SatNOGS-Tracker-Cloud/.env
 - echo "AZURE_STORAGE_CONTAINER_NAME={STORAGE_NAME}" >> /home/{SSH_USERNAME}/SatNOGS-Tracker-Cloud/.env
''',

print(f"Creating virtual machine {back_vm_name} ...")
create_virtual_machine(network_interface_back.id, back_vm_name, SSH_USERNAME, back_user_data, TEMPLATE_BACK)
print(f"Virtual machine {back_vm_name} has been Created")

# FRONT Instance Creation
front_vm_name="FRONT"
# --> FRONT IP Allocation
ip_address_front = create_ip(f"{resource_group.name}-{front_vm_name}-ip")
print(f"Allocation of public IP address for {front_vm_name} : {ip_address_front.ip_address}")

# --> FRONT Network Interface Creation
network_interface_front = create_network_interface(virtual_subnet.id, ip_address_front.id, network_security_group.id, f"{front_vm_name}-nic", f"{front_vm_name}-ip-config")
print(f'Creating network interface client {network_interface_front.name}')

# --> FRONT VM Creation 
front_user_data = f'''
#cloud-config
runcmd:
 - echo "BACKEND_URL=http://{ip_address_front.ip_address}:8080" > /home/{SSH_USERNAME}/SatNOGS-Tracker-Cloud/.env
'''


print(f"Creating virtual machine {front_vm_name} ...")
create_virtual_machine(network_interface_front.id, front_vm_name, SSH_USERNAME, PASSWORD , front_user_data, TEMPLATE_BACK)
print(f"Virtual machine {front_vm_name} has been Created")
