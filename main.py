import boto3
from botocore.exceptions import ClientError
from create_functions import *
from delete_functions import *

nv_region = 'us-east-1'
oh_region = 'us-east-2'

nv_key_pair_name = "nv_duarkey"
oh_key_pair_name = "oh_duarkey"

nv_key_pair = "/home/duarte/.ssh/" + nv_key_pair_name
oh_key_pair = "/home/duarte/.ssh/" + oh_key_pair_name

# nv_img_ubuntu_server_1804LTS = 'ami-0ac73f33a1888c64a' # OREGON
nv_img_ubuntu_server_1804LTS = 'ami-00ddb0e5626798373' # NV
oh_img_ubuntu_server_1804LTS = 'ami-0dd9f0e7df0f0a138' #OH

postgres_group_name = "security-group-postgres"
postgres_instance_name = "postgres"
postgres_user_data = '''#!/bin/bash
sudo apt update
sudo apt install postgresql postgresql-contrib -y
sudo -u postgres sh -c "psql -c \\"CREATE USER cloud WITH PASSWORD 'cloud';\\" && createdb -O cloud tasks"
sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/g" /etc/postgresql/10/main/postgresql.conf      
sudo sed -i "a\host all all 0.0.0.0/0 md5" /etc/postgresql/10/main/pg_hba.conf
sudo systemctl restart postgresql
'''

oh_client, oh_resource, oh_elb2, oh_elb, oh_auto = connect(oh_region)
nv_client, nv_resource, nv_elb2, nv_elb, nv_auto = connect(nv_region)

delete_auto_scaling(nv_auto)
delete_launch_config(nv_auto)
delete_load_balancer(nv_elb)
delete_image(nv_client)

terminate_all_instances(oh_resource, oh_client)
delete_key(oh_client, oh_key_pair_name)
create_key(oh_client, oh_key_pair_name, oh_key_pair)
delete_security_group(oh_client,SECURITY_GROUP_NAME=postgres_group_name)
oh_security_group = create_security_group(oh_client, GroupName=postgres_group_name,FromPort=5432, ToPort=5432)
postgres_instance_id, postgres_ip = create_instance(oh_client,oh_resource, oh_img_ubuntu_server_1804LTS, postgres_instance_name, oh_security_group, postgres_user_data, oh_key_pair_name)

orm_group_name = "security-group-orm"
orm_instance_name = 'ORM'
orm_user_data = '''#!/bin/bash
    sudo apt update
    cd /home/ubuntu
    git clone http://github.com/gDuarteg/tasks.git
    sudo sed -i 's/node1/{}/' /home/ubuntu/tasks/portfolio/settings.py  
    cd tasks
    ./install.sh
    sudo reboot
    '''.format(postgres_ip)

terminate_all_instances(nv_resource, nv_client)

delete_key(nv_client, nv_key_pair_name)
create_key(nv_client, nv_key_pair_name, nv_key_pair)
delete_security_group(nv_client, SECURITY_GROUP_NAME=orm_group_name)
nv_security_group = create_security_group(nv_client, GroupName=orm_group_name, FromPort=80, ToPort=80)
nv_instance_id, nv_instance_ip = create_instance(nv_client, nv_resource, nv_img_ubuntu_server_1804LTS, orm_instance_name, nv_security_group, orm_user_data, nv_key_pair_name)

orm_ami_id = create_image(nv_client, nv_instance_id)
terminate_all_instances(nv_resource, nv_client)

create_load_balancer(nv_client, nv_elb, nv_resource, nv_security_group)
create_launch_configuration(nv_auto, orm_ami_id, nv_key_pair_name, nv_security_group)
create_autoscaling(nv_client, nv_auto)

print("\nTudo certo :)")
