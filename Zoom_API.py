import getpass
import json
import os
import requests
import sys
import datetime
import time
import uuid
import urllib.request
import webexteamssdk 

# import supporting functions from additional file
from Firepower import Firepower

# Config Paramters
CONFIG_FILE     = "config.json"
CONFIG_DATA     = None

# Object Prefix
OBJECT_PREFIX = "" 


# A function to load CONFIG_DATA from file
def loadConfig():

    global CONFIG_DATA

    sys.stdout.write("\n")
    sys.stdout.write("Carregando arquivo de configuracao...")
    sys.stdout.write("\n")

    # If we have a stored config file, then use it, otherwise create an empty one
    if os.path.isfile(CONFIG_FILE):

        # Open the CONFIG_FILE and load it
        with open(CONFIG_FILE, 'r') as config_file:
            CONFIG_DATA = json.loads(config_file.read())

        sys.stdout.write("Arquivo de configuracao carregado com sucesso.")
        sys.stdout.write("\n")
        sys.stdout.write("\n")

    else:

        sys.stdout.write("Arquivo de configuracao nao encontrado, carregando com valores padroes...")
        sys.stdout.write("\n")
        sys.stdout.write("\n")

        # Set the CONFIG_DATA defaults
        CONFIG_DATA = {
            "FMC_IP": "",
            "FMC_USER": "",
            "FMC_PASS": "",
            "IP_BYPASS_UUID": "",
            "URL_BYPASS_UUID": "",
            "SERVICE":  False,
            "SSL_VERIFY": False,
            "SSL_CERT": "/path/to/certificate",
            "AUTO_DEPLOY": False,
            "WEBEX_ACCESS_TOKEN": "NjllYzE0MjAtYmFhYS00ZDI0LWI1NDMtMGFiZTY5OTRjMTJhODgyNDE5ZDItZmQ2_PF84_1eb65fdf-9643-417f-9974-ad72cae0e10f",
            "WEBEX_ROOM_ID": "Y2lzY29zcGFyazovL3VzL1JPT00vNjFhY2I5ZjAtZjg4NS0xMWVhLWEyOGUtMTFhZjkxYmU4ZjQ4",
        }

# A function to store CONFIG_DATA to file
def saveConfig():

    sys.stdout.write("Salvando arquivo de configuracao...")
    sys.stdout.write("\n")

    with open(CONFIG_FILE, 'w') as output_file:
        json.dump(CONFIG_DATA, output_file, indent=4)

# A function to deploy pending policy pushes
def DeployPolicies(fmc):

    # Get pending deployments
    pending_deployments = fmc.getPendingDeployments()

    # Setup a dict to hold our deployments
    deployments = {}

    # See if there are pending deployments
    if pending_deployments['paging']['count'] > 0:

        # Iterate through pending deployments
        for item in pending_deployments['items']:

            # Only get ones that can be deployed
            if item['canBeDeployed']:

                # Only get ones that don't cause traffic interruption
                if item['trafficInterruption'] == "NO":

                    # If there are multiple devices, append them
                    if item['version'] in deployments:
                        device_list = deployments[item['version']]
                        device_list.append(item['device']['id'])
                        deployments[item['version']] = device_list
                    else:
                        deployments[item['version']] = [item['device']['id']]

        # Build JSON for each of our deployments
        for version, devices in deployments.items():

            deployment_json = {
                "type": "DeploymentRequest",
                "version": version,
                "forceDeploy": False,
                "ignoreWarning": True,
                "deviceList": devices,
            }

            fmc.postDeployments(deployment_json)

        sys.stdout.write("All pending deployments have been requested.\n")
    
    else:

        sys.stdout.write("There were zero pending deployments.\n")

