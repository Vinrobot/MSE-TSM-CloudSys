from azure.identity import AzureCliCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.network.v2020_06_01.models import NetworkSecurityGroup, SecurityRule, SecurityRuleAccess, SecurityRuleDirection, SecurityRuleProtocol
from base64 import b64encode
import re

SUBSCRIPTION_ID = 'b78df499-efc9-4959-9b04-488a05dd34d9'
RESOURCE_GROUP_NAME = "MSE-TSM-CloudSys-Lab1"
LOCATION = "westeurope"
STORAGE_LOCATION = 'switzerlandnorth'
STORAGE_NAME = re.sub('[^a-z0-9]', '', RESOURCE_GROUP_NAME.lower())[0:24]

BACKEND_IMAGE_ID = f'/subscriptions/{SUBSCRIPTION_ID}/resourceGroups/{RESOURCE_GROUP_NAME}/providers/Microsoft.Compute/images/{RESOURCE_GROUP_NAME}-backend-image'
FRONTEND_IMAGE_ID = f'/subscriptions/{SUBSCRIPTION_ID}/resourceGroups/{RESOURCE_GROUP_NAME}/providers/Microsoft.Compute/images/{RESOURCE_GROUP_NAME}-frontend-image'

USERNAME, PASSWORD = 'azureuser', 'zW9YD%V$E88q'


credential = AzureCliCredential()
compute_client = ComputeManagementClient(credential, SUBSCRIPTION_ID)
resource_client = ResourceManagementClient(credential, SUBSCRIPTION_ID)
network_client = NetworkManagementClient(credential, SUBSCRIPTION_ID)
storage_client = StorageManagementClient(credential, SUBSCRIPTION_ID)


def create_storage_account(account_name):
    poller = storage_client.storage_accounts.begin_create(RESOURCE_GROUP_NAME, account_name, {
        "location" : STORAGE_LOCATION,
        "kind": "StorageV2",
        "sku": {"name": "Standard_LRS"}
    })
    account_result = poller.result()
    print(f"Provisioned storage account {account_result.name}")

    keys = storage_client.storage_accounts.list_keys(RESOURCE_GROUP_NAME, account_name)
    return f"DefaultEndpointsProtocol=https;EndpointSuffix=core.windows.net;AccountName={account_name};AccountKey={keys.keys[0].value}"

def create_virtual_network(vnet_name):
    poller = network_client.virtual_networks.begin_create_or_update(RESOURCE_GROUP_NAME, vnet_name, {
        "location": LOCATION,
        "address_space": { "address_prefixes": ["10.0.0.0/16"] }
    })
    vnet_result = poller.result()
    print(f'Provisioned virtual network {vnet_result.name} with address prefixes {vnet_result.address_space.address_prefixes}')
    return vnet_result

def create_subnet(vnet_name, subnet_name):
    poller = network_client.subnets.begin_create_or_update(RESOURCE_GROUP_NAME, vnet_name, subnet_name, {
        "address_prefix": "10.0.0.0/24"
    })
    subnet_result = poller.result()
    print(f'Provisioned virtual subnet {subnet_result.name} with address prefix {subnet_result.address_prefix}')
    return subnet_result

def create_ip(ip_name):
    poller = network_client.public_ip_addresses.begin_create_or_update(RESOURCE_GROUP_NAME, ip_name, {
        "location": LOCATION,
        "sku": { "name": "Standard" },
        "public_ip_allocation_method": "Static",
        "public_ip_address_version" : "IPV4"
    })
    ip_address_result = poller.result()
    print(f'Provisioned public IP address {ip_address_result.name} with address {ip_address_result.ip_address}')
    return ip_address_result

def create_network_security_group(nsg_name):
    def new_rule(name, port, priority):
        return SecurityRule(
            name=name,
            access=SecurityRuleAccess.allow,
            destination_address_prefix='*',
            destination_port_range=port,
            direction=SecurityRuleDirection.inbound,
            priority=priority,
            protocol=SecurityRuleProtocol.tcp,
            source_address_prefix='*',
            source_port_range='*',
        )

    nsg_params = NetworkSecurityGroup(
        location=LOCATION,
        security_rules=[
            new_rule('SSH-22', '22', 501),
            new_rule('HTTP-3000', '3000', 502),
            new_rule('HTTP-8080', '8080', 503),
        ],
    )
    poller = network_client.network_security_groups.begin_create_or_update(RESOURCE_GROUP_NAME, nsg_name, parameters=nsg_params)
    nsg_result = poller.result()
    print(f'Provisioned network security group {nsg_result.name}')
    return nsg_result

