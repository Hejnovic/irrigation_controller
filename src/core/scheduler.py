from typing import List, Dict, Optional
from ..utils.schedule_entry import ScheduleEntry
import json
import logging
from pathlib import Path
from typing import Callable, List
logger = logging.getLogger(__name__)

    
class Scheduler:
    def __init__(self):
        self._schedule: Dict[str, ScheduleEntry] = { #Default schedule, can be loaded from config file
            "Monday": ScheduleEntry(start_time="04:00", sections=["all"]),
            "Tuesday": ScheduleEntry(start_time="04:00", sections=["section3"]),
            "Wednesday": ScheduleEntry(start_time="04:00", sections=["all"]),
            "Thursday": ScheduleEntry(start_time="04:00", sections=["section3"]),
            "Friday": ScheduleEntry(start_time=None, sections=[]),
            "Saturday": ScheduleEntry(start_time="04:00", sections=["all"]),
            "Sunday": ScheduleEntry(start_time=None, sections=[])
        }
        self._default_irrigation_time = 10
        self._time_manager = None
        self._specific_section_irrigation_time = {"section3": 25} # minutes, can be loaded from config file
        self._winter_months = ["October","November", "December", "January", "February", "March"] # can be loaded from config file
        self._callbacks_on_schedule_change: List[Callable[[], None]] = []
    def set_time_manager(self, time_manager):
        if time_manager is None:
            logger.error("Cannot set None as time manager")
            return
        if self._time_manager is not None:
            logger.error("Time manager already set for Scheduler")
            return
        self._time_manager = time_manager
        logger.info("Time manager set for Scheduler")
    
    def get_irrigation_time(self, section_name: str) -> int:
        return self._specific_section_irrigation_time.get(section_name, self._default_irrigation_time)
    
    def get_schedule_for_day(self, day_of_week: str) -> ScheduleEntry:
        month = self._time_manager.current_month
        if month in self._winter_months:
            logger.info(f"Current month is {month}, which is in the winter months list. Returning empty schedule for {day_of_week}.")
            return ScheduleEntry(start_time=None, sections=[])
        return self._schedule.get(day_of_week, ScheduleEntry(start_time=None, sections=[]))
    
    def set_callback_on_schedule_change(self, callback):
        if callback not in self._callbacks_on_schedule_change:
            self._callbacks_on_schedule_change.append(callback)
            logger.info(f"Registered schedule change callback: {callback.__name__}")

    def load_schedule_from_json_file(self, json_file_path: Path):
        #Example: {"Monday":{"start_time":"04:00","sections":["all"]}, "Wednesday": ... }
        logger.info(f"Loading irrigation schedule from {json_file_path}")
        if not json_file_path.is_file():
            logger.warning(f"Irrigation schedule config file not found at {json_file_path}. Using default irrigation times.")
            return
        with open(json_file_path, 'r') as f:
            data = json.load(f)
        for day, entry in data.items(): # Don't need to clear existing cuz schedule is expected always defined for all days
            self._schedule[day] = ScheduleEntry(start_time=entry.get("start_time"), sections=entry.get("sections", []))
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
            data = json.load(f)
        self._specific_section_irrigation_time = {} # Clear existing
        for section, time in data.items():
            if section == "default":
                self._default_irrigation_time = time
            else:    
                self._specific_section_irrigation_time[section] = time
        logger.info(f"Irrigation times loaded from {json_file_path}")
    
    def load_winter_months_from_json_file(self, json_file_path: Path):
        #Example: ["October","November", "December", "January", "February", "March", "April"]
        logger.info(f"Loading winter months from {json_file_path}")
        if not json_file_path.is_file():
            logger.warning(f"Winter months config file not found at {json_file_path}. Using default winter months.")
            return
        with open(json_file_path, 'r') as f: 
            data = json.load(f)
        self._winter_months = data
        logger.info(f"Winter months loaded from {json_file_path}")
    