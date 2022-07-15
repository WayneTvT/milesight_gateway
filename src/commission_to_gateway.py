import ssl
import urllib.request
import json
class milesight_api:
    def __init__(self,host='127.0.0.1',port='8080',config_path=None):
        self.config = None
        if config_path:
            self.config_path = config_path
            self.load_config()                  
        self.host = host
        self.port = port
        self.token = ''
        self.connections = []
        self.applications = []
        self.profiles = []
        self.devices = []
        ssl._create_default_https_context = ssl._create_unverified_context
        
    def load_config(self):
        with open(self.config_path,'r') as f:
            config = json.loads(f.read())
            self.config = config
   
    def login(self, username='apiuser',password='password'):
        payload = {'username':username,'password':password}
        payload = json.dumps(payload).encode()
        req = urllib.request.Request(f'https://{self.host}:{self.port}/api/internal/login', method="POST")
        r = urllib.request.urlopen(req,data=payload)
        response = r.read()
        self.token = json.loads(response.decode())['jwt'] 
        return self.token
        
    def get_token(self):
        if len(self.token):
            token = self.token
        else:
            token = self.login()
        return token
    
    def get_connection(self):
        self.connections = []
        application= self.get_applications()
        application_mqtt = self.get_applications_mqtt()
        profile = self.get_profiles()
        device = self.get_devices()
        for devices_ix,device in enumerate(self.devices):
            for applications_ix,application in enumerate(self.applications):
                if device['applicationID'] == application['id']:
                    device['application_detail'] = application
            for profiles_ix,profile in enumerate(self.profiles):
                if device['profileID'] == profile['profile']['profileID']:
                    device['profile_detail'] = profile
            self.connections.append(device)    
        
    def get_applications(self):
        token = self.get_token()
        req = urllib.request.Request(f'https://{self.host}:{self.port}/api/urapplications?limit=9999&offset=0&organizationID=1', 
                                     method="GET")
        req.add_header("Authorization", "Bearer "+token)
        r = urllib.request.urlopen(req)
        response = r.read()
        response = json.loads(response.decode())
        self.applications = response['result']    
        return response
    
    def get_applications_mqtt(self):
        token = self.get_token()
        applications = self.get_applications()
        if len(self.applications):
            for app in self.applications:
                req = urllib.request.Request(f"https://{self.host}:{self.port}/api/urapplications/{app['id']}/integrations/mqtt", 
                                             method="GET")   
                req.add_header("Authorization", "Bearer "+token)
                try:
                    r = urllib.request.urlopen(req)
                    response = r.read()
                    if r.status == 200:
                        app['mqtt'] = json.loads(response.decode())
                except urllib.error.HTTPError as e:                        
                    app['mqtt'] ={}        
            
    def set_application(self,description,name):
        token = self.get_token()
        applications = self.get_applications()
        match_application = [x for x in applications['result'] if x['name'] == name]
        if len(match_application):
            pass
        else:
            payload = {
                      'description':description,
                      'name':name,
                      "organizationID":"1",
                      'serviceProfileID': 'f6f7d81d-647f-4c7f-8409-3e5218c0c523',
                      "payloadCodec":"",
                      "payloadEncoderScript":"",
                      "payloadDecoderScript":"",
                      "using":False,
                      "kinds":['URMQTT']
                     }

            payload = json.dumps(payload).encode()
            req = urllib.request.Request(f'https://{self.host}:{self.port}/api/urapplications', method="POST")
            req.add_header("Authorization", "Bearer "+token)
            r = urllib.request.urlopen(req,data=payload)
            applications = self.get_applications()
            
        return applications['result']
    
    def set_application_transport(self,client_id,host,port,app_id,use_auth,username,password,uplink_topic):
        token = self.get_token()
        applications = self.get_applications()
        match_application = [x for x in range(len(self.applications)) if self.applications[x]['id']==str(app_id)]
        if len(match_application):
            payload= {"TLSMode":0,
                        "clientID":str(client_id),
                        "connectTimeout":30,
                        "host":host,
                        "id":app_id,
                        "keepAliveInterval":60,
                        "port":1883,
                        "useAuth":True,
                        "useTLS":False,
                        "username":username,
                        "password":password,
                        "ackQoS":0,
                        "ackTopic":"",
                        "errorQoS":0,
                        "errorTopic":"",
                        "joinQoS":0,
                        "joinTopic":"",
                        "upQoS":0,
                        "uplinkTopic":uplink_topic,
                        "downlinkTopic":"",
                        "downlinkQoS":0,
                        "mcDownlinkTopic":"",
                        "mcDownlinkQoS":0}
            payload = json.dumps(payload).encode()
            req = urllib.request.Request(f"https://{self.host}:{self.port}/api/urapplications/{app_id}/integrations/mqtt",
                                         method="POST")
            req.add_header("Authorization", "Bearer "+token)
            try:
                r = urllib.request.urlopen(req,data=payload)            
                response = r.read()
                if r.status == 200:
                    self.applications[match_application[0]]['mqtt'] = json.loads(response.decode())
            except urllib.error.HTTPError as e:    
                self.applications[match_application[0]]['mqtt'] ={} 
                
    def get_profiles(self):
        token = self.get_token()
        req = urllib.request.Request(f"https://{self.host}:{self.port}/api/urprofiles?limit=9999&offset=0&organizationID=1",
                                     method="GET")
        req.add_header("Authorization", "Bearer "+token)
        r = urllib.request.urlopen(req)            
        response = r.read()     
        response = json.loads(response.decode())
        self.profiles = response['result']
        return response    
    
    def set_profile(self,name,class_a=True,class_b=True,class_c=True,join_type='OTAA'):
        token = self.get_token()
        profiles = self.get_profiles()
        match_profile = [x for x in profiles['result'] if x['name'] == name]
        if len(match_profile):
            pass
        else:
            payload=   {"name":name,
                             "organizationID":"1",
                             "profile":{"factoryPresetFreqs":[],
                                        "macVersion":"1.0.2",
                                        "maxEIRP":0,
                                        "regParamsRevision":"B",
                                        "rxDROffset1":0,
                                        "rxDataRate2":2,
                                        "rxFreq2":923200000,
                                        "supports32bitFCnt":class_a,
                                        "supportsClassB":class_b,
                                        "supportsClassC":class_c,
                                        "supportsJoin":(lambda x:True if x.upper()=='OTAA' else False)(join_type),
                                        "pingSlotPeriod":0,
                                        "pingSlotDR":3,
                                        "pingSlotFreq":923400000,
                                        "classBTimeout":10,
                                        "classCTimeout":0}}
            payload = json.dumps(payload).encode()
            req = urllib.request.Request(f'https://{self.host}:{self.port}/api/urprofiles',
                                         method="POST")
            req.add_header("Authorization", "Bearer "+token)
            r = urllib.request.urlopen(req,data=payload)         
    
        profiles = self.get_profiles()
        return profiles['result']
    
    def get_devices(self):
        token = self.get_token()
        req = urllib.request.Request(f"https://{self.host}:{self.port}/api/urdevices?limit=9999&offset=0&organizationID=1",method="GET")
        req.add_header("Authorization", "Bearer "+token)
        r = urllib.request.urlopen(req)            
        response = r.read()          
        response = json.loads(response.decode())
        self.devices = response['deviceResult']
        return response           
    
    def set_device(self,join_type,name,description,dev_eui,profile_id,application_id,app_key='5572404C696E6B4C6F52613230313823',skipFCntCheck=True):
        token = self.get_token()
        devices = self.get_devices()
        match_device = [x for x in devices['deviceResult'] if x['name'] == name]
        if len(match_device):
            print(f"device:{dev_eui} existed")
            pass
        else:        
            if join_type == 'OTAA':
                payload = {  "name":name,
                             "description":description,
                             "devEUI":dev_eui,
                             "profileID":profile_id,
                             "applicationID":application_id,
                             "appKey":app_key,
                             "skipFCntCheck":skipFCntCheck
                          }
            elif join_type == 'ABP':
                payload = {  "name":name,
                             "description":description,
                             "devEUI":dev_eui,
                             "profileID":profile_id,
                             "applicationID":application_id,
                             "skipFCntCheck":skipFCntCheck,
                             "devAddr":'b2669103',
                             "nwkSKey":app_key,
                             "appSKey":app_key
                          }
            payload = json.dumps(payload).encode()
            req = urllib.request.Request(f"https://{self.host}:{self.port}/api/urdevices",
                                         method="POST")            
            req.add_header("Authorization", "Bearer "+token)
            r = urllib.request.urlopen(req,data=payload)   
            
        devices = self.get_devices()
        return devices['deviceResult']
        
    def start_commissioning(self):
        if self.config:
            username = self.config['application']['mqtt']['username']
            password = self.config['application']['mqtt']['password']
            applications_list = [{'name':x['mqtt']['addition']['application_name'],
                                  'mqtt_topic':x['mqtt']['topic'],
                                  'id':''
                                 } for x in self.config['devices']]
            if len(set([x['name']+x['mqtt_topic'] for x in applications_list])) != len(applications_list):
                print('Error of application and mqtt topic')

            profiles_list = [x['mqtt']['addition']['profile'] for x in self.config['devices']]
            profiles_list = [dict(tupleized) for tupleized in set(tuple(item.items()) for item in profiles_list)]
            for profile in profiles_list:
                profile['id'] = ''

            device_list = self.config['devices']

            for application in applications_list:
                application_description = application_name = application['name']
                response = self.set_application(application_description,application_name)

            for api_application in self.applications:
                for application in applications_list:
                    if api_application['name'] == application['name']:
                        application['id'] = api_application['id']
                        response = self.set_application_transport(1,self.host,self.port,application['id'],
                                                                 True,username,password,uplink_topic=application['mqtt_topic'])

            for profile in profiles_list:
                name = profile['name']
                class_a = profile['supports32bitFCnt']
                class_b = profile['supportsClassB']
                class_c = profile['supportsClassC']
                join_type = (lambda x:'OTAA' if x else 'ABP')(profile['supportsJoin'])
                response = self.set_profile(name,class_a,class_b,class_c,join_type)

            for api_profile in self.profiles:
                for profile in profiles_list:
                    if api_profile['name'] == profile['name']:
                        profile['id'] = api_profile['profile']['profileID']

            for device in device_list:
                for application in applications_list:
                    if device['mqtt']['addition']['application_name'] == application['name']:
                        application_id = application['id']
                        break
                for profile in profiles_list:
                    if device['mqtt']['addition']['profile']['name'] == profile['name']:
                        profile_id = profile['id']
                        profile_join_type = (lambda x:'OTAA' if x else 'ABP')(profile['supportsJoin'])
                        break
                if application_id and profile_id:
                    response = self.set_device(   join_type = profile_join_type,
                                                  name = device['name'],
                                                  description = device['name'],
                                                  dev_eui = device['mqtt']['addition']['device_eui'],
                                                  profile_id=profile_id,
                                                  application_id=application_id,
                                                  app_key='5572404C696E6B4C6F52613230313823',
                                                  skipFCntCheck=True)        