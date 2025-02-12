#AUTHOR : Serdar AYSAN
#This script help to have VMuuid for Nutanix VM

"""
#REAL NUTANIX COMMAND EXEMPLE
curl -X 'POST' \\
'[<https://XX.XXX.XXX.X:9440/api/nutanix/v3/vms/list>](<https://XX.XXX.XXX.X:9440/api/nutanix/v3/vms/list>)' \\
-H 'accept: application/json' \\
-H 'Content-Type: application/json' \\
-H 'X-Nutanix-Client-Type: ui' \\
-d '
{
"kind": "vm",
"sort_attribute": "string",
"filter": "vm_name==YUCELSAN-RHA",
"length": 5,
"sort_order": "ASCENDING",
"offset": 0
}'
"""
#**********************************************************************************************************************************************
#FUNCTIONS

#TRANSFORMED PYTHON REQUEST
#VARS
#ip_prisma = 'XX.XXX.XXX.XXX'
#ip_prismb = 'XX.XXX.XXX.X'

def getnutanixvmuuid():
    import requests
    import json
    
    #url_prism_a='https://XX.XXX.XXX.XXX:9440/api/nutanix/v3/vms/list'
    #url_prism_b='https://XX.XXX.XXX.X:9440/api/nutanix/v3/vms/list'
    url_prism_a='http://localhost:8030/nutanixapiresponse1.json'
    url_prism_b='http://localhost:8030/nutanixapiresponse1.json'

    name_server = input("SERVER NAME : ")
    vm_name='vm_name==' + name_server
    if name_server == "":
        print("No server name entered ! Bye !")
        exit(10)
    else:
        print("Searching UUID for nutanix VM : [", name_server, "] please wait...")
    

    headers = {
        'accept: application/json',
        'Content-Type: application/json'
        'X-Nutanix-Client-Type: ui'
    }

    data = {
        'kind': 'vm',
        'sort_attribute': 'string',
        #'filter': 'vm_name==YUCELSAN-RHA',
        'filter': vm_name,
        'length': 5,
        'sort_order': "ASCENDING",
        'offset': 0
    }

    response_a = requests.post(url_prism_a, headers=headers, data=data)
    response_b = requests.post(url_prism_b, headers=headers, data=data)


    data_json_a = json.loads(response_a.read())
    data_json_b = json.loads(response_b.read())

    vmuuid_a = data_json['entities'][0]['metadata']['uuid']
    vmuuid_b = data_json['entities'][0]['metadata']['uuid']

    #print(data_json)
    print("le uid de la vm recherchee est :", vmuuid_a)
    print("le uid de la vm recherchee est :", vmuuid_b)
    return(vmuuid_a, vmuuid_b)


def simplegetuid():
    import json
    from urllib.request import urlopen

    #****************************************************************
    #VARIABLES
    prisma = 'XX.XXX.XXX.XXX'
    prismb = 'XX.XXX.XXX.X'
    #url a remplacer par la vraie url pour contacter le server nutanix A ou B
    url = 'http://localhost:8030/nutanixapiresponse1.json'

    response = urlopen(url)
    #lecture de l'url
    data_json = json.loads(response.read())
    #chemin de la data dans le json nutanix
    vmuuid = data_json['entities'][0]['metadata']['uuid']

    #FORCE UID A ETRE A VIDE 
    #vmuuid = "AAAAAAAAAAAAAAAAAAAAAAAAABBBBBBBBBBBBBBBBBBBBBBBBBBBBZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ"

    if vmuuid == "":
        status = False
        print("Sorry ! No VM UUID found !")
        return status
    else:
        status = True
        #print(data_json)
        #print("VM UUID found :", vmuuid)
        return status , vmuuid

#***************************************************************************************************************************************************************************************************************
#MAIN

def main():
    #getnutanixvmuuid()
    #simplegetuid()
    print(simplegetuid())


#***************************************************************************************************************************************************************************************************************
#START

if __name__ == "__main__":
    main()
