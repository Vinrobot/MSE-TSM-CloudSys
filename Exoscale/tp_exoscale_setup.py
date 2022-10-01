import exoscale

exo = exoscale.Exoscale()

# Creating Object Storage Bucket
print("Creating Object Storage Bucket")
bucket = exo.storage.create_bucket("cloudsys-tp1", zone="ch-gva-2")

# Creating key to bucket
api_key = exo.iam.create_api_key(
    "sos-access",
    "sos/*"
)


S3_KEY = api_key.key
S3_SECRET = api_key.secret

print("Creating Firewall security group")
# Adding firewall security group
security_group_web = exo.compute.create_security_group("cloudsys-tp1")

for rule in [
    exoscale.api.compute.SecurityGroupRule.ingress(
        description="ssh",
        network_cidr="0.0.0.0/0",
        port="22",
        protocol="tcp",
    ),
    exoscale.api.compute.SecurityGroupRule.ingress(
        description="frontend",
        network_cidr="0.0.0.0/0",
        port="3000",
        protocol="tcp",
    ),
    exoscale.api.compute.SecurityGroupRule.ingress(
        description="backend",
        network_cidr="0.0.0.0/0",
        port="8080",
        protocol="tcp",
    )
]:
    security_group_web.add_rule(rule)

# Creating backend
zone_gva2 = exo.compute.get_zone("ch-gva-2")

print("Creating backend instance")
backend_instance = exo.compute.create_instance(
    name="backend",
    zone=zone_gva2,
    type=exo.compute.get_instance_type("micro"),
    template=exo.compute.get_instance_template(zone_gva2, "0c03a81d-b65c-4e3b-9c05-1acfe99f84d4"),
    volume_size=10,
    security_groups=[security_group_web],
    ssh_key=exo.compute.get_ssh_key("desktop"),
    user_data=f"""#cloud-boothook
#!/bin/bash
cd /home/ubuntu/SatNOGS-Tracker-Cloud
echo "BUCKET_NAME={bucket.name}" > .env
echo "AWS_KEY={S3_KEY}" >> .env
echo "AWS_SECRET={S3_SECRET}" >> .env
node backend.js"""
)

IPV4_BACKEND = backend_instance.ipv4_address

# Creating frontend
print("Creating frontend instance")

frontend_instance = exo.compute.create_instance(
    name="frontend",
    zone=zone_gva2,
    type=exo.compute.get_instance_type("micro"),
    template=exo.compute.get_instance_template(zone_gva2, "229a4e40-ee5a-45a5-97e9-7a2974073d1f"),
    volume_size=10,
    security_groups=[security_group_web],
    ssh_key=exo.compute.get_ssh_key("desktop"),
    user_data=f"""#cloud-boothook
#!/bin/bash
cd /home/ubuntu/SatNOGS-Tracker-Cloud
echo "BACKEND_URL=http://{IPV4_BACKEND}:8080" > .env
node web.js"""
)