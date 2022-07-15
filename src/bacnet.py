from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser
from bacpypes.core import run, deferred, enable_sleeping
from bacpypes.app import BIPSimpleApplication
from bacpypes.errors import ExecutionError
from bacpypes.object import ReadableProperty,WritableProperty,PropertyError,ExecutionError,\
                             AnalogValueObject, AnalogInputObject,AnalogOutputObject, BinaryValueObject,\
                             BinaryInputObject,BinaryOutputObject,PropertyError,NotificationClassObject,\
                             EventEnrollmentObject,get_object_class
from bacpypes.local.device import LocalDeviceObject
from bacpypes.service import cov
from bacpypes.service.object import ReadWritePropertyServices,ReadWritePropertyMultipleServices
from bacpypes.service.device import WhoIsIAmServices,WhoHasIHaveServices,DeviceCommunicationControlServices
from bacpypes.pdu import Address
from bacpypes.basetypes import ServicesSupported,ObjectTypesSupported,\
                                 Destination, Recipient,DeviceAddress,\
                                 DeviceObjectPropertyReference,TimeStamp,EventParameterChangeOfValue,EventParameter,\
                                 EventParameterChangeOfValueCOVCriteria,EventParameterChangeOfState,PropertyStates,\
                                 EventTransitionBits,AddressBinding,BinaryPV,EventState,StatusFlags,EventTransitionBits,\
                                 Reliability,NotifyType,TimeStamp,DateTime,NotificationParametersChangeOfState 
from bacpypes.iocb import IOCB
from bacpypes.apdu import SimpleAckPDU, ReadPropertyRequest, ReadPropertyACK, WritePropertyRequest,\
                                    EventNotificationParameters,ConfirmedEventNotificationRequest, \
                                        NotificationParameters,UnconfirmedEventNotificationRequest,\
                                        CreateObjectRequest,CreateObjectACK
from bacpypes.primitivedata import Null, Atomic, Boolean, Unsigned, Integer, \
                                    Real, Double, OctetString, CharacterString, BitString, Date, Time, ObjectIdentifier
from bacpypes.constructeddata import Array, Any, AnyAtomic,ArrayOf,SequenceOf,ListOf,List,Choice

import os
import logging
from threading import Thread
import cov_toggle
import out_of_service_toggle
import event_notification
import utils
from datetime import datetime