# Function that can be used to schedule the  to refresh at intervals. Caution: this creates an infinite loop.
# Takes the  function and the interval as parameters. 
def intervalScheduler(function, interval):

    # user feedback
    sys.stdout.write("\n")
    sys.stdout.write(f"Zoom Web Service Parser vai ser atualizado a cada: {interval} segundos. Por favor use ctrl-C para sair.\n")
    sys.stdout.write("\n")

    # interval loop, unless keyboard interrupt
    try:
        while True:
            function()
            # get current time, for user feedback 
            date_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            sys.stdout.write("\n")
            sys.stdout.write(f"{date_time} - Zoom Web Service Parser executado por intervalo, intervalo atual de : {interval} segundos. \nPor favor use ctrl-C para sair.\n")
            sys.stdout.write("\n")
            # sleep for X amount of seconds and then run again. Caution: this creates an infinite loop to check the Web Service Feed for changes
            time.sleep(interval)

    # handle keyboard interrupt
    except (KeyboardInterrupt, SystemExit):
        sys.stdout.write("\n")
        sys.stdout.write("\n")
        sys.stdout.write("Exiting... Zoom Web Service Parser nao vai ser mais atualizado automaticamente.\n")
        sys.stdout.write("\n")
        sys.stdout.flush()
        pass

