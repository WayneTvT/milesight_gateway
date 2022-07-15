from bacpypes.debugging import bacpypes_debugging, DebugContents, ModuleLogger
from bacpypes.capability import Capability

from bacpypes.core import deferred
from bacpypes.task import OneShotTask, RecurringFunctionTask, TaskManager
from bacpypes.iocb import IOCB

from bacpypes.basetypes import DeviceAddress, COVSubscription, PropertyValue, Recipient, RecipientProcess, ObjectPropertyReference
from bacpypes.constructeddata import ListOf, Any
from bacpypes.apdu import  SimpleAckPDU, Error, RejectPDU, AbortPDU
from bacpypes.errors import ExecutionError

from bacpypes.object import Property
from bacpypes.service.detect import DetectionAlgorithm, monitor_filter

_debug = 0
_log = ModuleLogger(globals())

class TimeDelayOneShot(OneShotTask):
    def __init__(self, when=None,obj = None ,prop=None,value=None):
        OneShotTask.__init__(self,when)
        self.obj = obj
        self.prop = prop
        self.value = value
    def process_task(self):
        for i in range(len(self.prop)):
            setattr(self.obj,self.prop[i],self.value[i])
        
class CovToggleDetection(DetectionAlgorithm):
    properties_tracked = ()
    properties_reported = ()
    monitored_property_reference = None    
    def __init__(self, obj):
        DetectionAlgorithm.__init__(self)
        self.obj = obj
        self._triggered = False

        kwargs = {}
        for property_name in self.properties_tracked:
            setattr(self, property_name, None)
            kwargs[property_name] = (obj, property_name)
        self.bind(**kwargs)
        
    def execute(self):
        self.toggle()
        
    def toggle(self):
        current_time = TaskManager().get_time()
        if self.obj.objectIdentifier[0] in ['binaryInput','binaryOutput','binaryValue']:
            alarm_value = self.obj.alarmValue
            present_value = self.obj.presentValue
            status_flags = self.obj.statusFlags
            time_delay = self.obj.timeDelay
            time_delay_normal = self.obj.timeDelayNormal
            if present_value == alarm_value:
                status_flags.value[0] = 1
                TimeDelayOneShotTask = TimeDelayOneShot(when = TaskManager().get_time() + time_delay,
                                                        obj = self.obj,
                                                        prop = ['statusFlags','eventState'],
                                                        value = [status_flags,'offnormal'])
                TimeDelayOneShotTask.install_task()
            else:
                status_flags.value[0] = 0
                TimeDelayOneShotTask = TimeDelayOneShot(when = TaskManager().get_time() + time_delay_normal,
                                                        obj = self.obj,
                                                        prop = ['statusFlags','eventState'],
                                                        value = [status_flags,'normal'])
                TimeDelayOneShotTask.install_task()  
               
        elif self.obj.objectIdentifier[0] in ['analogInput','analogOutput','analogValue']:                                                     
            present_value = self.obj.presentValue
            high_limit = self.obj.highLimit
            low_limit = self.obj.lowLimit                                                        
            status_flags = self.obj.statusFlags
            deadband = self.obj.deadband
            time_delay = self.obj.timeDelay
            time_delay_normal = self.obj.timeDelayNormal
            limit_enable = self.obj.limitEnable
            event_state = self.obj.eventState
            if limit_enable[-1] == 1:
                if event_state == 'normal' and present_value > high_limit and limit_enable[-1] == 1  :
                    status_flags.value[0] = 1
                    TimeDelayOneShotTask = TimeDelayOneShot(when = TaskManager().get_time() + time_delay,
                                                            obj = self.obj,
                                                            prop = ['statusFlags','eventState'],
                                                            value = [status_flags,'highLimit'])
                    TimeDelayOneShotTask.install_task()                                                          
                elif event_state == 'highLimit' and present_value < (high_limit - deadband) and present_value > low_limit and limit_enable[-1] == 1:
                    status_flags.value[0] = 0
                    TimeDelayOneShotTask = TimeDelayOneShot(when = TaskManager().get_time() + time_delay_normal,
                                                            obj = self.obj,
                                                            prop = ['statusFlags','eventState'],
                                                            value = [status_flags,'normal'])
                    TimeDelayOneShotTask.install_task()     
                    
                elif event_state == 'lowLimit' and present_value > high_limit and limit_enable[-1] == 1:
                    status_flags.value[0] = 1
                    TimeDelayOneShotTask = TimeDelayOneShot(when = TaskManager().get_time() + time_delay_normal,
                                                            obj = self.obj,
                                                            prop = ['statusFlags','eventState'],
                                                            value = [status_flags,'highLimit'])
                    TimeDelayOneShotTask.install_task()                       
            else:
                if event_state == 'highLimit':
                    status_flags.value[0] = 0
                    setattr(self.obj,'statusFlags',status_flags)
                    setattr(self.obj,'eventState','normal') 
                                                        
            if limit_enable[0] == 1:
                if event_state == 'normal' and present_value < low_limit and limit_enable[0] == 1  :
                    status_flags.value[0] = 1
                    TimeDelayOneShotTask = TimeDelayOneShot(when = TaskManager().get_time() + time_delay,
                                                            obj = self.obj,
                                                            prop = ['statusFlags','eventState'],
                                                            value = [status_flags,'lowLimit'])
                    TimeDelayOneShotTask.install_task()                               
                elif event_state == 'lowLimit' and present_value > (low_limit + deadband) and present_value < high_limit and limit_enable[0] == 1:
                    status_flags.value[0] = 0        
                    TimeDelayOneShotTask = TimeDelayOneShot(when = TaskManager().get_time() + time_delay_normal,
                                                            obj = self.obj,
                                                            prop = ['statusFlags','eventState'],
                                                            value = [status_flags,'normal'])
                    TimeDelayOneShotTask.install_task()  
                    
                elif event_state == 'highLimit' and present_value < low_limit and limit_enable[0] == 1:
                    status_flags.value[0] = 1
                    TimeDelayOneShotTask = TimeDelayOneShot(when = TaskManager().get_time() + time_delay_normal,
                                                            obj = self.obj,
                                                            prop = ['statusFlags','eventState'],
                                                            value = [status_flags,'lowLimit'])
                    TimeDelayOneShotTask.install_task()                     
            else:
                if event_state == 'lowLimit':
                    status_flags.value[0] = 0 
                    setattr(self.obj,'statusFlags',status_flags)
                    setattr(self.obj,'eventState','normal')                 
                    
                    
                                                        
class GenericBinaryCriteria(CovToggleDetection):

    properties_tracked = (
        'presentValue',
        'statusFlags',
        )
    properties_reported = (
        'presentValue',
        'statusFlags',
        )
    monitored_property_reference = 'presentValue'   
    
class GenericAnalogCriteria(CovToggleDetection):

    properties_tracked = (
        'presentValue',
        'statusFlags',
        'limitEnable',
        'highLimit',
        'lowLimit'
        )
    properties_reported = (
        'presentValue',
        'statusFlags',
        )
    monitored_property_reference = 'presentValue'      

criteria_type_map = {
    'binaryInput': GenericBinaryCriteria,
    'binaryOutput': GenericBinaryCriteria,
    'binaryValue': GenericBinaryCriteria,
    'analogInput': GenericAnalogCriteria,
    'analogOutput': GenericAnalogCriteria,
    'analogValue': GenericAnalogCriteria,
}
                
class CovToggleServices(Capability):
        def __init__(self):
            Capability.__init__(self)
            self.cov_toggle_detections = {}
            for obj in self.iter_objects():
                criteria_class = criteria_type_map.get(obj.objectType, None)
                if criteria_class != None:
                    self.cov_toggle_detections[obj] = criteria_class(obj)     