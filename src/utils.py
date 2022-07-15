from bacpypes.task import RecurringTask
from bacpypes.local.device import LocalDeviceObject
from bacpypes.object import get_object_class
import json
import os
def read_json(path):
    with open(path,'r')  as f:
        data = json.load(f)
    return data

def read_txt(path):
    with open(path,'r') as f:
        data = f.read()  
    return data

def get_license_key(commissioning_config,path):
    if 'license_key' in commissioning_config.keys():
        key = commissioning_config['license_key']
    else:
        if 'license_key.txt' in os.listdir(os.path.dirname(path)):
            key = utils.read_txt(path)
        else:
            key = None
    return key

def load_log_config(path):
    config = read_json(path)
    log_path = os.path.join(os.path.dirname(os.path.dirname(path)),'log')
    if "handlers" in config.keys():
        for key in config['handlers']:
            if 'filename' in config['handlers'][key].keys():
                config['handlers'][key]['filename'] = config['handlers'][key]['filename'].replace('$PATH',log_path)
    return config

def get_summary(commissioning_config):
    commissioning_config_summary = commissioning_config.copy()
    summary = []
    mqtt_keys = ['value']
    bacnet_keys = ['objectId','description','presentValue']
    for device in commissioning_config_summary['devices']:
        for object_point in device['object_points']:
            object_point_summary = object_point.copy()
            if 'value' in object_point_summary['mqtt']:
                object_point_summary['mqtt'] = {key:value for key,value in object_point_summary['mqtt'].items() if key in mqtt_keys}
            else:
                object_point_summary['mqtt'] = {'value':None}

            if 'bacpypes_object' in object_point_summary['bacnet']:
                try:
                    object_point_summary['bacnet']['presentValue']['value'] = object_point_summary['bacnet']['bacpypes_object'].presentValue.value
                except Exception:
                    object_point_summary['bacnet']['presentValue']['value'] = None
            else:
                object_point_summary['bacnet']['presentValue']['value'] = None
            object_point_summary['bacnet'] = {key:value for key,value in object_point_summary['bacnet'].items() if key in bacnet_keys}
            summary.append(object_point_summary)
    return summary

class task_func(RecurringTask):
    def __init__(self, app, interval,task, *args, **kwargs):
        RecurringTask.__init__(self, interval * 1000)
        self.interval = interval
        self.app = app
        self.task = task
        self.param1 = args
        self.param2 = kwargs
        
    def process_task(self):
        self.task(*self.param1,**self.param2)
            
class config_convertor:
    def __init__(self,config,name=None,description=None):
        self.config = config
        if name:
            self.name = name
        else:
            if 'name' in self.config['application']['bacnet']:
                self.name = self.config['application']['bacnet']['name']
            else:
                self.name = 'application_name'
            
        if description:
            self.description = description
        else:
            if 'description' in self.config['application']['bacnet']:
                self.description = self.config['application']['bacnet']['description']
            else:
                self.description = 'application_description'
            
    def devices(self):
        bacnet_primary_any = any([x['bacnet']['primary'] for x in self.config['devices']])
        if bacnet_primary_any:
            pass
        else:
            self.config['devices'][0]['bacnet']['primary'] = True      	
        for device in self.config['devices']:
            if device['bacnet']['primary'] == True:
                if 'objectId' in device['bacnet']['node']: 
                    device['bacnet']['node']['objectId']['value'] = int(device['bacnet']['node']['objectId']['value'])
                if 'objectType' in device['bacnet']['node']:
                    if device['bacnet']['node']['objectType']['value'] == 'device':
                         device_class = LocalDeviceObject(objectIdentifier=('device',device['bacnet']['node']['objectId']['value']),vendorIdentifier=device['bacnet']['node']['vendorIdentifier']['value']) 
                            
                for prop_key,prop_content in device['bacnet']['node'].items():
                    if prop_key in ['objectType','objectId', 'vendorIdentifier','alignIntervals','autoSlaveDiscovery','intervalOffset','slaveProxyEnable','interfaceValue']:
                        pass
                    else:
                        if prop_key == 'objectName':
                            prop_value = self.name
                        
                        elif prop_key == 'description':
                            prop_value = self.description
                        else:
                            prop_value = prop_content['value']
                        
                        if 'writable' in prop_content:
                            prop_writable = prop_content['writable']
                        else:
                            prop_writable = True
                        
                        if isinstance(prop_value,list) and len(prop_value) > 0:
                            if all([type(x)==dict for x in prop_value]):
                                prop_value = None
                                
                        if prop_value == None:
                            prop_value = device_class.get_datatype(prop)    
                        
                        try:
                            setattr(device_class,prop_key,prop_value)
                            device_class._properties.get(prop_key).mutable = prop_writable  
                        except Exception:
                            pass      
                device['bacnet']['bacpypes_object'] = device_class        
        
        
    def object_points(self,device):
        for object_point in device['object_points']:
            object_point['bacnet']['objectId']['value'] = int(object_point['bacnet']['objectId']['value'])
            
            if 'objectType' in object_point['bacnet'] and 'objectId' in object_point['bacnet']:
                object_class = get_object_class(object_point['bacnet']['objectType']['value'])
                object_class = object_class()
                setattr(object_class,'objectIdentifier',(object_class.objectType,object_point['bacnet']['objectId']['value']))
            for prop_key,prop_content in object_point['bacnet'].items():
                if prop_key in ['objectType','objectId','bacpypes_object']:
                    pass
                else:
                    prop_value = prop_content['value']
                    if 'writable' in prop_content:
                        prop_writable = prop_content['writable']
                    else:
                        prop_writable = False
                        
                    if isinstance(prop_value,list) and len(prop_value) > 0:
                        if all([type(x)==dict for x in prop_value]):
                            prop_subtype = object_class.get_datatype(prop_key).subtype
                            prop_subtype = prop_subtype()
                            for subtype_prop in prop_value:
                                for subtype_prop_key,subtype_prop_content in subtype_prop.items():
                                    subtype_prop_value = subtype_prop_content['value']
                                    if isinstance(subtype_prop_value,list) and len(subtype_prop_value) > 0:
                                        if all([type(x)==dict for x in subtype_prop_value]):
                                            pass
                                    else:
                                        setattr(prop_subtype,subtype_prop_key,subtype_prop_value)
                            prop_subtype_list = [prop_subtype]
                            prop_value = prop_subtype_list
                            
                    if prop_value == None:
                        prop_value = object_class.get_datatype(prop_key)
                        prop_value = prop_value()
                    
                    try:
                        if isinstance(prop_value,str):      
                            setattr(object_class,prop_key,prop_value)
                            object_class._properties.get(prop_key).mutable = prop_writable 
                        # else:
                        #     setattr(object_class,prop_key,prop_value)
                        #     object_class._properties.get(prop_key).mutable = prop_writable 
                    except Exception:
                        pass 
            object_point['bacnet']['bacpypes_object'] = object_class  
            object_point['bacnet']['bacpypes_object'].presentValue = None
    def process(self):
        self.devices()
        for device in self.config['devices']:
            self.object_points(device)      