class Application(BIPSimpleApplication, ReadWritePropertyMultipleServices,WhoIsIAmServices,WhoHasIHaveServices):
    def __init__(self,licenser,configuration,host=None,port=None,NC_amount=6,event_logger=None,msg_logger=None,debug=True):
        self.licenser = licenser
        self.config = configuration
        self.nc_address = []
        self.NC_amount = NC_amount
        self.event_logger = event_logger
        self.msg_logger = msg_logger
        self.debug = debug
        self.addon_capabilities = [cov.ChangeOfValueServices,DeviceCommunicationControlServices,
                                   cov_toggle.CovToggleServices,event_notification.EventNotificationServices,
                                   out_of_service_toggle.OutOfServiceToggleServices
                                   ]
        self.__device = [x['bacnet']['bacpypes_object'] for x in self.config['devices'] if 'bacpypes_object' in x['bacnet']][0]
        if host and port:
            self.config['application']['bacnet']['host'] = self.host = host
            self.config['application']['bacnet']['port'] = self.port = port
        else:
            self.host = self.config['application']['bacnet']['host']
            self.port = self.config['application']['bacnet']['port']
        super().__init__(self.__device, f"{self.host}:{self.port}")     
        
        if self.debug and self.event_logger: 
            self.event_logger.info(f"Building BACnet Application object name = {self.__device.objectName} ,object id = {self.__device.objectIdentifier}")
        if self.debug and self.event_logger: 
            self.event_logger.info(f"Building BACnet Application host={self.host} , port={self.port}")
        self.__bacnet_core_thread = Thread(target=run, name="BACnet core thread", daemon=True, kwargs={"sigterm": None, "sigusr1": None}) 
        
    def request(self, apdu):
        BIPSimpleApplication.request(self, apdu)
        if self.debug and self.msg_logger:  
            self.msg_logger.info(f"Received request apdu: {apdu}, pduSource: {apdu.pduSource}")
            
    def indication(self, apdu):
        BIPSimpleApplication.indication(self, apdu)
        source = apdu.apci_contents()['source']
        if source not in self.nc_address:
            self.nc_address.append(source)          
        if self.debug and self.msg_logger:  
            self.msg_logger.info(f"Received indication apdu: {apdu}, pduSource: {apdu.pduSource}") 
            
    def response(self, apdu):
        BIPSimpleApplication.response(self, apdu)
         
    def confirmation(self, apdu):
        BIPSimpleApplication.confirmation(self, apdu)   
        
    def do_ReadPropertyRequest(self, apdu):
        objId = apdu.objectIdentifier
        if (objId == ('device', 4194303)) and self.localDevice is not None:
            objId = self.localDevice.objectIdentifier
        obj = self.get_object_id(objId)
        if not obj:
            raise ExecutionError(errorClass='object', errorCode='unknownObject')
        try:
            datatype = obj.get_datatype(apdu.propertyIdentifier)
            value = obj.ReadProperty(apdu.propertyIdentifier, apdu.propertyArrayIndex)
            if self.debug and self.msg_logger: 
                self.msg_logger.info(f"Read --- object = {obj}, property = {apdu.propertyIdentifier}, value = {value}")
            if value is None:
                raise PropertyError(apdu.propertyIdentifier)
                
            if issubclass(datatype, Atomic) or (issubclass(datatype, (Array, List)) and isinstance(value, list)):
                value = datatype(value)
                
            elif issubclass(datatype, Array) and (apdu.propertyArrayIndex is not None):
                if apdu.propertyArrayIndex == 0:
                    value = Unsigned(value)
                    
                elif issubclass(datatype.subtype, Atomic):
                    value = datatype.subtype(value)
                    
                elif not isinstance(value, datatype.subtype):
                    raise TypeError("invalid result datatype, expecting {0} and got {1}".format(datatype.subtype.__name__, type(value).__name__))
            
            
            elif issubclass(datatype, List):
                if apdu.propertyIdentifier in ['recipientList']:
                    value = datatype(value.value)
                else:
                    value = datatype(value)
            
            elif not isinstance(value, datatype):
                raise TypeError("invalid result datatype, expecting {0} and got {1}" .format(datatype.__name__, type(value).__name__))
                
            resp = ReadPropertyACK(context=apdu)
            resp.objectIdentifier = objId
            resp.propertyIdentifier = apdu.propertyIdentifier
            resp.propertyArrayIndex = apdu.propertyArrayIndex
            resp.propertyValue = Any()
            resp.propertyValue.cast_in(value)
            if self.debug and self.msg_logger: 
                self.msg_logger.info(f"Read Return ----- object = {obj}, property = {apdu.propertyIdentifier}, value = {value}, response = {resp}")
            
        except PropertyError:
            raise ExecutionError(errorClass='property', errorCode='unknownProperty')
        self.response(resp)        
        
    def do_WritePropertyRequest(self, apdu):
        obj = self.get_object_id(apdu.objectIdentifier)
        if not obj:
            raise ExecutionError(errorClass='object', errorCode='unknownObject')
            
        if obj.ReadProperty(apdu.propertyIdentifier, apdu.propertyArrayIndex) is None:
            raise PropertyError(apdu.propertyIdentifier)

        if apdu.propertyValue.is_application_class_null():
            datatype = Null
        else:
            datatype = obj.get_datatype(apdu.propertyIdentifier)     
            
        if issubclass(datatype, Array) and (apdu.propertyArrayIndex is not None):
            if apdu.propertyArrayIndex == 0:
                value = apdu.propertyValue.cast_out(Unsigned)
            else:
                value = apdu.propertyValue.cast_out(datatype.subtype)
        else:
            value = apdu.propertyValue.cast_out(datatype)     
        if self.debug and self.msg_logger:    
            self.msg_logger.info(f"Write to {apdu.propertyIdentifier} with value = {value}")
        if apdu.propertyIdentifier in ['description','timeDelay','timeDelayNormal','deadband','limitEnable']:
            value = obj.WriteProperty(apdu.propertyIdentifier, value, apdu.propertyArrayIndex, apdu.priority,direct=True)    
        else:
            value = obj.WriteProperty(apdu.propertyIdentifier, value, apdu.propertyArrayIndex, apdu.priority)    
        resp = SimpleAckPDU(context=apdu)
        self.response(resp)  
        
    def do_CreateObjectRequest(self,apdu):
        object_class = get_object_class(apdu.objectSpecifier.objectType)
        object_class = object_class()
        match_obj = []
        for obj in self.iter_objects():
            if obj.objectType == object_class.objectType:
                match_obj.append(obj.objectIdentifier)
        if len(match_obj) == 0:
            next_objectId = 1
        else:
            next_objectId = max([x[-1] for x in match_obj])+1
        setattr(object_class,'objectIdentifier',(object_class.objectType, next_objectId))

        for ix in range(len(apdu.listOfInitialValues)):
            if apdu.listOfInitialValues[ix].value.is_application_class_null():
                datatype = Null
            else:
                datatype = object_class.get_datatype(apdu.listOfInitialValues[ix].propertyIdentifier)
            setattr(object_class,apdu.listOfInitialValues[ix].propertyIdentifier,apdu.listOfInitialValues[ix].value.cast_out(datatype))

        if object_class.objectType == 'notificationClass':
            setattr(object_class,'notificationClass',object_class.objectIdentifier[-1])
            for prop in object_class.properties:
                if prop.identifier in list(map(str.strip, writable_property_config['NotificationClass']['NC'].strip('][').replace("'", '').split(','))):
                    prop.mutable = True                    
        self.add_object(object_class)
        resp = CreateObjectACK(context=apdu)
        resp.objectIdentifier = object_class.objectIdentifier
        self.response(resp)          
        
    def do_DeleteObjectRequest(self,apdu):
        object_class = self.get_object_id(apdu.objectIdentifier)
        self.delete_object(object_class)
        resp = SimpleAckPDU(context=apdu)
        self.response(resp) 
        
    def add_object_points(self):
        for device in self.config['devices']:
            for object_point in device['object_points']:
                self.add_object(object_point['bacnet']['bacpypes_object'])        
 
    def override_cov(self):
        cov.GenericCriteria.properties_tracked = ( 'presentValue', 'statusFlags', 'eventState')
        cov.GenericCriteria.properties_reported = ( 'presentValue', 'statusFlags', 'eventState')
        cov.COVIncrementCriteria.properties_tracked = ( 'presentValue', 'statusFlags','eventState')
        cov.COVIncrementCriteria.properties_reported = ( 'presentValue', 'statusFlags', 'eventState')
        
    def add_capabilities(self):
        for cap in self.addon_capabilities:
            self.add_capability(cap)        
        
    def notification_class(self,identifier):
        nc_destination = Destination(
                            validDays=[1, 1, 1, 1, 1, 1, 1],
                            fromTime=(0, 0, 0, 0),
                            toTime=(23, 59, 59, 99),
                            recipient=Recipient(device=('device',9998),address=DeviceAddress(networkNumber=1, macAddress=Address("1:192.168.10.50").addrAddr)),
                            processIdentifier=0,
                            issueConfirmedNotifications=True,
                            transitions=[1, 1, 1],
                            )
        nc = NotificationClassObject(
                            objectIdentifier=('notificationClass', identifier),
                            description='Notification Class %s'%(identifier),
                            objectType='notificationClass',
                            objectName='NC_%s'%(identifier),
                            notificationClass=identifier,
                            priority=ArrayOf(Unsigned)([40,40, 40]),
                            ackRequired=[1, 1, 1],
                            recipientList=ListOf(Destination)([nc_destination]),
                            )      
        for prop in nc.properties:
            if prop.identifier in ['priority','ackRequired','recipientList']:
                prop.mutable = True  
        return nc 
    
    def build_notification_class(self):
        for _id in range(1,self.NC_amount+1):
            nc = self.notification_class(_id)
            self.add_object(nc)
    
    def set_object_status(self,object_point,status,value):
        object_type = object_point.objectType
        object_name = object_point.objectName
        if 'binary' in object_type:
            if status == 'presentValue':
                value = (lambda x:'active' if str(x) == '1' else 'inactive')(value)
        elif 'analog' in object_type:
            if status == 'presentValue':
                value = round(float(value),3) 
                
        if self.debug and self.msg_logger: self.msg_logger.info(f"{object_name} set {status} to  {value}")  
        try:                  
            setattr(object_point,status,value)
        except Exception:
            pass
            
    def update_value_task(self,*args, **kwargs):
        default_out_of_service_timeout = 120
        for device in self.config['devices']:
            if 'out_of_service_timeout' in device.keys():
                if device['out_of_service_timeout'] == None:
                    out_of_service_timeout = default_out_of_service_timeout    
                else:
                    out_of_service_timeout = device['out_of_service_timeout']
            else:
                out_of_service_timeout = default_out_of_service_timeout    
                
            
            last_updatetime = (lambda x:x['last_updatetime'] if 'last_updatetime' in x else None)(device)
            
            for object_point in device['object_points']:
                if 'value' in object_point['mqtt'].keys():
                    missing_value = False
                    if object_point['mqtt']['value'] != None:
                        value_empty = False
                    else:
                        value_empty = True                    
                else:
                    missing_value = True
                    value_empty = True

                if last_updatetime:
                    out_of_service = ((datetime.now() - datetime.strptime(last_updatetime,'%Y-%m-%d %H:%M:%S')).seconds >= out_of_service_timeout)
                else:
                    out_of_service = True
                
                if missing_value or value_empty or out_of_service:
                    self.set_object_status(object_point['bacnet']['bacpypes_object'],'outOfService',out_of_service)
                else:
                    self.set_object_status(object_point['bacnet']['bacpypes_object'],'outOfService',out_of_service)
                    self.set_object_status(object_point['bacnet']['bacpypes_object'],'presentValue',object_point['mqtt']['value'])     
                    
    def task_install(self,func,interval,task,task_param):
        task = getattr(self, task)
        func(self,interval,task,*task_param).install_task()        
               
    def start(self):
        if self.licenser.verify:
            if self.debug and self.event_logger: self.event_logger.info("licenser verified")
            self.add_object_points()
            self.override_cov()
            self.add_capabilities()
            self.build_notification_class()
            self.task_install(func=utils.task_func,interval=5,task='update_value_task',task_param = (None,None,None))          
            if self.debug and self.event_logger: 
                self.event_logger.info("Bacnet Application Start")
            self.__bacnet_core_thread.start()
        else:
            if self.debug and self.event_logger: self.event_logger.info("licenser not verified")