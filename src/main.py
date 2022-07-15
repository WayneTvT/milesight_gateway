import sys
import os 
import json
import logging
import logging.config
import commission_to_gateway
import utils
import bacnet
import mqtt
import time
from license import licensing
def main():
    logging.basicConfig(level = logging.INFO)
    project_path = os.path.dirname(sys.path[0])
    log_config_path = os.path.join(project_path,os.path.join('cfg', 'log_config.json'))
    commissioning_config_path = os.path.join(project_path,os.path.join('cfg', 'commitioning_json_structure.json'))
    license_key_path = os.path.join(project_path,'license_key.txt')

    log_config = utils.load_log_config(log_config_path)
    logging.config.dictConfig(log_config)

    commissioning_config = utils.read_json(commissioning_config_path)
    key = utils.get_license_key(commissioning_config,license_key_path)
    if key:
        licenser = licensing.action(project_path)
        licenser.generate_key(key)
    else:
        logging.info("License Key not found")

    api = commission_to_gateway.milesight_api(config_path=commissioning_config_path)
    #api.start_commissioning()
    mqttworker = mqtt.mqtt_worker(licenser,commissioning_config,
                                  event_logger=logging.getLogger('mqtt'),msg_logger = logging.getLogger('mqtt_msg'))

    cfg_convertor = utils.config_convertor(commissioning_config)
    cfg_convertor.process()
    bacnet_app = bacnet.Application(licenser,cfg_convertor.config,
                                        event_logger=logging.getLogger('bacnet'),msg_logger = logging.getLogger('bacnet_msg'))
    bacnet_app.start()
    mqttworker.run()
    SUMMARY_INTERVAL = 5
    while True:
        summary = utils.get_summary(commissioning_config)
        logging.info(summary)
        time.sleep(SUMMARY_INTERVAL)
        
if __name__ == "__main__":
    main()        