def check_for_new_version():
    if not os.listdir('json'): 
        sys.stdout.write(f"\nScrip rodando pela primeira vez =D\n")
        os.mkdir("json")
        ParseTXT_Json("https://assets.zoom.us/docs/ipranges/Zoom.txt", "zoom") 
        ParseTXT_Json("https://assets.zoom.us/docs/ipranges/ZoomMeetings.txt", "zoom_meetings")
        ParseTXT_Json("https://assets.zoom.us/docs/ipranges/ZoomCRC.txt", "zoom_crc")
        ParseTXT_Json("https://assets.zoom.us/docs/ipranges/ZoomPhone.txt", "zoom_phone")
        return True
    else:
        sys.stdout.write(f"\nChecando se há atualizações....\n\n")
        ParseTXT_Json("https://assets.zoom.us/docs/ipranges/Zoom.txt", "zoom_check") 
        ParseTXT_Json("https://assets.zoom.us/docs/ipranges/ZoomMeetings.txt", "zoom_meetings_check")
        ParseTXT_Json("https://assets.zoom.us/docs/ipranges/ZoomCRC.txt", "zoom_crc_check")
        ParseTXT_Json("https://assets.zoom.us/docs/ipranges/ZoomPhone.txt", "zoom_phone_check")
        
        #Pegar novos arquivos .json para comparar se teve alguma att
        with open('json/zoom_check.json') as z:
            zoom_check = json.load(z)
        with open('json/zoom_meetings_check.json') as m:
            meetings_check = json.load(m)
        with open('json/zoom_crc_check.json') as c:
            crc_check = json.load(c)
        with open('json/zoom_phone_check.json') as p: 
            phone_check = json.load(p)
            
        # Arquivos antigos que já estao na pasta json
        with open('json/zoom.json') as z:
            zoom_runn = json.load(z)
        with open('json/zoom_meetings.json') as m:
            meetings_runn = json.load(m)
        with open('json/zoom_crc.json') as c:
            crc_rnn = json.load(c)
        with open('json/zoom_phone.json') as p: 
            phone_runn = json.load(p)
        
        
        sizeZoom = len(zoom_runn)
        sizeZoomCheck = len(zoom_check)
        
        sizeMeetings = len(meetings_runn)
        sizeMeetingsCheck = len(meetings_check)
        
        sizeCrc = len(crc_rnn)
        sizeCrcCheck = len(crc_check)
        
        sizePhone = len(phone_runn)
        sizePhoneCheck = len(phone_check)
                
        if sizeZoom == sizeZoomCheck:
            # Se os arquivos forem iguais de tamanho remover todos os checks que foram baixados
            os.remove("json/zoom_check.json")
            os.remove("json/zoom_meetings_check.json")
            os.remove("json/zoom_crc_check.json")
            os.remove("json/zoom_phone_check.json")
            sys.stdout.write("O Web Service List da Zoom não teve nenhum update, não precisa de atualização!!\n\n") 
            return False
        else:
            # Se os arquivos forem de tamanho diferente(há um update), remover o atual rodando e renomear o check
            os.remove("json/zoom.json")
            os.rename(r'json/zoom_check.json',r'json/zoom.json')
            sys.stdout.write("O Web Service List da Zoom encontrou um update, atualizando as versões...\n\n")
            return True
        
        if sizeMeetings == sizeMeetingsCheck:
            # Se os arquivos forem iguais de tamanho remover todos os checks que foram baixados
            os.remove("json/zoom_check.json")
            os.remove("json/zoom_meetings_check.json")
            os.remove("json/zoom_crc_check.json")
            os.remove("json/zoom_phone_check.json")
            sys.stdout.write("O Web Service List da Zoom não teve nenhum update, não precisa de atualização!!\n\n") 
            return False
        else:
            # Se os arquivos forem de tamanho diferente(há um update), remover o atual rodando e renomear o check
            os.remove("json/zoom_meetings.json")
            os.rename(r'json/zoom_meetings_check.json',r'json/zoom_meetings.json')
            sys.stdout.write("O Web Service List da Zoom encontrou um update, atualizando as versões...\n\n")
            return True
            
        if sizeCrc == sizeCrcCheck:
            # Se os arquivos forem iguais de tamanho remover todos os checks que foram baixados
            os.remove("json/zoom_check.json")
            os.remove("json/zoom_meetings_check.json")
            os.remove("json/zoom_crc_check.json")
            os.remove("json/zoom_phone_check.json")
            sys.stdout.write("O Web Service List da Zoom não teve nenhum update, não precisa de atualização!!\n\n") 
            return False
        else:
            # Se os arquivos forem de tamanho diferente(há um update), remover o atual rodando e renomear o check
            os.remove("json/zoom_crc.json")
            os.rename(r'json/zoom_crc_check.json',r'json/zoom_crc.json')
            sys.stdout.write("O Web Service List da Zoom encontrou um update, atualizando as versões...\n\n")
            return True
            
        if sizePhone == phone_check:
            # Se os arquivos forem iguais de tamanho remover todos os checks que foram baixados
            os.remove("json/zoom_check.json")
            os.remove("json/zoom_meetings_check.json")
            os.remove("json/zoom_crc_check.json")
            os.remove("json/zoom_phone_check.json")
            sys.stdout.write("O Web Service List da Zoom não teve nenhum update, não precisa de atualização!!\n\n") 
            return False
        else:
            # Se os arquivos forem de tamanho diferente(há um update), remover o atual rodando e renomear o check
            os.remove("json/zoom_phone.json")
            os.rename(r'json/zoom_phone_check.json',r'json/zoom_phone.json')
            sys.stdout.write("O Web Service List da Zoom encontrou um update, atualizando as versões...\n\n")
            return True

             
#function for parse .txt to a json
def ParseTXT_Json(url, name):
    file = urllib.request.urlopen(url)
      
    # resultant dictionary 
    dict1 = {} 
      
    # fields in the sample file  
    fields =['ip'] 

    # count variable for employee id creation 

    l = 1
    for line in file: 
        # reading line by line from the text file 
        decoded_line = line.decode("utf-8")
        description = list(decoded_line.strip().split(None, 0)) 
        
        # for output see below 
        #print(description) 
        
        # for automatic creation of id for each employee 
        sno ='Range '+str(l)

        # loop variable 
        i = 0
        # intermediate dictionary 
        dict2 = {} 
        while i<len(fields): 
            
                # creating dictionary for each employee 
                dict2[fields[i]]= description[i] 
                i = i + 1
                
        # appending the record of each employee to 
        # the main dictionary 
        dict1[sno]= dict2 
        l = l + 1
      
    # creating json file         
    out_file = open("json/" + name + ".json", "w")
    json.dump(dict1, out_file, indent = 4) 
    out_file.close() 


