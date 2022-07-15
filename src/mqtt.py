import paho.mqtt.client as mqtt
import threading
import json
import logging
import logging.config
from  SensorDecoder import data_loader

class mqtt_worker(mqtt.Client):
    def __init__(self,licenser,config,event_logger=None,msg_logger=None,debug=True):
        super(mqtt_worker, self).__init__()
        self.event_logger = event_logger
        self.msg_logger = msg_logger
        self.debug = debug

        #if licenser.verify():
        if True:
            if self.debug and self.event_logger: self.event_logger.info("Key Verified")
            self.config = config
            self.MQTT_BROKER_HOST = str(config['application']['mqtt']['host'])
            self.MQTT_BROKER_PORT = int(config['application']['mqtt']['port'])
            self.MQTT_BROKER_USERNAME = str(config['application']['mqtt']['username'])
            self.MQTT_BROKER_PASSWORD = str(config['application']['mqtt']['password'])
            self.MQTT_TOPIC_ARRAY = list(dict.fromkeys([x['mqtt']['topic'] for x in config['devices']]))
            self.MESSAGE_RECORDS = []
            self.MESSAGE_RECORDS_KEEP = 10
            self.flag_connected = 0
        else:
            self.MQTT_BROKER_HOST = None
            self.MQTT_BROKER_PORT = None
            self.MQTT_BROKER_USERNAME = None
            self.MQTT_BROKER_PASSWORD = None
            if self.debug and self.event_logger: self.event_logger.info("Key not Verified")            
        
    def on_subscribe(self, mqttc, obj, mid, granted_qos):
        if self.debug and self.event_logger: 
            self.event_logger.info("Subscribed: mid=%s qos=%s"%(str(mid),str(granted_qos)))
        
    def on_connect(self, mqttc, obj, flags, rc):
        self.flag_connected = 1
        if self.debug and self.event_logger:
            self.event_logger.info(f"MQTT Broker Connected host={self.MQTT_BROKER_HOST},port={self.MQTT_BROKER_PORT}")
        for topic in self.MQTT_TOPIC_ARRAY:
            if self.debug and self.event_logger: self.event_logger.info(f"MQTT Topic Subscribed topic={topic}")
            self.subscribe(topic=topic,qos=0)
        
    def on_disconnect(self, mqttc, obj, rc):
        self.flag_connected = 0
        if self.debug and self.event_logger: self.event_logger.info("MQTT Broker Disconnected")
        
    def on_message(self, mqttc, obj, msg):
        payload = msg.payload.decode('utf-8')
        message_loader = data_loader(self.config,payload)
        self.config = message_loader.load_data()
        self.record_add(payload)
        if self.debug and self.msg_logger: self.msg_logger.info(payload)
        
    def record_add(self,message):
        if isinstance(message,str):
            message = json.loads(message)
        if len(self.MESSAGE_RECORDS) >= self.MESSAGE_RECORDS_KEEP:
            self.MESSAGE_RECORDS.pop(0)
        self.MESSAGE_RECORDS.append(message)

    def run(self):
        if self.MQTT_BROKER_HOST and self.MQTT_BROKER_PORT and self.MQTT_BROKER_USERNAME and self.MQTT_BROKER_PASSWORD:
            self.connect_async(self.MQTT_BROKER_HOST, self.MQTT_BROKER_PORT, 60)
            self.username_pw_set(self.MQTT_BROKER_USERNAME,self.MQTT_BROKER_PASSWORD)
            rc = 0
            while rc == 0:
                if self.debug and self.event_logger: self.event_logger.info("MQTT application Start")
                rc = self.loop_start()       
            return rc
        else:
            if self.debug and self.event_logger: 
                self.event_logger.info("MQTT missing parameter")