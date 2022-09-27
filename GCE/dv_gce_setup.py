import re
import sys
from typing import Any, List
import warnings

from google.api_core.extended_operation import ExtendedOperation
from google.cloud import compute_v1
from google.cloud import storage

PROJECT_ID = "cloudsys-grp12"
ZONE = "europe-west3-a"
BUCKET_NAME = "cloudsys-grp12-bucket"

AMI_BACKEND = "cloudsys-lab1-backend"
AMI_FRONTEND = "cloudsys-lab1-frontend"

S3_KEY = ""
S3_SECRET = ""

def create_key(project_id, service_account_email):
    """
    Create a new HMAC key using the given project and service account.
    """
    # project_id = 'Your Google Cloud project ID'
    # service_account_email = 'Service account used to generate the HMAC key'

    storage_client = storage.Client(project=project_id)

    hmac_key, secret = storage_client.create_hmac_key(
        service_account_email=service_account_email, project_id=project_id
    )

    print(f"The base64 encoded secret is {secret}")
    print("Do not miss that secret, there is no API to recover it.")
    print("The HMAC key metadata is:")
    print(f"Service Account Email: {hmac_key.service_account_email}")
    print(f"Key ID: {hmac_key.id}")
    print(f"Access ID: {hmac_key.access_id}")
    print(f"Project ID: {hmac_key.project}")
    print(f"State: {hmac_key.state}")
    print(f"Created At: {hmac_key.time_created}")
    print(f"Updated At: {hmac_key.updated}")
    print(f"Etag: {hmac_key.etag}")
    return hmac_key, secret

def get_image_from_family(project: str, family: str) -> compute_v1.Image:
    """
    Retrieve the newest image that is part of a given family in a project.

    Args:
        project: project ID or project number of the Cloud project you want to get image from.
        family: name of the image family you want to get image from.

    Returns:
        An Image object.
    """
    image_client = compute_v1.ImagesClient()
    # List of public operating system (OS) images: https://cloud.google.com/compute/docs/images/os-details
    newest_image = image_client.get_from_family(project=project, family=family)
    return newest_image

def disk_from_image(
    disk_type: str,
    disk_size_gb: int,
    boot: bool,
    source_image: str,
    auto_delete: bool = True,
) -> compute_v1.AttachedDisk:
    """
    Create an AttachedDisk object to be used in VM instance creation. Uses an image as the
    source for the new disk.

    Args:
         disk_type: the type of disk you want to create. This value uses the following format:
            "zones/{zone}/diskTypes/(pd-standard|pd-ssd|pd-balanced|pd-extreme)".
            For example: "zones/us-west3-b/diskTypes/pd-ssd"
        disk_size_gb: size of the new disk in gigabytes
        boot: boolean flag indicating whether this disk should be used as a boot disk of an instance
        source_image: source image to use when creating this disk. You must have read access to this disk. This can be one
            of the publicly available images or an image from one of your projects.
            This value uses the following format: "projects/{project_name}/global/images/{image_name}"
        auto_delete: boolean flag indicating whether this disk should be deleted with the VM that uses it

    Returns:
        AttachedDisk object configured to be created using the specified image.
    """
    boot_disk = compute_v1.AttachedDisk()
    initialize_params = compute_v1.AttachedDiskInitializeParams()
    initialize_params.source_image = source_image
    initialize_params.disk_size_gb = disk_size_gb
    initialize_params.disk_type = disk_type
    boot_disk.initialize_params = initialize_params
    # Remember to set auto_delete to True if you want the disk to be deleted when you delete
    # your VM instance.
    boot_disk.auto_delete = auto_delete
    boot_disk.boot = boot
    return boot_disk

def wait_for_extended_operation(
    operation: ExtendedOperation, verbose_name: str = "operation", timeout: int = 300
) -> Any:
    """
    This method will wait for the extended (long-running) operation to
    complete. If the operation is successful, it will return its result.
    If the operation ends with an error, an exception will be raised.
    If there were any warnings during the execution of the operation
    they will be printed to sys.stderr.

    Args:
        operation: a long-running operation you want to wait on.
        verbose_name: (optional) a more verbose name of the operation,
            used only during error and warning reporting.
        timeout: how long (in seconds) to wait for operation to finish.
            If None, wait indefinitely.

    Returns:
        Whatever the operation.result() returns.

    Raises:
        This method will raise the exception received from `operation.exception()`
        or RuntimeError if there is no exception set, but there is an `error_code`
        set for the `operation`.

        In case of an operation taking longer than `timeout` seconds to complete,
        a `concurrent.futures.TimeoutError` will be raised.
    """
    result = operation.result(timeout=timeout)

    if operation.error_code:
        print(
            f"Error during {verbose_name}: [Code: {operation.error_code}]: {operation.error_message}",
            file=sys.stderr,
            flush=True,
        )
        print(f"Operation ID: {operation.name}", file=sys.stderr, flush=True)
        raise operation.exception() or RuntimeError(operation.error_message)

    if operation.warnings:
        print(f"Warnings during {verbose_name}:\n", file=sys.stderr, flush=True)
        for warning in operation.warnings:
            print(f" - {warning.code}: {warning.message}", file=sys.stderr, flush=True)

    return result

