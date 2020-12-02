import boto3
from botocore.exceptions import ClientError
import time

def connect(region):
    client = boto3.client('ec2', region_name=region)
    resource = boto3.resource('ec2', region_name=region)
    elbv2 = boto3.client('elbv2', region_name=region)
    elb = boto3.client('elb', region_name = region)
    auto = boto3.client('autoscaling', region_name = region)
    return client, resource, elbv2, elb, auto

def create_key(client, name, path):
    print("Creating key...")

    try:
        response = client.create_key_pair(
            KeyName=name,
            TagSpecifications=[{
                'ResourceType': 'key-pair', 
                'Tags': [{'Key':'Name','Value':name}, {'Key':'aluno','Value':'duarte'}]}]
        )
        with open(path, "w") as f:
            f.write(response['KeyMaterial'])

    except ClientError as e:
        print('\nERRO:', e)

def create_instance(client, resource, id_image, name, id_security_group, user_data, key_name):
    print("Creating Instances...")
    try:
        waiter = client.get_waiter('instance_status_ok')
        instance = resource.create_instances(
            ImageId= id_image,
            MinCount=1,
            MaxCount=1,
            InstanceType='t2.micro',
            TagSpecifications=[{
                'ResourceType': 'instance', 
                'Tags': [{'Key':'Name','Value':name}, {'Key':'projeto','Value':'orm-duarte'}]}],
            SecurityGroupIds=[id_security_group],
            UserData=user_data,
            KeyName=key_name,
        )
        # instance[0].wait_until_running()
        waiter.wait(InstanceIds=[instance[0].id])
        # response = client.describe_instance_status(InstanceIds=[instance[0].id])
        # while (response['InstanceStatuses'][0]['InstanceStatus']['Status'] != 'ok'):     
        #     time.sleep(30)     
        #     response = client.describe_instance_status(InstanceIds=[instance[0].id])
        ipv4 = client.describe_instances(InstanceIds=[instance[0].id])['Reservations'][0]['Instances'][0]['NetworkInterfaces'][0]['PrivateIpAddresses'][0]['Association']['PublicIp']
        # ip = instance[0].private_ip_address
        # ipv4 = instance[0].public_ip_address
        return instance[0].id, ipv4
    except ClientError as e:
        print("\nERRO:",e)

def create_security_group(client, GroupName="security-group-duarte", FromPort=80,ToPort=80, Description="None"):
    print("Creating security group...")
    response = client.describe_vpcs()
    vpc_id = response.get('Vpcs', [{}])[0].get('VpcId', '')

    try:
        security_group_id = client.create_security_group(
            GroupName=GroupName,
            TagSpecifications=[{
                'ResourceType': 'security-group', 
                'Tags': [{'Key':'Name','Value':GroupName}, {'Key':'projeto','Value':'orm-duarte'}]}],
            Description=Description,
            VpcId=vpc_id
            )['GroupId']
        client.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[
            {
                'IpProtocol': 'tcp',
                'FromPort': 22,
                'ToPort': 22,
                'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
            },
            {
                'IpProtocol': 'tcp',
                'FromPort': 8080,
                'ToPort': 8080,
                'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
            },
            {
                'IpProtocol': 'tcp',
                'FromPort': FromPort,
                'ToPort': ToPort,
                'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
            }])
        return security_group_id
    except ClientError as e:
        print("\nERRO:",e)

def create_image(client, instace):
    print("Creating Image...")
    try:
        image_waiter = client.get_waiter('image_available')
        
        image = client.create_image(
            InstanceId=instace,
            Name='orm-duarte',
        )
        image_waiter.wait(ImageIds=[image['ImageId']])
        return image['ImageId']
    except ClientError as e:
        print("\nERRO:",e)

def create_load_balancer(client, elb, resource, SecurityGroups):
    print("Creating Load Balancer...")
    try:
        subnets = resource.subnets.all()
        subnets_id = [s.id for s in subnets]
        load_balancer = elb.create_load_balancer(
            LoadBalancerName='orm-duarte',
            Listeners=[
                    {
                        'Protocol': 'HTTP',
                        'LoadBalancerPort': 8080,
                        'InstancePort': 8080,
                    },
            ],
            Subnets=subnets_id,
            SecurityGroups=[SecurityGroups],
            Tags=[
                {
                    'Key': 'Name',
                    'Value': 'Load Balancer'
                },
                {
                    'Key': 'projeto',
                    'Value': 'orm-duarte'
                },
            ])
        time.sleep(60)

    except ClientError as e:
        print('\nERRO:', e)

def create_launch_configuration(client, ImageId, KeyName, SecurityGroups):
    print("Creating Launch Configuration...")
    try:
        launch_configuration = client.create_launch_configuration(
            LaunchConfigurationName='orm-duarte',
            ImageId=ImageId,
            KeyName=KeyName,
            SecurityGroups=[SecurityGroups],
            InstanceType='t2.micro',
            InstanceMonitoring={'Enabled': True},
        )
        time.sleep(60)
    except ClientError as e:
        print('\nERRO:', e)
     
def create_autoscaling(client, auto_client):
    print("Creating AutoScaling...")
    try:
        AvailabilityZones = [zone['ZoneName'] for zone in client.describe_availability_zones()['AvailabilityZones']]
        response = auto_client.create_auto_scaling_group(
            AutoScalingGroupName='orm-duarte',
            LaunchConfigurationName='orm-duarte',
            LoadBalancerNames=['orm-duarte'],
            AvailabilityZones=AvailabilityZones,
            DesiredCapacity=2,
            MinSize=2,
            MaxSize=5,
        )
        print("autoscaling created")

    except ClientError as e:
        print('Error', e)


