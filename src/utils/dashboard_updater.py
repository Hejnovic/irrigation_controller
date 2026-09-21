import logging
from .enums import IrrigationState
from ..protocols.time_manager_protocol import TimeManagerProtocol
from ..protocols.mqtt_manager_protocol import MqttManagerProtocol
from ..protocols.translator_protocol import TranslatorProtocol
from ..utils.schedule_entry import ScheduleEntry
logger = logging.getLogger(__name__)

class DashboardUpdater:

    def __init__(self):
        self._mqtt_manager:MqttManagerProtocol | None = None
        self._time_manager: TimeManagerProtocol | None  = None 
        self._translator: TranslatorProtocol | None = None
    def set_mqtt_manager(self, mqtt_manager):
        if mqtt_manager is None:
            logger.error("Cannot set None as MQTT manager")
            return
        if self._mqtt_manager is not None:
            logger.error("MQTT manager already set for DashboardUpdater")
            return
        self._mqtt_manager = mqtt_manager
        logger.info("MQTT manager set for DashboardUpdater")
        
    def set_time_manager(self, time_manager: TimeManagerProtocol):
        if time_manager is None:
            logger.error("Cannot set None as time manager")
            return
        if self._time_manager is not None:
            logger.error("Time manager already set for DashboardUpdater")
            return
        self._time_manager = time_manager
        self._time_manager.set_callback_on_minute_change(self.update_datetime)
        logger.info("Time manager set for DashboardUpdater")

    def set_translator(self,translator: TranslatorProtocol):
        if translator is None:
            logger.error("Cannot set None as time manager")
            return
        if self._translator is not None:
            logger.error("Time manager already set for DashboardUpdater")
            return
        self._translator = translator
        logger.info("Translator set for DashboardUpdater")

    def update_datetime(self,_):
        timestamp = self._time_manager.current_datetime
        weekday = self._time_manager.current_day_of_week
        self._mqtt_manager.publish("ds/deviceTime", f"{timestamp} - {weekday}",retain=True)
        logger.debug("Dashboard updated")

  
    def update_active_section(self, state:IrrigationState,**kwargs):
    #     class IrrigationState(IntEnum):
    #     IDLE = 0
    #     IRRIGATING = 1
    #     MANUAL_PUMP = 2
    #     MANUAL_SECTION = 3
    #     ERROR = 4 
    ## 5 states that have to consider
        match state:
            case IrrigationState.IDLE:   
                # self._mqtt_manager.publish("ds/activeSection","Urzadzenie jest bezczynne",retain=True)
                self._mqtt_manager.publish("ds/activeSection",self._translator.translate("device_idle"),retain=True)
                                          
            case IrrigationState.IRRIGATING:
                section = kwargs.get("section",None)
                time_interval = kwargs.get("time_interval", None)
                time_end = kwargs.get("time_end",None)
                # self._mqtt_manager.publish("ds/activeSection",f"Podlewanie sekcji nr {section[-1]}",retain=True)
                self._mqtt_manager.publish("ds/activeSection",self._translator.translate("section_running_auto",section=section[-1]),retain=True)
                self.update_time_interval(time_end=time_end,time_interval=time_interval)

            case IrrigationState.MANUAL_PUMP:
                # self._mqtt_manager.publish("ds/activeSection","Uruchomiono pompę w trybie manualnym",retain=True)
                self._mqtt_manager.publish("ds/activeSection",self._translator.translate("pump_running_manual"),retain=True)

            case IrrigationState.MANUAL_SECTION:
                section = kwargs.get("section",None)
                # self._mqtt_manager.publish("ds/activeSection",f"Uruchomiono ręcznie sekcję nr {section[-1]}",retain=True)
                self._mqtt_manager.publish("ds/activeSection",self._translator.translate("section_running_manual",section=section[-1]),retain=True)
            case IrrigationState.ERROR:
                error = kwargs.get("error",None)
                self._mqtt_manager.publish("ds/activeSection",self._translator.translate("error"),retain=True)
                logger.error(f"Error occured: {error}")

        logger.debug(f"Dashboard updated")

    def update_time_interval(self, **kwargs) -> None:
        time_end = kwargs.get("time_end",None)
        time_interval = kwargs.get("time_interval",None)
        if not time_interval or not time_end:
            self._mqtt_manager.publish("ds/timeInterval","",retain=True)
        else:
            # self._mqtt_manager.publish("ds/timeInterval", f"Zmiana sekcji o godzinie {time_end} - interwał: {time_interval} min",retain=True)
            self._mqtt_manager.publish("ds/timeInterval",self._translator.translate("time_interval_auto",time_end=time_end,time_interval=time_interval),retain=True)
        logger.debug(f"Dashboard updated")

    def update_schedule(self,schedule:ScheduleEntry) -> None:
        start_time = schedule.start_time
        sections = schedule.sections
        #sections are either ["all"], [] or ["section1","section2"] or None
        #start time is string HH:MM example: 05:25
        section_numbers = sorted([section[-1] for section in sections])
        if section_numbers == ["l"]:
            section_numbers = ["1","2","3","4","5"]
        if start_time:
            # self._mqtt_manager.publish("ds/currentSchedule",f"Start: {start_time}, sekcje: {(",".join(section_numbers))}",retain=True)
            self._mqtt_manager.publish("ds/currentSchedule",self._translator.translate("daily_schedule",sections=(",".join(section_numbers))),retain=True)
        else:
            # self._mqtt_manager.publish("ds/currentSchedule",f"Dzień bez podlewania",retain=True)
            self._mqtt_manager.publish("ds/currentSchedule",self._translator.translate("daily_schedule_empty"),retain=True)
        

    def reset_dashboard_buttons(self) -> None:
        self._mqtt_manager.publish("ds/startSection", 0)
        self._mqtt_manager.publish("ds/runPump", 0)
        logger.info("Dashboard buttons reset")

    def reset_dashboard_button(self,button) -> None:
        self._mqtt_manager.publish(button,0)
        logger.info(f"Dashboard button: {button} has been reset")