def create_instance(
    project_id: str,
    zone: str,
    instance_name: str,
    disks: List[compute_v1.AttachedDisk],
    machine_type: str = "n1-standard-1",
    network_link: str = "global/networks/default",
    boot_script: str = None,
    tags: List[str] = [],
    subnetwork_link: str = None,
    internal_ip: str = None,
    external_access: bool = False,
    external_ipv4: str = None,
    accelerators: List[compute_v1.AcceleratorConfig] = None,
    preemptible: bool = False,
    spot: bool = False,
    instance_termination_action: str = "STOP",
    custom_hostname: str = None,
    delete_protection: bool = False,
) -> compute_v1.Instance:
    """
    Send an instance creation request to the Compute Engine API and wait for it to complete.

    Args:
        project_id: project ID or project number of the Cloud project you want to use.
        zone: name of the zone to create the instance in. For example: "us-west3-b"
        instance_name: name of the new virtual machine (VM) instance.
        disks: a list of compute_v1.AttachedDisk objects describing the disks
            you want to attach to your new instance.
        machine_type: machine type of the VM being created. This value uses the
            following format: "zones/{zone}/machineTypes/{type_name}".
            For example: "zones/europe-west3-c/machineTypes/f1-micro"
        network_link: name of the network you want the new instance to use.
            For example: "global/networks/default" represents the network
            named "default", which is created automatically for each project.
        subnetwork_link: name of the subnetwork you want the new instance to use.
            This value uses the following format:
            "regions/{region}/subnetworks/{subnetwork_name}"
        internal_ip: internal IP address you want to assign to the new instance.
            By default, a free address from the pool of available internal IP addresses of
            used subnet will be used.
        external_access: boolean flag indicating if the instance should have an external IPv4
            address assigned.
        external_ipv4: external IPv4 address to be assigned to this instance. If you specify
            an external IP address, it must live in the same region as the zone of the instance.
            This setting requires `external_access` to be set to True to work.
        accelerators: a list of AcceleratorConfig objects describing the accelerators that will
            be attached to the new instance.
        preemptible: boolean value indicating if the new instance should be preemptible
            or not. Preemptible VMs have been deprecated and you should now use Spot VMs.
        spot: boolean value indicating if the new instance should be a Spot VM or not.
        instance_termination_action: What action should be taken once a Spot VM is terminated.
            Possible values: "STOP", "DELETE"
        custom_hostname: Custom hostname of the new VM instance.
            Custom hostnames must conform to RFC 1035 requirements for valid hostnames.
        delete_protection: boolean value indicating if the new virtual machine should be
            protected against deletion or not.
    Returns:
        Instance object.
    """
    instance_client = compute_v1.InstancesClient()

    # Use the network interface provided in the network_link argument.
    network_interface = compute_v1.NetworkInterface()
    network_interface.name = network_link
    if subnetwork_link:
        network_interface.subnetwork = subnetwork_link

    if internal_ip:
        network_interface.network_i_p = internal_ip

    if external_access:
        access = compute_v1.AccessConfig()
        access.type_ = compute_v1.AccessConfig.Type.ONE_TO_ONE_NAT.name
        access.name = "External NAT"
        access.network_tier = access.NetworkTier.PREMIUM.name
        if external_ipv4:
            access.nat_i_p = external_ipv4
        network_interface.access_configs = [access]

    # Collect information into the Instance object.
    instance = compute_v1.Instance()
    instance.network_interfaces = [network_interface]
    instance.name = instance_name
    instance.tags = compute_v1.Tags(items=tags)
    instance.disks = disks
    if re.match(r"^zones/[a-z\d\-]+/machineTypes/[a-z\d\-]+$", machine_type):
        instance.machine_type = machine_type
    else:
        instance.machine_type = f"zones/{zone}/machineTypes/{machine_type}"

    if accelerators:
        instance.guest_accelerators = accelerators

    if preemptible:
        # Set the preemptible setting
        warnings.warn(
            "Preemptible VMs are being replaced by Spot VMs.", DeprecationWarning
        )
        instance.scheduling = compute_v1.Scheduling()
        instance.scheduling.preemptible = True

    if spot:
        # Set the Spot VM setting
        instance.scheduling = compute_v1.Scheduling()
        instance.scheduling.provisioning_model = (
            compute_v1.Scheduling.ProvisioningModel.SPOT.name
        )
        instance.scheduling.instance_termination_action = instance_termination_action

    if custom_hostname is not None:
        # Set the custom hostname for the instance
        instance.hostname = custom_hostname

    if delete_protection:
        # Set the delete protection bit
        instance.deletion_protection = True

    if boot_script:
        # Set the boot script for the instance
        instance.metadata = compute_v1.Metadata()
        instance.metadata.items = [
            compute_v1.Items(key="startup-script", value=boot_script)
        ]

    # Prepare the request to insert an instance.
    request = compute_v1.InsertInstanceRequest()
    request.zone = zone
    request.project = project_id
    request.instance_resource = instance

    # Wait for the create operation to complete.
    print(f"Creating the {instance_name} instance in {zone}...")

    operation = instance_client.insert(request=request)

    wait_for_extended_operation(operation, "instance creation")

    print(f"Instance {instance_name} created.")
    return instance_client.get(project=project_id, zone=zone, instance=instance_name)

