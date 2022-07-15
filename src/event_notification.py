from bacpypes.debugging import bacpypes_debugging, DebugContents, ModuleLogger
from bacpypes.capability import Capability
from bacpypes.core import deferred
from bacpypes.task import OneShotTask, RecurringFunctionTask, TaskManager
from bacpypes.iocb import IOCB
from bacpypes.basetypes import Destination, Recipient,DeviceAddress,\
                                 DeviceObjectPropertyReference,TimeStamp,EventParameterChangeOfValue,EventParameter,\
                                 EventParameterChangeOfValueCOVCriteria,EventParameterChangeOfState,PropertyStates,EventTransitionBits,\
                                 AddressBinding,BinaryPV,EventState,StatusFlags,EventTransitionBits,Reliability,NotifyType,\
                                 TimeStamp,DateTime,NotificationParametersChangeOfState,RecipientProcess, \
                                 ObjectPropertyReference,StatusFlags,NotificationParametersOutOfRange
from bacpypes.constructeddata import ListOf, Any
from bacpypes.apdu import ConfirmedEventNotificationRequest,UnconfirmedEventNotificationRequest,\
                            EventNotificationParameters,NotificationParameters,\
                                SimpleAckPDU, Error, RejectPDU, AbortPDU
from bacpypes.errors import ExecutionError
from bacpypes.object import Property
from bacpypes.service.detect import DetectionAlgorithm, monitor_filter
from bacpypes.pdu import Address,RemoteStation,RemoteBroadcast
_debug = 0
_log = ModuleLogger(globals())

class EventNotificationDetection(DetectionAlgorithm):
    properties_tracked = ()
    properties_reported = ()
    monitored_property_reference = None    
    def __init__(self, obj):
        DetectionAlgorithm.__init__(self)
        self.obj = obj
        self._triggered = False
        self.count = 0
        kwargs = {}
        for property_name in self.properties_tracked:
            setattr(self, property_name, None)
            kwargs[property_name] = (obj, property_name)
        self.bind(**kwargs)
        
    @monitor_filter('eventState')
    def event_state_filter(self, old_value, new_value):
        self.old_value = old_value
        self.new_value = new_value
        return True        
        
    def execute(self):
        notification_class_obj = self.find_notification_class()
        self.send_event_notifications(notification_class_obj)
        
    def find_notification_class(self):
        notification_class_obj = None
        for obj in self.obj._app.iter_objects():
            if obj.objectIdentifier[0] == 'notificationClass':
                if obj.notificationClass == self.obj.notificationClass:
                    notification_class_obj = obj
        return notification_class_obj
        
    def send_event_notifications(self, notification_class_obj):
        current_time = TaskManager().get_time()
        object_identifier = self.obj.objectIdentifier
        object_type,object_id = object_identifier
        object_notification_class = self.obj.notificationClass
        object_notify_type = self.obj.notifyType
        
        
        notification_class_priority = notification_class_obj.priority
        notification_class_ackRequired = [(lambda x: True if x ==1 else False)(x) for x in notification_class_obj.ackRequired]
        notification_class_process_identifier = notification_class_obj.recipientList[0].processIdentifier
        if object_type in ['binaryInput','binaryOutput','binaryValue']:
            object_status_flag = self.obj.ReadProperty('statusFlags').value
            self.obj.changeOfStateCount = self.obj.changeOfStateCount + 1
            request = UnconfirmedEventNotificationRequest()
            #request.pduDestination = [x for x in self.obj._app.subscriptions()][0].client_addr
            #request.pduDestination = RemoteBroadcast(net=notification_class_obj.recipientList[0].recipient.address.networkNumber)
            #request.pduDestination = Address('192.168.23.200')
            request.pduDestination = Address(self.obj._app.nc_address[-1])
            request.processIdentifier = notification_class_process_identifier
            request.initiatingDeviceIdentifier = self.obj._app.localDevice.objectIdentifier
            request.eventObjectIdentifier = self.obj.objectIdentifier
            request.notificationClass = object_notification_class
            request.eventType = 'changeOfState'
            request.timeStamp = TimeStamp(sequenceNumber=self.obj.changeOfStateCount)    
            request.notifyType = object_notify_type
            request.priority = notification_class_priority[1]
            request.ackRequired = notification_class_ackRequired[-1]
            request.fromState = self.old_value
            request.toState = self.new_value
            request.eventValues = NotificationParameters(changeOfState=NotificationParametersChangeOfState(
                                                                        newState = PropertyStates(binaryValue=self.obj.presentValue),
                                                                                       statusFlags=object_status_flag))   
            iocb = IOCB(request)
            self.obj._app.request_io(iocb) 
            
        elif object_type in ['analogInput','analogOutput','analogValue']:
            object_status_flag = self.obj.ReadProperty('statusFlags').value
            self.count = self.count + 1 
            request = UnconfirmedEventNotificationRequest()
            #request.pduDestination = [x for x in self.obj._app.subscriptions()][0].client_addr
            #request.pduDestination = RemoteBroadcast(net=notification_class_obj.recipientList[0].recipient.address.networkNumber)
            #request.pduDestination = Address('192.168.23.200')
            request.pduDestination = Address(self.obj._app.nc_address[-1])
            request.processIdentifier = notification_class_process_identifier
            request.initiatingDeviceIdentifier = self.obj._app.localDevice.objectIdentifier
            request.eventObjectIdentifier = self.obj.objectIdentifier
            request.notificationClass = object_notification_class
            request.eventType = 'outOfRange'
            request.timeStamp = TimeStamp(sequenceNumber=self.count)
            request.notifyType = object_notify_type
            request.fromState = self.old_value
            request.toState = self.new_value  
            request.priority = notification_class_priority[1]
              
            if self.new_value == 'normal':
                request.ackRequired = notification_class_ackRequired[0] 
            else:
                request.ackRequired = notification_class_ackRequired[-1] 
            if self.old_value == 'highLimit' or self.new_value == 'highLimit':
                request.eventValues = NotificationParameters(outOfRange=NotificationParametersOutOfRange(
                                                                                exceedingValue = self.obj.presentValue,
                                                                                statusFlags=object_status_flag,
                                                                                deadband=self.obj.deadband,
                                                                                exceededLimit=self.obj.highLimit                                                           
                                                                                               ))                  
            elif self.old_value == 'lowLimit' or self.new_value == 'lowLimit':
                request.eventValues = NotificationParameters(outOfRange=NotificationParametersOutOfRange(
                                                                                exceedingValue = self.obj.presentValue,
                                                                                statusFlags=object_status_flag,
                                                                                deadband=self.obj.deadband,
                                                                                exceededLimit=self.obj.lowLimit                                                           
                                                                                           ))  
            
            iocb = IOCB(request)
            self.obj._app.request_io(iocb)                    

                            

                
class GenericEventStateCriteria(EventNotificationDetection):
    properties_tracked = ['eventState']
    properties_reported = ['eventState']
    monitored_property_reference = ['eventState']
        
criteria_type_map = {
    'binaryInput': GenericEventStateCriteria,
    'binaryOutput': GenericEventStateCriteria,
    'binaryValue': GenericEventStateCriteria,
    'analogInput': GenericEventStateCriteria,
    'analogOutput': GenericEventStateCriteria,
    'analogValue': GenericEventStateCriteria,
}

class EventNotificationServices(Capability):
        def __init__(self):
            Capability.__init__(self)
            self.event_notification_detections = {}
            for obj in self.iter_objects():
                criteria_class = criteria_type_map.get(obj.objectType, None)
                if criteria_class != None:
                    self.event_notification_detections[obj] = criteria_class(obj)