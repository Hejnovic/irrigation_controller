import logging
logger = logging.getLogger(__name__)

class DashboardUpdater:

    def __init__(self):
        self._mqtt_manager = None
        self._time_manager = None 

    
    def set_mqtt_manager(self, mqtt_manager):
        if mqtt_manager is None:
            logger.error("Cannot set None as MQTT manager")
            return
        if self._mqtt_manager is not None:
            logger.error("MQTT manager already set for DashboardUpdater")
            return
        self._mqtt_manager = mqtt_manager
        logger.info("MQTT manager set for DashboardUpdater")
    def set_time_manager(self, time_manager):
        if time_manager is None:
            logger.error("Cannot set None as time manager")
            return
        if self._time_manager is not None:
            logger.error("Time manager already set for DashboardUpdater")
            return
        self._time_manager = time_manager
        self._time_manager.set_callback_on_minute_change(self.update_datetime_dashboard)
        logger.info("Time manager set for DashboardUpdater")
    def update_datetime_dashboard(self,_):
        if self._mqtt_manager is None:
            logger.error("MQTT manager not set for DashboardUpdater")
            return
        if self._time_manager is None:
            logger.error("Time manager not set for DashboardUpdater")
            return
        if not self._mqtt_manager.is_connected():
            logger.warning("Cannot update dashboard: MQTT broker is not reachable")
            return
        timestamp = self._time_manager.current_datetime
        self._mqtt_manager.publish("ds/deviceTime", f"{timestamp} - {self._time_manager.current_day_of_week}")
        logger.debug("Dashboard updated")

    def update_active_section(self, section_name):
        if self._mqtt_manager is None:
            logger.error("MQTT manager not set for DashboardUpdater")
            return
        if not self._mqtt_manager.is_connected():
            logger.warning("Cannot update dashboard: MQTT broker is not reachable")
            return
        self._mqtt_manager.publish("ds/activeSection", section_name)
        logger.debug(f"Dashboard updated with active section: {section_name}")

    def update_time_interval(self, time_interval):
        if self._mqtt_manager is None:
            logger.error("MQTT manager not set for DashboardUpdater")
            return
        if not self._mqtt_manager.is_connected():
            logger.warning("Cannot update dashboard: MQTT broker is not reachable")
            return
        self._mqtt_manager.publish("ds/timeInterval", time_interval)
        logger.debug(f"Dashboard updated with time interval: {time_interval}")
    def reset_dashboard_buttons(self):
        if self._mqtt_manager is None:
            logger.error("MQTT manager not set for DashboardUpdater")
            return
        if not self._mqtt_manager.is_connected():
            logger.warning("Cannot update dashboard: MQTT broker is not reachable")
            return
        self._mqtt_manager.publish("ds/startSection", 0)
        self._mqtt_manager.publish("ds/runPump", 0)
        logger.info("Dashboard buttons reset")