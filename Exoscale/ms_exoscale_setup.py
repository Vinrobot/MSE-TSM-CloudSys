import exoscale

exo = exoscale.Exoscale()

#VAR
REGION = "ch-gva-2"
S3_BUCKET_NAME = "buckyg12"
SSH_KEY ="SSH Key"
VM_TYPE = "micro"
TEMPLATE_BACK = "2a0adbe7-aefe-4fbe-b8a1-057f7fb294bd"
TEMPLATE_FRONT = "63438932-64af-44fd-9734-8345befdef02"

api_key = exo.iam.create_api_key(
    "sos-access",
    "sos/*"
)
S3_BUCKET_KEY = api_key.key
S3_BUCKET_SECRET = api_key.secret

print("Creating the Object Storage Bucket")
bucket = exo.storage.create_bucket(S3_BUCKET_NAME, zone=REGION)

#Compute
#Zone Object 
zone = exo.compute.get_zone(REGION)


print("Security Group Definition")
security_group_app_g12 = exo.compute.create_security_group("app_g12")
for rule in [
    exoscale.api.compute.SecurityGroupRule.ingress(
        description="SSH",
        network_cidr="0.0.0.0/0",
        port="22",
        protocol="tcp"
    ),
    exoscale.api.compute.SecurityGroupRule.ingress(
        description="backend",
        network_cidr="0.0.0.0/0",
        port="8080",
        protocol="tcp"
    ),
    exoscale.api.compute.SecurityGroupRule.ingress(
        description="frontend",
        network_cidr="0.0.0.0/0",
        port="3000",
        protocol="tcp"
    ),
]:
    security_group_app_g12.add_rule(rule)


print("Create Instance : backend")
# Creating backend
instance_BACK = exo.compute.create_instance(
    name="BACK",
    zone=zone,
    type=exo.compute.get_instance_type(VM_TYPE),
    template=exo.compute.get_instance_template(zone, TEMPLATE_BACK),
    volume_size=10,
    security_groups=[security_group_app_g12],
    ssh_key=exo.compute.get_ssh_key(SSH_KEY),
    user_data=f"""#cloud-boothook
#!/bin/bash
cd /home/ubuntu/SatNOGS-Tracker-Cloud
echo "BUCKET_NAME={bucket.name}" > .env
echo "AWS_KEY={S3_BUCKET_KEY}" >> .env
echo "AWS_SECRET={S3_BUCKET_SECRET}" >> .env
node backend.js"""
)

BACK_IP = instance_BACK.ipv4_address

print("Create Instance : frontend")
# Creating frontend
instance_FRONT = exo.compute.create_instance(
    name="FRONT",
    zone=zone,
    type=exo.compute.get_instance_type(VM_TYPE),
    template=exo.compute.get_instance_template(zone, TEMPLATE_FRONT),
    volume_size=10,
    security_groups=[security_group_app_g12],
    ssh_key=exo.compute.get_ssh_key(SSH_KEY),
    user_data=f"""#cloud-boothook
#!/bin/bash
cd /home/ubuntu/SatNOGS-Tracker-Cloud
echo "BACKEND_URL=http://{BACK_IP}:8080" > .env
node web.js"""
)


FRONT_IP = instance_FRONT.ipv4_address

print("FRONT IP : " + FRONT_IP)
print("BACK IP : " + BACK_IP)