# function to parse the Web Service, so that it can be called iteratively (e.g by the scheduler function)
def WebServiceParser():

    bool_new_version = check_for_new_version()
    
    if bool_new_version == True:
        # Instantiate a Firepower object
        fmc = Firepower(CONFIG_DATA)

        # If there's no defined Network Object, make one, then store the UUID - else, get the current object
        if CONFIG_DATA['IP_BYPASS_UUID'] is '':
            # Create the JSON to submit
            object_json = {
                'name': OBJECT_PREFIX + "ZOOM_IPs_BYPASS",
                'type': 'NetworkGroup',
                'overridable': True,
            }
            # Create the Network Group object in the FMC
            ip_group_object = fmc.createObject('networkgroups', object_json)

            # Save the UUID of the object
            CONFIG_DATA['IP_BYPASS_UUID'] = ip_group_object['id']
            saveConfig()
        else:
            # Get the Network Group object of the specified UUID
            ip_group_object = fmc.getObject('networkgroups', CONFIG_DATA['IP_BYPASS_UUID'])
            
            
        # If there's no defined URL Object, make one, then store the UUID
        if CONFIG_DATA['URL_BYPASS_UUID'] is '':
            # Create the JSON to submit
            object_json = { 
                'name': OBJECT_PREFIX + "ZOOM_URLs_BYPASS",
                'type': 'UrlGroup',
                'overridable': True,
            }

            # Create the Network Group object in the FMC
            url_group_object = fmc.createObject('urlgroups', object_json)

            # Save the UUID of the object
            CONFIG_DATA['URL_BYPASS_UUID'] = url_group_object['id']
            saveConfig()
        else:
            # Get the Network Group object of the specified UUID
            url_group_object = fmc.getObject('urlgroups', CONFIG_DATA['URL_BYPASS_UUID'])
            
        # initiate lists to be filled with addresses
        IP_List = []
        URL_List = []

        # reading the json local file
        with open('json/zoom.json') as z:
            zoom = json.load(z)
        with open('json/zoom_meetings.json') as m:
            meetings = json.load(m)
        with open('json/zoom_crc.json') as c:
            crc = json.load(c)
        with open('json/zoom_phone.json') as p: 
            phone = json.load(p)

        # iterate through each 'item' in the JSON data
        for zoom_key, zoom_subdict in zoom.items():
           for zoom_subkey, zoom_value in zoom_subdict.items():
                # iterate through all IPs in each item
                IP_List.append(zoom_value)
        for meetings_key, meetings_subdict in meetings.items():
           for meetings_subkey, meetings_value in meetings_subdict.items():
                # iterate through all IPs in each item
                IP_List.append(meetings_value) 
        for crc_key, crc_subdict in crc.items():
           for crc_subkey, crc_value in crc_subdict.items():
                # iterate through all IPs in each item
                IP_List.append(crc_value)
        for phone_key, phone_subdict in phone.items():
           for phone_subkey, phone_value in phone_subdict.items():
                # iterate through all IPs in each item
                IP_List.append(phone_value)
        # Reset the fetched Network Group object to clear the 'literals'
        ip_group_object['literals'] = []
        ip_group_object.pop('links', None)
        # check whether list not empty (microsoft sometimes doesn't return IP's for default IP addresses for example)
        if not IP_List:
            IP_List.append("240.0.0.0/4")
            # user feed back
            sys.stdout.write("\n")
            sys.stdout.write("IP_BYPASS list returned no IP's, empty list with dummy IP range (240.0.0.0/4) created (to avoid policy deploy failure)...\n")

        # Add all the fetched IPs to the 'literals'of the Network Group object
        for ip_address in IP_List:
            ip_group_object['literals'].append({'type': 'Network', 'value': ip_address})

         
        #ip_group_object = list(dict.fromkeys(ip_group_object))
        #print(ip_group_object)
        # Update the NetworkGroup object
        fmc.updateObject('networkgroups', CONFIG_DATA['IP_BYPASS_UUID'], ip_group_object)

        # Reset the fetched URL Group object to clear the 'literals'
        url_group_object['literals'] = []
        url_group_object.pop('links', None)
        URL_List.append("zoom.us")
        URL_List.append("*.zoom.us")
        if not URL_List:
            URL_List.append("example.com")
            # user feed back
            sys.stdout.write("\n")
            sys.stdout.write("URL_BYPASS list returned no URL's, empty list with dummy URL (example.com) created (to avoid policy deploy failure)...\n")
            
        # Add all the fetched URLs to the 'literals' of the URL Group object
        for url in URL_List:
            url_group_object['literals'].append({'type': 'Url', 'url': url})
                

        # Update the UrlGroup object
        fmc.updateObject('urlgroups', CONFIG_DATA['URL_BYPASS_UUID'], url_group_object)


        # user feed back
        sys.stdout.write("\n")
        sys.stdout.write(f"A lista de Web Service do Zoom foi atualizada com sucesso!\n")
        sys.stdout.write("\n")

        saveConfig()

        # If the user wants us to deploy policies, then do it
        if CONFIG_DATA['AUTO_DEPLOY']:
            DeployPolicies(fmc)

        # if Webex Teams tokens set, then send message to Webex room
        if CONFIG_DATA['WEBEX_ACCESS_TOKEN'] == '' or CONFIG_DATA['WEBEX_ROOM_ID'] == '':

            # user feed back
            sys.stdout.write("Webex Teams not set.\n")
            sys.stdout.write("\n")
        else:

            # adjust the Webex message based on the config
            if CONFIG_DATA['AUTO_DEPLOY']:
                message_text = f"Objetos Zoom foram atualizados com sucesso! Deployment inicado..."
            else:
                message_text = f"Objetos Zoom foram atualizados com sucesso! É necessario um deploy na policy do Firepower."

            # instantiate the Webex handler with the access token
            #webex = ciscosparkapi.CiscoSparkAPI(CONFIG_DATA['WEBEX_ACCESS_TOKEN'])
            teams = webexteamssdk.WebexTeamsAPI(CONFIG_DATA['WEBEX_ACCESS_TOKEN'])

            # post a message to the specified Webex room
            message = teams.messages.create(CONFIG_DATA['WEBEX_ROOM_ID'], text=message_text)
    elif bool_new_version == False:
        # no new version, do nothing
        pass
       
        
##############END PARSE FUNCTION##############START EXECUTION SCRIPT##############

if __name__ == "__main__":

    # Load config data from file
    loadConfig()

    # If not hard coded, get the FMC IP, Username, and Password
    if CONFIG_DATA['FMC_IP'] == '':
        CONFIG_DATA['FMC_IP'] = input("FMC IP Address: ")
    if CONFIG_DATA['FMC_USER'] == '':
        CONFIG_DATA['FMC_USER'] = input("\nFMC Username: ")
    if CONFIG_DATA['FMC_PASS'] == '':
        CONFIG_DATA['FMC_PASS'] = getpass.getpass("\nFMC Password: ")
    # Save the FMC data
    saveConfig()

    try:
        if CONFIG_DATA['SERVICE']:
            # Calls the intervalScheduler for automatic refreshing (pass function and interval in seconds (1 hour = 3600 seconds))
            intervalScheduler(WebServiceParser, 3600) #set to 1 hour
        else:
            # Execute  just once
            WebServiceParser()

    except (KeyboardInterrupt, SystemExit):
        sys.stdout.write("\n\nExiting...\n\n")
        sys.stdout.flush()
        pass

# end of script
