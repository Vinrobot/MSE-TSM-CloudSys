import boto3

# This script assumes you have already created the right security groups,
# IAM role and key pairs

REGION = 'eu-central-1'

BACKEND_AMI = 'ami-0eacf1e0c44e181d1'
FRONTEND_AMI = 'ami-0d24f1695911b7942'

BACKEND_KEY_PAIR = 'GRP12_KP'
FRONTEND_KEY_PAIR = 'GRP12_KP'

S3_BUCKET_NAME = 'cloudsys-grp12-bucket'

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
    SecurityGroupIds=["sg-0e54eae0e9842a42f"],
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
    SecurityGroupIds=["sg-00b37ee0dfd4c202e"],
    KeyName=FRONTEND_KEY_PAIR,
    UserData=f"""#cloud-boothook
    #!/bin/bash
    echo "export BACKEND_URL=http://{backend_ip}:8080" > /home/ec2-user/SatNOGS-Tracker-Cloud/.env
    """
)

print('Created frontend instance')
print('Done!')