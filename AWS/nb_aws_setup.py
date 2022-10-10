#based on dv_aws_setup.py

import boto3

# This script assumes you have already created the right security groups,
# IAM role and key pairs

REGION = 'eu-central-1'

BACKEND_AMI = 'ami-09edd6842f47510f2'
FRONTEND_AMI = 'ami-0cd4b54186bf37f31'

BACKEND_SECURITY_GROUP = "sg-02bd16347cfb50214" #launch-wizard-6
FRONTEND_SECURITY_GROUP = "sg-0af33571d9a7a8423" #frontend-sg

BACKEND_KEY_PAIR = 'NicolasCle'
FRONTEND_KEY_PAIR = 'NicolasCle'

S3_BUCKET_NAME = 's3-nico'

S3_KEY = ''
S3_SECRET = ''

### BUCKET CREATION ###

# Create an S3 bucket
try:
    s3 = boto3.resource('s3')
    s3.create_bucket(Bucket=S3_BUCKET_NAME, CreateBucketConfiguration={'LocationConstraint': REGION})

    print('Created S3 bucket')
except Exception as e:
    print(e)


### EC2 INSTANCES ###
# Create an EC2 instance and add the IAM role
ec2 = boto3.resource('ec2')
backend = ec2.create_instances(
    ImageId=BACKEND_AMI,
    MinCount=1,
    MaxCount=1,
    InstanceType='t2.micro',
    SecurityGroupIds=[BACKEND_SECURITY_GROUP],
    KeyName=BACKEND_KEY_PAIR,
    UserData=f"""#cloud-boothook
    #!/bin/bash
    echo "export BUCKET_NAME={S3_BUCKET_NAME}" > /home/ec2-user/SatNOGS-Tracker-Cloud/.env
    echo "export AWS_KEY={S3_KEY}" >> /home/ec2-user/SatNOGS-Tracker-Cloud/.env
    echo "export AWS_SECRET={S3_SECRET}" >> /home/ec2-user/SatNOGS-Tracker-Cloud/.env
    """
)

print('Created backend instance')

# Get the instance dns name
instance = backend[0]
instance.wait_until_running()
instance.load()

# Get the private IP address
backend_ip = instance.private_ip_address

print('Backend IP: ' + backend_ip)

# Create the frontend instance and add the backend dns name to the environment
frontend = ec2.create_instances(
    ImageId=FRONTEND_AMI,
    MinCount=1,
    MaxCount=1,
    InstanceType='t2.micro',
    SecurityGroupIds=[FRONTEND_SECURITY_GROUP],
    KeyName=FRONTEND_KEY_PAIR,
    UserData=f"""#cloud-boothook
    #!/bin/bash
    echo "export BACKEND_URL=http://{backend_ip}:8080" > /home/ec2-user/SatNOGS-Tracker-Cloud/.env
    """
)

print('Created frontend instance')

frontendIp = frontend[0].public_ip_address
print('Application deployed on: http://' + frontendIp + ':3000')