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
        
class OutOfServiceToggleDetection(DetectionAlgorithm):
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
        out_of_service = self.obj.outOfService
        status_flags = self.obj.statusFlags
        time_delay = self.obj.timeDelay

        status_flags.value[-1] = (lambda x:1 if x else 0)(out_of_service)
        TimeDelayOneShotTask = TimeDelayOneShot(when = TaskManager().get_time() + time_delay,
                                                obj = self.obj,
                                                prop = ['statusFlags'],
                                                value = [status_flags])
        TimeDelayOneShotTask.install_task()                       
                                                        
class GenericBinaryCriteria(OutOfServiceToggleDetection):

    properties_tracked = (
        'outOfService',
        )
    properties_reported = (
        'outOfService',
        'statusFlags',
        )
    monitored_property_reference = 'presentValue'   
    
class GenericAnalogCriteria(OutOfServiceToggleDetection):
    properties_tracked = (
        'outOfService',
        )
    properties_reported = (
        'outOfService',
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
                
class OutOfServiceToggleServices(Capability):
        def __init__(self):
            Capability.__init__(self)
            self.out_of_service_toggle_detections = {}
            for obj in self.iter_objects():
                criteria_class = criteria_type_map.get(obj.objectType, None)
                if criteria_class != None:
                    self.out_of_service_toggle_detections[obj] = criteria_class(obj)     