from .core.mqtt_manager import MQTTManager
from .utils.time_manager import TimeManager
from .utils.dashboard_updater import DashboardUpdater
from .utils.cleanup_manager import CleanupManager
from .core.gpio_controller import GPIOController
from .core.scheduler import Scheduler
from .utils.watchdog import Watchdog
from .utils.load_logger_config_yml import load_logging_config_yml
from .adapters.paho_mqtt_adapter import PahoMqttAdapter
from .utils.translator import Translator
from .utils.enums import MQTTTopics
from .utils.gpiod_config_builder import GPIOBuilder
from .utils.json_loader import load_json_file
import os
from pathlib import Path



import json
import logging
import asyncio

logger = logging.getLogger(__name__)

load_logging_config_yml(logger=logger)


BLYNK_AUTH = os.environ["BLYNK_AUTH"]
BROKER = os.environ["MQTT_BROKER"]
PORT = int(os.environ["MQTT_PORT"])
TLS_ENABLED = bool(os.environ["MQTT_TLS_ENABLED"])
LOCALE = os.environ["LOCALE"]
DIR_PATH = Path(__file__).resolve().parent
PIN_CONFIG = load_json_file(f"{DIR_PATH}/configs/irrigation_configs/pin_config.json")



cleanup_manager = CleanupManager()
gpiod_config_builder = GPIOBuilder(PIN_CONFIG)
gpio_controller = GPIOController(gpiod_config_builder)
scheduler = Scheduler()
client = PahoMqttAdapter()
mqtt_manager = MQTTManager(client,BROKER, PORT, username="device", password=BLYNK_AUTH, tls_enabled=TLS_ENABLED)
time_manager = TimeManager()
dashboard_updater = DashboardUpdater()
watchdog = Watchdog((DIR_PATH/"configs").resolve())
translator = Translator((DIR_PATH/"locales").resolve())
translator.set_locale(LOCALE)

def on_connect(rc):
    if rc == 0:
        logger.info(f"Connected to MQTT broker at {BROKER}:{PORT} with TLS={TLS_ENABLED}")
        # Subscribe to control pin(s)
        mqtt_manager.subscribe(MQTTTopics.get_topics_list())
        mqtt_manager.publish(MQTTTopics.ACTIVE_SECTION.topic,translator.translate("device_idle"),qos=MQTTTopics.ACTIVE_SECTION.qos)
        mqtt_manager.publish(MQTTTopics.CHOOSE_SECTION.topic, 1, qos=MQTTTopics.CHOOSE_SECTION.qos, retain=True) 
        mqtt_manager.publish(MQTTTopics.CURRENT_SCHEDULE.topic,"",qos=MQTTTopics.CHOOSE_SECTION.qos)
        mqtt_manager.publish(MQTTTopics.TIME_INTERVAL.topic, "",qos=MQTTTopics.TIME_INTERVAL.qos)
        mqtt_manager.publish(MQTTTopics.RUN_PUMP.topic, 0,qos=MQTTTopics.RUN_PUMP.qos) # This resets UI button
        mqtt_manager.publish(MQTTTopics.START_SECTION.topic, 0,qos=MQTTTopics.START_SECTION.qos) # This resets UI button
        dashboard_updater.update_schedule(scheduler.get_schedule_for_day(time_manager.current_day_of_week))
    else:
        logger.warning(f"Connection failed with code {rc}")

def on_message(msg):
    topic = msg.topic
    payload = None
    try: 
        payload = msg.payload.decode('utf-8')
        match topic:
            case MQTTTopics.RUN_PUMP.downlink:
                gpio_controller.run_pump()
            case MQTTTopics.CHOOSE_SECTION.downlink:
                gpio_controller.choose_section(int(payload))
            case MQTTTopics.START_SECTION.downlink:
                gpio_controller.start_selected_section()
            case MQTTTopics.STOP_DEVICE.downlink: #Clicking button sends 1 when pressed and 0 instantly when you lift finger
                if int(payload) == 1:
                    gpio_controller.stop_device()
            case MQTTTopics.START_IRRIGATION.downlink: #The same as STOP_DEVICE 
                if int(payload) == 1:
                    gpio_controller.start_manual_irrigation()
            case _:
                logger.warning("Unknown topic")
                pass
        logger.info(f"Received message on topic {topic}: {payload}")
    except ValueError as e:
        logger.error(f"Wrong format of payload for topic {topic}: {payload!r} ({e})")
    except Exception as e:
        logger.exception(f"Error processing message on topic {topic}: ({e})")
        

def on_disconnect(rc):
    #reconnect is handled by reconnect_delay_set
    if rc != 0:  # 0 = clean disconnect
        logger.warning(f"Unexpected disconnect (rc={rc}). Auto-reconnecting...")
    else:
        logger.info("Clean disconnect from MQTT broker")

async def day_loop():
    while True:
        time_manager.update_day() 
        time_manager.update_time()
        await asyncio.sleep(1)  # Run every second - though it creates overhead - more precise would be tracking time at enter and then subcract whatever value of the time is in the end of the day_loop and then use asyncio.sleep(max(0, 1 - time_elapsed)) 

async def main():
    cleanup_manager.register(gpio_controller.cleanup)
    mqtt_manager.set_on_connect(on_connect)
    mqtt_manager.set_on_message(on_message)
    mqtt_manager.set_on_disconnect(on_disconnect)
    dashboard_updater.set_mqtt_manager(mqtt_manager)
    dashboard_updater.set_time_manager(time_manager)
    dashboard_updater.set_translator(translator)
    scheduler.set_time_manager(time_manager)
    scheduler.set_callback_on_schedule_change(gpio_controller.set_daily_schedule)
    gpio_controller.set_time_manager(time_manager)
    gpio_controller.set_scheduler(scheduler)
    gpio_controller.set_dashboard_updater(dashboard_updater)
    gpio_controller.set_callback_on_stop_device(dashboard_updater.reset_dashboard_buttons)
    watchdog.register_handler("irrigation_schedule.json", scheduler.load_schedule_from_json_file)
    watchdog.register_handler("irrigation_section_time.json", scheduler.load_irrigation_times_from_json_file)
    watchdog.register_handler("winter_months.json", scheduler.load_winter_months_from_json_file)
    watchdog.register_handler("weather_adjustment.json",scheduler.load_weather_adjustment_from_json_file)
    watchdog.preload_configs()
    mqtt_manager.connect()
    await asyncio.gather(
        day_loop(),
        watchdog.watch()
    )
if __name__ == "__main__":
    asyncio.run(main())



