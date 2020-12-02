import boto3
from botocore.exceptions import ClientError

def delete_key(client, name):
    print("Deleting Key...")
    try:
        response = client.delete_key_pair(KeyName=name)

    except ClientError as e:
        print('\nERRO:', e)

def terminate_all_instances(resource, client):
    print("\nDeleting Instaces...")
    try:
        all_instaces = resource.instances.filter(Filters=[
            {'Name': 'tag:projeto', 'Values': ['orm-duarte']}
        ])
        instaces_id = []
        for instance in all_instaces:
            instaces_id.append(instance.id)
        if len(instaces_id) > 0:
            terminate_waiter = client.get_waiter('instance_terminated')
            all_instaces.terminate()
            terminate_waiter.wait(InstanceIds=instaces_id)        
        
    except ClientError as e:
        print("\nERRO:", e)

def delete_security_group(client, SECURITY_GROUP_ID=None, SECURITY_GROUP_NAME=None):
    print("Deleting security group...")
    try:
        if SECURITY_GROUP_ID != None:
            response = client.delete_security_group(GroupId=SECURITY_GROUP_ID)
        elif SECURITY_GROUP_NAME != None:
            response = client.delete_security_group(GroupName=SECURITY_GROUP_NAME)
        else:
            print("Missing args")
        
    except ClientError as e:
        print("\nERRO:",e)

def delete_auto_scaling(client):
    try:
        response = client.delete_auto_scaling_group(
        AutoScalingGroupName='orm-duarte',
        ForceDelete=True
        )
    except ClientError as e:
        print("\nERRO:",e)

def delete_launch_config(client):
    print("Deleting Launch Config...")
    try:
        response = client.delete_launch_configuration(
        LaunchConfigurationName='orm-duarte'
        )
    except ClientError as e:
        print("\nERRO:",e)

def delete_load_balancer(client):
    print("Deleting Load Balancer...")
    try:
        response = client.delete_load_balancer(
            LoadBalancerName='orm-duarte'
        )
    except ClientError as e:
        print("\nERRO:",e)


def delete_image(client):
    print("Deleting Image...")
    try:
        image = client.describe_images(
            Filters=[
                {
                    'Name': 'name',
                    'Values': ['orm-duarte']
                },
            ],
        )['Images']
        if(len(image) > 0):

            client.deregister_image(ImageId=image[0]['ImageId'])

    except ClientError as e:
        print('\nERRO:', e)