def create_bucket(name):
    """Creates a new bucket."""
    # The ID of your GCS bucket
    # bucket_name = "your-new-bucket-name"

    storage_client = storage.Client(project=PROJECT_ID)

    bucket = storage_client.create_bucket(name, location="EU")

    print(f"Bucket {bucket.name} created.")

    return bucket

# Create a new bucket
try:
    bucket = create_bucket(BUCKET_NAME)
    print("Bucket {} created.".format(bucket.name))

except:
    print("Bucket {} already exists.".format(BUCKET_NAME))

# Get the backend image
backend_image = get_image_from_family(PROJECT_ID, AMI_BACKEND)

# Get the frontend image
frontend_image = get_image_from_family(PROJECT_ID, AMI_FRONTEND)

# Create a new disk for the backend from the specified image.
backend_disk = disk_from_image(
    disk_type=f"zones/{ZONE}/diskTypes/pd-standard",
    disk_size_gb=10,
    boot=True,
    source_image=backend_image.self_link
)
print("Backend disk created.")

# Create a new disk for the frontend from the specified image.
frontend_disk = disk_from_image(
    disk_type=f"zones/{ZONE}/diskTypes/pd-standard",
    disk_size_gb=10,
    boot=True,
    source_image=frontend_image.self_link
)
print("Frontend disk created.")

# Create the backend instance and set the bucket address as an environment variable.
# With backend tag
backend_instance = create_instance(
    project_id=PROJECT_ID,
    zone=ZONE,
    instance_name="backend-instance",
    disks=[backend_disk],
    machine_type="e2-micro",
    external_access=True,
    tags=["backend"],
    boot_script=f"""#!/bin/bash
    echo "export BUCKET_NAME={BUCKET_NAME}" > /home/ec2-user/SatNOGS-Tracker-Cloud/.env
    echo "export AWS_KEY={S3_KEY}" >> /home/ec2-user/SatNOGS-Tracker-Cloud/.env
    echo "export AWS_SECRET={S3_SECRET}" >> /home/ec2-user/SatNOGS-Tracker-Cloud/.env
    echo "export IS_GOOGLE=1" >> /home/ec2-user/SatNOGS-Tracker-Cloud/.env
    """
)

# Get the internal IP address of the backend instance
backend_ip = backend_instance.network_interfaces[0].network_i_p
print(f"Backend IP: {backend_ip}")

# Create the frontend instance and set the backend IP address as an environment variable.
frontend_instance = create_instance(
    project_id=PROJECT_ID,
    zone=ZONE,
    instance_name="frontend-instance",
    disks=[frontend_disk],
    machine_type="e2-micro",
    external_access=True,
    tags=["frontend"],
    boot_script=f"""#!/bin/bash
    echo "export BACKEND_URL=http://{backend_ip}:8080" > /home/ec2-user/SatNOGS-Tracker-Cloud/.env
    """
)

print("Frontend instance created.")
print("Done!")