def create_network_interface(subnet_result_id, ip_address_result_id, network_security_group_id, nic_name, ip_config_name):
    poller = network_client.network_interfaces.begin_create_or_update(RESOURCE_GROUP_NAME, nic_name, {
        "location": LOCATION,
        "ip_configurations": [ {
            "name": ip_config_name,
            "subnet": { "id": subnet_result_id },
            "public_ip_address": { "id": ip_address_result_id }
        }],
        'network_security_group':{
            'id' : network_security_group_id,
        },
    })
    nic_result = poller.result()
    print(f'Provisioned network interface client {nic_result.name}')
    return nic_result

def create_virtual_machine(nic_id, vm_name, username, password, cloud_init=None, image_id=None):
    if cloud_init:
        cloud_init = b64encode(cloud_init.encode('ascii')).decode('utf-8')

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

    print(f'Provisioning virtual machine {vm_name}; this operation might take a few minutes.')
    poller = compute_client.virtual_machines.begin_create_or_update(RESOURCE_GROUP_NAME, vm_name,
        {
            "location": LOCATION,
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
                "custom_data": cloud_init,
                "linux_configuration": {
                    "disable_password_authentication": True,
                    "ssh": {
                        "public_keys": [
                            {
                                "path": f'/home/{username}/.ssh/authorized_keys',
                                "key_data": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDGMGyRbHn88mwKpHM9DhXqyGKe74+RGs4w/vKrKvkm1H52uBAicDJGQNYXbHWq+E0YReV7AHwhjPpRIgXtp4ofNgiygGzE8J8niSfABzYQIf0v7/gkMi6nNPp3tRYEBBVDX3VaFNynrFmn2/gt5g8Zp5KcXox6VSI0/b2A88Tc3opzr/12Wz4Y/vzeZgzT4wqGizuAByt/YnXwVmjuHRm0uCCOUv5GyUsCCLdFH0inqM/hHmOO452gbVRvVQOzeWliAjCeNETHD9tBgHHcJ3tthouAIDzB8KFKWqqbgD4ncN7S071uiOBY4yIsQZh0r2c1VTDg6vZXQaK6+4JdRgJUp9QDnuU2GcOZqcKNY4JrvksqOe3vCs3+YgJY6sxXo3AMk1Ef6nkmT8Eq4lwJ6oVX2UnhP1DbUgQWejJI+CES12U7OtEfMJwZCoRDHTunXevFvbvL7SOb8N37oNnpZ0lR7Yzs4zs+3PVtR9hJxULs6TkHh7q1meJwSieD7XexVYXX55JyuJcGuwZTLkRRMsQAgIXtkNq4SASbbWTre4ZDn1klRt6W9atv3Lj9mPNypoCZlIgAshix2xH20lWrBTRrmZzfJ+c+7AoyxfFof2w2X6bzI1JlGWp6QwcYUQMKjA6Ytsw+mRHF8+XshZduaBrQ0DJ09bczm2KvdEqVAIMl+Q== vinrobot97@gmail.com"
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
    vm_result = poller.result()
    print(f'Provisioned virtual machine {vm_result.name}')
    return vm_result

def create_full_virtual_machine(subnet_id, network_security_group_id, vm_name, username, password, cloud_init=None, image_id=None):
    ip = create_ip(f'{vm_name}-ip')
    nic = create_network_interface(subnet_id, ip.id, network_security_group_id, f'{vm_name}-nic', f'{vm_name}-ip-config')
    return ip, nic, create_virtual_machine(nic.id, vm_name, username, password, cloud_init, image_id)


resource_group = resource_client.resource_groups.create_or_update(RESOURCE_GROUP_NAME, { "location": LOCATION })
print(f'Provisioned resource group {resource_group.name} in the {resource_group.location} region')

connection_string = create_storage_account(STORAGE_NAME)

vnet = create_virtual_network(f'{resource_group.name}-vnet')
subnet = create_subnet(f'{resource_group.name}-vnet', f'{resource_group.name}-subnet')
nsg = create_network_security_group(f'{resource_group.name}-security-group')

ip, _, _ = create_full_virtual_machine(subnet.id, nsg.id, f'{resource_group.name}-backend', USERNAME, PASSWORD, f'''
#cloud-config
runcmd:
 - echo "AZURE_STORAGE_CONNECTION_STRING={connection_string}" > /home/{USERNAME}/SatNOGS-Tracker-Cloud/.env
 - echo "AZURE_STORAGE_CONTAINER_NAME={STORAGE_NAME}" >> /home/{USERNAME}/SatNOGS-Tracker-Cloud/.env
''', BACKEND_IMAGE_ID)

create_full_virtual_machine(subnet.id, nsg.id, f'{resource_group.name}-frontend', USERNAME, PASSWORD, f'''
#cloud-config
runcmd:
 - echo "BACKEND_URL=http://{ip.ip_address}:8080" > /home/{USERNAME}/SatNOGS-Tracker-Cloud/.env
''', FRONTEND_IMAGE_ID)
