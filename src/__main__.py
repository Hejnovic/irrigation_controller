from .core.mqtt_manager import MQTTManager
from .utils.time_manager import TimeManager
from .utils.dashboard_updater import DashboardUpdater
from .utils.cleanup_manager import CleanupManager
from .core.gpio_controller import GPIOController
from .core.scheduler import Scheduler
from .utils.watchdog import ConfigWatcher
from .utils.load_logger_config_yml import load_logging_config_yml
import os
from pathlib import Path



import time
import logging
import asyncio

logger = logging.getLogger(__name__)

load_logging_config_yml(logger=logger)

BLYNK_AUTH = os.environ.get("BLYNK_AUTH")
BROKER = os.environ.get("MQTT_BROKER")
PORT = int(os.environ.get("MQTT_PORT"))
TLS_ENABLED = os.environ.get("MQTT_TLS_ENABLED")
ALL_TOPICS =  os.environ.get("MQTT_ALL_TOPICS").split(",") # Comma-separated list of topics to subscribe to, e.g. "downlink/ds/startSection,downlink/ds/runPump"
DIR_PATH = Path(__file__).resolve().parent
# PUMP_PIN = 2
# SECTION_PIN1 = 3
# SECIONT_PIN2 = 4
# SECTION_PIN3 = 14
# SECTION_PIN4 = 15
# SECTION_PIN5 = 18
# gpio = gpiod.request_lines(
#     "/dev/gpiochip0",
#     consumer = "irigation_controller",
#     config = {
#         PUMP_PIN: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.ACTIVE),
#         SECTION_PIN1: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.ACTIVE),
#         SECIONT_PIN2: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.ACTIVE),
#         SECTION_PIN3: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.ACTIVE),
#         SECTION_PIN4: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.ACTIVE),
#         SECTION_PIN5: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.ACTIVE)
#     }
# )
PIN_CONFIG = {
    "pump": 17,
    "section1": 22,
    "section2": 23,
    "section3": 24,
    "section4": 25,
    "section5": 27
}


cleanup_manager = CleanupManager()
gpio_controller = GPIOController(PIN_CONFIG)
scheduler = Scheduler()
mqtt_manager = MQTTManager(BROKER, PORT, username="device", password=BLYNK_AUTH, TLS_enabled=TLS_ENABLED)
time_manager = TimeManager()
dashboard_updater = DashboardUpdater()
watchdog = ConfigWatcher((DIR_PATH/"configs").resolve())


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        logger.info(f"Connected to MQTT broker at {BROKER}:{PORT} with TLS={TLS_ENABLED}")
        # Subscribe to control pin(s)
        for topic in ALL_TOPICS:
            client.subscribe(topic, qos=2)
            logger.info(f"Subscribed to topic: {topic}")
        client.publish("ds/activeSection", "Urządzenie jest bezczynne")
        client.publish("ds/choosingSection", 1, qos=2) 
        client.publish("ds/timeInterval", "",qos=2)
        client.publish("ds/runPump", 0,qos=2)
        client.publish("ds/startSection", 0,qos=2)
    else:
        logger.warning(f"Connection failed with code {rc}")
def on_message(client, userdata, msg):
    topic = msg.topic
    try: 
        payload = msg.payload.decode('utf-8')
        match topic:
            case "downlink/ds/runPump":
                gpio_controller.run_pump(int(payload))
            case "downlink/ds/choosingSection":
                gpio_controller.choose_section(int(payload))
            case "downlink/ds/startSection":
                gpio_controller.start_selected_section(int(payload))
            case "downlink/ds/stopDevice":
                if int(payload) == 1:
                    gpio_controller.stop_device()
            case "downlink/ds/startIrigation":
                if int(payload) == 1:
                    gpio_controller.start_manual_irrigation()
    except Exception as e:
        logger.error(f"Error processing message on topic {topic}: {e}")
    logger.info(f"Received message on topic {topic}: {payload}")
def on_disconnect(client, userdata,flags, rc, properties=None):
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
    mqtt_manager.on_connect(on_connect)
    mqtt_manager.on_message(on_message)
    mqtt_manager.on_disconnect(on_disconnect)
    mqtt_manager.connect()
    cleanup_manager.register(gpio_controller.cleanup)
    dashboard_updater.set_mqtt_manager(mqtt_manager)
    dashboard_updater.set_time_manager(time_manager)
    scheduler.set_time_manager(time_manager)
    scheduler.set_callback_on_schedule_change(gpio_controller.set_daily_schedule)
    gpio_controller.set_time_manager(time_manager)
    gpio_controller.set_scheduler(scheduler)
    gpio_controller.set_dashboard_updater(dashboard_updater)
    gpio_controller.set_callback_on_stop_device(dashboard_updater.reset_dashboard_buttons)
    watchdog.register_handler("irrigation_schedule.json", scheduler.load_schedule_from_json_file)
    watchdog.register_handler("irrigation_section_time.json", scheduler.load_irrigation_times_from_json_file)
    watchdog.register_handler("winter_months.json", scheduler.load_winter_months_from_json_file)

    await asyncio.gather(
        day_loop(),
        watchdog.start()
    )
if __name__ == "__main__":
    # mqtt_manager.on_publish()
    asyncio.run(main())



