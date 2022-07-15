import base64 
import json
from datetime import datetime

class data_loader:
    def __init__(self,config,payload):
        self.config = config
        self.payload = payload
        if isinstance(self.payload,str):
            self.payload = json.loads(self.payload)
            
        #application_name = self.payload['applicationName']
        #config_device = [x for x in config['devices'] if x['mqtt']['addition']['application_name'] == application_name]
        payload_dev_eui = self.payload['devEUI'].lower()
        config_device = [x for x in config['devices'] if x['mqtt']['addition']['device_eui'].replace(' ','').lower() == payload_dev_eui]        
        if len(config_device):
            config_device[0]['last_updatetime']= str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            self.config_object_point = config_device[0]['object_points']
    
    def find_path(self,input,path):
        node_content = input
        for node in path:
            if isinstance(node_content,list) and len(node_content)>0:
                node_content = [x[node] for x in node_content]
            else:
                node_content = node_content[node]    
        if isinstance(node_content,list) and len(node_content)==1:
            node_content = node_content[0]
        return node_content
    
    def find_data(self,input,key,from_ix,to_ix,from_format=None,to_format=None,reverse=True):
        input = input.upper()
        if key in input:
            key_ix = input.find(key) + len(key)
            from_ix = int(from_ix) * 2
            to_ix = int(to_ix) * 2
            output = input[key_ix+from_ix:key_ix+to_ix]
            if reverse:
                n = 2
                output = ''.join([output[i:i+n] for i in range(0, len(output), n)][::-1])
            if to_format == 'heximal':
                output = int(output,16)
            elif to_format == 'decimal':
                output = int(output,10)
        else:
            output = None
        return output    
    
    def load_data(self):
        if len(self.config_object_point):
            for object_point in self.config_object_point:
                if 'value' in object_point['mqtt'].keys():
                    previous_value = object_point['mqtt']['value']
                else:
                    previous_value = None                
                path = object_point['mqtt']['path']
                input_format = object_point['mqtt']['input_format']
                decode_format = object_point['mqtt']['decode_format']
                channel_id = object_point['mqtt']['channel_id']
                channel_type = object_point['mqtt']['channel_type']
                _bytes = object_point['mqtt']['bytes']
                calculation = object_point['mqtt']['calculation']
                if len(path) == 0 and len(input_format) == 0 and len(decode_format) == 0 and len(channel_id) == 0 and len(channel_type) == 0 and len(_bytes['from']) == 0 and len(_bytes['to'])== 0 and len(calculation) == 0:
                    value = None
                else:
                    if len(path):
                        data = self.find_path(self.payload,path)
                    if decode_format == 'heximal':
                        if input_format == 'base64':
                            data = base64.b64decode(data).hex()
                            if len(channel_id) and len(channel_type) and len(_bytes['from']) and len(_bytes['to']):
                                key = channel_id + channel_type
                                from_bytes = _bytes['from']
                                to_bytes = _bytes['to']
                                data = self.find_data(data,key,from_bytes,to_bytes,to_format=decode_format,reverse=True)                           

                        elif input_format == 'heximal':
                            if len(channel_id) and len(channel_type) and len(_bytes['from']) and len(_bytes['to']):
                                key = channel_id + channel_type
                                from_bytes = _bytes['from']
                                to_bytes = _bytes['to']
                                data = self.find_data(data,key,from_bytes,to_bytes,to_format=decode_format,reverse=True)                                               

                    elif decode_format == 'decimal':
                        if input_format == 'base64':
                            data = base64.b64decode(data).hex()
                            if len(channel_id) and len(channel_type) and len(_bytes['from']) and len(_bytes['to']):
                                key = channel_id + channel_type
                                from_bytes = _bytes['from']
                                to_bytes = _bytes['to']
                                data = self.find_data(data,key,from_bytes,to_bytes,to_format=decode_format,reverse=False)                      

                        elif input_format == 'heximal':
                            if len(channel_id) and len(channel_type) and len(_bytes['from']) and len(_bytes['to']):
                                key = channel_id + channel_type
                                from_bytes = _bytes['from']
                                to_bytes = _bytes['to']
                                data = self.find_data(data,key,from_bytes,to_bytes,to_format=decode_format,reverse=False)                       

                        # elif input_format == 'decimal':
                        #     data = data

                        elif input_format == 'json':
                            data = json.loads(data)
                            
                    # else:
                    #     data = data

                    if calculation:
                        if data != None:
                            data =eval(str(data) + calculation)
                        
                    if previous_value != None and data == None:
                        data = previous_value
                    
                    value = data
                object_point['mqtt']['value'] = value        
        return self.config