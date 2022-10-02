import openstack, re
from time import sleep
from base64 import b64encode

# openstack.enable_logging(debug=True)

PROJECT_NAME = 'MSE-TSM-CloudSys-Lab1'
BACKEND_NAME, FRONTEND_NAME = f'{PROJECT_NAME}-Backend', f'{PROJECT_NAME}-Frontend'
BACKEND_IMAGE, FRONTEND_IMAGE = f'{BACKEND_NAME}-Image', f'{FRONTEND_NAME}-Image'
KEYPAIR_NAME = 'Vincent Jaquet - Macbook Pro 2018'
INSTANCE_FLAVOR = 'c1.small'
SECURITY_GROUPS = ['default', 'http', 'ssh']
PRIVATE_NETWORK_NAME, PUBLIC_NETWORK_NAME = 'private', 'public'


AZURE_STORAGE_ACCOUNT_NAME = re.sub('[^a-z0-9]', '', PROJECT_NAME.lower())[0:24]
AZURE_STORAGE_ACCOUNT_KEY = 'ZDJYTjBwWlpHV0c3VTkzVEtXXjBKMCFSNm8mJGQyWE4wcFpa'
AZURE_STORAGE_CONNECTION_STRING = f"DefaultEndpointsProtocol=https;EndpointSuffix=core.windows.net;AccountName={AZURE_STORAGE_ACCOUNT_NAME};AccountKey={AZURE_STORAGE_ACCOUNT_KEY}"


conn = openstack.connect(cloud='switchengine')


KEYPAIR = conn.compute.find_keypair(KEYPAIR_NAME)
PUBLIC_NETWORK = conn.network.find_network(PUBLIC_NETWORK_NAME)
PRIVATE_NETWORK = conn.network.find_network(PRIVATE_NETWORK_NAME)
INSTANCE_FLAVOR = conn.compute.find_flavor(INSTANCE_FLAVOR)
BACKEND_IMAGE = conn.compute.find_image(BACKEND_IMAGE)
FRONTEND_IMAGE = conn.compute.find_image(FRONTEND_IMAGE)
SECURITY_GROUPS = [conn.network.find_security_group(name) for name in SECURITY_GROUPS]


def clean(conn):
    for server in conn.list_servers():
        print(f' - Server: {server.name}')
        conn.compute.delete_server(server.id)
        sleep(1)

    for ip in conn.list_floating_ips():
        print(f' - Floating IP: {ip.floating_ip_address}')
        conn.network.delete_ip(ip.id)
        sleep(1)

    for volume in conn.list_volumes():
        try:
            conn.volume.delete_volume(volume.id)
            print(f' - Volume: {volume.id}')
        except:
            pass


def create_compute_instance(conn, name, image, user_data=None):
    if user_data:
        user_data = b64encode(user_data.encode('ascii')).decode('utf-8')

    # Remove existing
    server = conn.compute.find_server(name)
    if server:
        conn.compute.delete_server(server.id)

    # Create new
    server = conn.compute.create_server(
        name=name,
        image_id=image.id,
        flavor_id=INSTANCE_FLAVOR.id,
        networks=[{"uuid": PRIVATE_NETWORK.id}],
        key_name=KEYPAIR.name,
        security_groups=[{"name": sg.name} for sg in SECURITY_GROUPS],
        user_data=user_data,
    )
    server = conn.compute.wait_for_server(server)
    print(f'Provisioned compute instance {server.name}')

    # Create and link floating IP
    ip = conn.network.find_available_ip()
    if not ip:
        ip = conn.network.create_ip(floating_network_id=PUBLIC_NETWORK.id)
    conn.compute.add_floating_ip_to_server(server, ip.floating_ip_address)
    print(f'Provisioned floating ip {ip.floating_ip_address} to {server.name}')

    return ip, server


print('Cleaning...')
clean(conn)
print('Cleaned\n')


backend_ip, backend = create_compute_instance(conn, BACKEND_NAME, BACKEND_IMAGE, f'''
#cloud-config
runcmd:
 - echo "AZURE_STORAGE_CONNECTION_STRING={AZURE_STORAGE_CONNECTION_STRING}" > /home/debian/SatNOGS-Tracker-Cloud/.env
 - echo "AZURE_STORAGE_CONTAINER_NAME={AZURE_STORAGE_ACCOUNT_NAME}" >> /home/debian/SatNOGS-Tracker-Cloud/.env
''')
print(f'Backend provisioned {backend.name} with IP {backend_ip.floating_ip_address}')

frontend_ip, frontend = create_compute_instance(conn, FRONTEND_NAME, FRONTEND_IMAGE, f'''
#cloud-config
runcmd:
 - echo "BACKEND_URL=http://{backend_ip.floating_ip_address}:8080" > /home/debian/SatNOGS-Tracker-Cloud/.env
''')
print(f'Backend provisioned {frontend.name} with IP {frontend_ip.floating_ip_address}')
