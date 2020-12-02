import requests
import boto3
from botocore.exceptions import ClientError
import datetime
import json

region = 'us-east-1'

client = boto3.client('elb', region_name = region)
ip_load_balancer = client.describe_load_balancers(LoadBalancerNames=['orm-duarte'])['LoadBalancerDescriptions'][0]['DNSName']
url = 'http://{}:8080/tasks'.format(ip_load_balancer)

while True:
    try:
        print(''' 
0 - Teste Postgres
1 - Create Task
2 - Get Task
3 - Delete Task
4 - Get All Tasks
5 - Delete All Tasks
6 - Sair
            ''')
        menu = int(input("Selecione: "))

        if menu == 0:
            # test index
            r = requests.get(url)
            print("\nResponse:", r.text)
        
        elif menu == 1:
            # post task
            payload = {
                "title":str(input("Titulo Task: ")),
                "pub_date": datetime.datetime.now().isoformat(),
                "description":str(input("Descricao Task: "))
            }

            r = requests.post(url + "/create", data=json.dumps(payload))
            print("\nResponse:", r.text)
        
        elif menu == 2:
            # get task
            r = requests.get(url + "/task", data=json.dumps({"title":input("Titulo Task: ")}))
            print("\nResponse:", r.text)
        
        elif menu == 3:
            # delete task
            r = requests.delete(url + "/delete", data=json.dumps({"title":input("Titulo Task: ")}))
            print("\nResponse:", r.text)
        
        elif menu == 4:
            # get all tasks
            r = requests.get(url + "/tasks")
            print("\nResponse:", r.text)
            # for i in json.dumps(r.text):
            #     print(i)

        elif menu == 5:
            # delete all tasks
            r = requests.delete(url + "/deleteAll")
            print("\nResponse:", r.text)
        else:
            break
    except:
        print("ERRO desconhecido")
        break
