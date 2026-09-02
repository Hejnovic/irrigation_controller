from ..utils.schedule_entry import ScheduleEntry
import json
import logging
from pathlib import Path
from collections.abc import Callable
from ..protocols.time_manager_protocol import TimeManagerProtocol
logger = logging.getLogger(__name__)

    
class Scheduler:
    def __init__(self):
        self._schedule: dict[str, ScheduleEntry] = { #Default schedule, can be loaded from config file
            "Monday": ScheduleEntry(start_time="04:00", sections=["all"]),
            "Tuesday": ScheduleEntry(start_time="04:00", sections=["section3"]),
            "Wednesday": ScheduleEntry(start_time="04:00", sections=["all"]),
            "Thursday": ScheduleEntry(start_time="04:00", sections=["section3"]),
            "Friday": ScheduleEntry(start_time=None, sections=[]),
            "Saturday": ScheduleEntry(start_time="04:00", sections=["all"]),
            "Sunday": ScheduleEntry(start_time=None, sections=[])
        }
        self._default_irrigation_time:int = 10
        self._adjustment:float = 0 # In %
        self._time_manager:TimeManagerProtocol | None = None
        self._specific_section_irrigation_time: dict[str,int] = {} # minutes, can be loaded from config file
        self._winter_months: list[str] = [] # can be loaded from config file
        self._callbacks_on_schedule_change: list[Callable[..., None]] = []

    def set_time_manager(self, time_manager: TimeManagerProtocol):
        if time_manager is None:
            logger.error("Cannot set None as time manager")
            return
        if self._time_manager is not None:
            logger.error("Time manager already set for Scheduler")
            return
        self._time_manager = time_manager
        logger.info("Time manager set for Scheduler")
    
    def get_irrigation_time(self, section_name: str) -> int:
        return self._specific_section_irrigation_time.get(section_name, self._default_irrigation_time)*(1+self._adjustment)
    
    def get_schedule_for_day(self, day_of_week: str) -> ScheduleEntry:
        month = self._time_manager.current_month
        if month in self._winter_months:
            logger.info(f"Current month is {month}, which is in the winter months list. Returning empty schedule for {day_of_week}.")
            return ScheduleEntry(start_time=None, sections=[])
        return self._schedule.get(day_of_week, ScheduleEntry(start_time=None, sections=[]))
    
    def set_callback_on_schedule_change(self, callback: Callable):
        if not callable(callback):
            logger.warning(f"Can't set non-callable as callback: {callback}")
            return
        if callback not in self._callbacks_on_schedule_change:
            self._callbacks_on_schedule_change.append(callback)
            logger.info(f"Registered schedule change callback: {callback.__name__}")

    ##TODO separate module that loads files - json/yaml etc
    def load_schedule_from_json_file(self, json_file_path: Path):
        #Example: {"Monday":{"start_time":"04:00","sections":["all"]}, "Wednesday": ... }
        logger.info(f"Loading irrigation schedule from {json_file_path}")
        if not json_file_path.is_file():
            logger.warning(f"Irrigation schedule config file not found at {json_file_path}. Using default irrigation times.")
            return
        with open(json_file_path, 'r') as f:
            try:
                data: dict[str,dict] = json.load(f)
            except json.JSONDecodeError as e:
                logger.error(f"Provided file is not parsable JSON with {e.msg}, line: {e.lineno}, column: {e.colno}")
                return
        ##TODO type checking 
        for day, entry in data.items(): # Don't need to clear existing cuz schedule is expected always defined for all days, defining only few days will leave other entries unaffected
            #Validate if entry has needed keys for setting up schedule
            entry_keys = entry.keys()
            if "start_time" in entry_keys and "sections" in entry_keys:
                self._schedule[day] = ScheduleEntry(start_time=entry.get("start_time",None), sections=entry.get("sections", []))
            else:
                logger.error(f"Entry does not include mandatory fields: start_time and sections. Leaving schedule for day {day} unchanged")
        ## pass schedule to gpio controller as well
        for callback in self._callbacks_on_schedule_change:
            try:
                callback(self._time_manager.current_day_of_week)  # I think it needs to be done better 
            except Exception as e:
                logger.error(f"Error in schedule change callback: {e}")
        logger.info(f"Schedule loaded from {json_file_path}")
        
    def load_irrigation_times_from_json_file(self, json_file_path: Path):
        #Example: {"section1": 15 , "section3": 25}
        logger.info(f"Loading irrigation times from {json_file_path}")
        if not json_file_path.is_file():
            logger.warning(f"Irrigation times config file not found at {json_file_path}. Using default irrigation times.")
            return
        with open(json_file_path, 'r') as f:
            try:
                data = json.load(f) 
            except json.JSONDecodeError as e:
                logger.error(f"Provided file is not parsable JSON with {e.msg}, line: {e.lineno}, column: {e.colno}")
                return
        ##TODO type checking 
        self._specific_section_irrigation_time = {} # Clear existing
        for section, value in data.items():
            #Validate if entry has int value assigned to section
            if type(value) is not int:
                logger.error(f"Expected int and got {value} for {section}")
                return
            if section == "default":
                self._default_irrigation_time = value
            else:    
                self._specific_section_irrigation_time[section] = value
        logger.info(f"Irrigation times loaded from {json_file_path}")
    
    def load_winter_months_from_json_file(self, json_file_path: Path):
        #Example: ["October","November", "December", "January", "February", "March", "April"]
        logger.info(f"Loading winter months from {json_file_path}")
        if not json_file_path.is_file():
            logger.warning(f"Winter months config file not found at {json_file_path}. Using default winter months.")
            return
        with open(json_file_path, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                logger.error(f"Provided file is not parsable JSON with {e.msg}, {e.doc}")
                return
        ##TODO type checking 
        if type(data) is not list:
            logger.error(f"Provided data is not a list")
            return
        for entry in data:
            if type(entry) is not str:
                logger.error(f"Provided entry {entry} in data is not string")
                return
        self._winter_months = data
        logger.info(f"Winter months loaded from {json_file_path}")

    def load_weather_adjustment_from_json_file(self,json_file_path: Path):
        #Example: {"adj_percentage": 25, "total_pop": 0.5, "days_analyzed": 5, "avg_max_temps": 26.43, "max_temp": 28.95}
        #This is run by cron job - when error is occured maybe just rerun cron job?
        logger.info(f"Loading weather adjustments from {json_file_path}")
        if not json_file_path.is_file():
            logger.warning(f"Weather adjustment config file at {json_file_path} not found. Not taking adjustments to irrigation times")
            return
        with open(json_file_path, 'r') as f:
            try:
                data = json.load(f) 
            except json.JSONDecodeError as e:
                logger.error(f"Provided file is not parsable JSON with {e.msg}, line: {e.lineno}, column: {e.colno}")
                return
        ##TODO type checking
        if not isinstance(data,dict):
            logger.error(f"Provided data is not a dict")
            return
        self._adjustment = round(data.get("adj_percentage",0)/100,2)
        logger.info(f"Adjustment loaded: {self._adjustment}")