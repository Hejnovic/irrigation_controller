import gpiod
from gpiod.line import Direction, Value
from typing import Dict
# from ..utils.schedule_entry import ScheduleEntry
import logging
logger = logging.getLogger(__name__)

class GPIOController:
    class IrrigationState:
        IDLE = 0,
        IRRIGATING = 1,
        MANUAL_PUMP = 2,
        MANUAL_SECTION = 3
    def __init__(self, pin_mapping: Dict[str, int], chip = "/dev/gpiochip0", consumer="irrigation_controller"):
        self._daily_schedule = None
        self._pin_mapping = pin_mapping
        self._chosen_section = None
        self._time_manager = None
        self._scheduler = None
        self._dashboard_updater = None
        self._sections = None
        self._irrigation_state = self.IrrigationState.IDLE
        self._sections_to_irrigate = []
        self._current_section = None
        self._time_end = None
        self._start_time = None
        self._callback_on_stop_device = []
        config = { # Only outputs so far 
            pin: gpiod.LineSettings(
                direction=Direction.OUTPUT,
                output_value=Value.ACTIVE
            )
            for pin in pin_mapping.values()
        }
        
        self._gpio = gpiod.request_lines(
            chip,
            consumer=consumer,
            config=config
        )
        logger.info(f"GPIO lines requested: {self._pin_mapping}")
    def set_time_manager(self, time_manager):
        if time_manager is None:
            logger.error("Cannot set None as time manager")
            return
        if self._time_manager is not None:
            logger.error("Time manager already set for GPIOController")
            return
        self._time_manager = time_manager
        self._time_manager.set_callback_on_day_change(self.set_daily_schedule)
        self._time_manager.set_callback_on_minute_change(self.check_if_should_start_irrigation)
        self._time_manager.set_callback_on_minute_change(self.check_if_should_switch_section)
        logger.info("Time manager set for GPIOController")
    def set_scheduler(self, scheduler):
        if scheduler is None:
            logger.error("Cannot set None as scheduler")
            return
        if self._scheduler is not None:
            logger.error("Scheduler already set for GPIOController")
            return
        self._scheduler = scheduler
        logger.info("Scheduler set for GPIOController")
    def set_dashboard_updater(self, dashboard_updater):
        if dashboard_updater is None:
            logger.error("Cannot set None as dashboard updater")
            return
        if self._dashboard_updater is not None:
            logger.error("Dashboard updater already set for GPIOController")
            return
        self._dashboard_updater = dashboard_updater
        logger.info("Dashboard updater set for GPIOController")
    def set_callback_on_stop_device(self, callback):
        if callback is None:
            logger.error("Cannot set None as callback for stop device")
            return
        self._callback_on_stop_device.append(callback)
        logger.info(f"Registered stop device callback: {callback.__name__}")
    def set_value(self, name: str, state: bool):

        if name not in self._pin_mapping:
            logger.error(f"Unknown pin name: {name}")
            return
        pin = self._pin_mapping[name]
        value = Value.ACTIVE if state else Value.INACTIVE # Might need reversed because of relay module
        self._gpio.set_value(pin, value)
        logger.info(f"Set pin {name} (GPIO {pin}) to {'ACTIVE' if state else 'INACTIVE'}")

    def set_values(self, states: Dict[str, bool]):
        for name, state in states.items():
            if name not in self._pin_mapping:
                logger.error(f"Unknown pin name: {name}")
                continue
            pin = self._pin_mapping[name]
            value = Value.ACTIVE if state else Value.INACTIVE # Might need reversed because of relay module
            self._gpio.set_value(pin, value)
            logger.info(f"Set pin {name} (GPIO {pin}) to {'ACTIVE' if state else 'INACTIVE'}")
    def get_value(self, name: str) -> bool:
        if name not in self._pin_mapping:
            logger.error(f"Unknown pin name: {name}")
            return False
        
        pin = self._pin_mapping[name]
        value = self._gpio.get_value(pin)
        logger.info(f"Read pin {name} (GPIO {pin}): {'ACTIVE' if value else 'INACTIVE'}")
        return value == Value.ACTIVE
    ## MANUAL
    def run_pump(self, state: int): # Manual pump control, mqtt handler
        if self._irrigation_state == self.IrrigationState.IDLE or self._irrigation_state == self.IrrigationState.MANUAL_PUMP:
            self.set_value("pump", not state)
            self._irrigation_state = self.IrrigationState.MANUAL_PUMP if state == 1 else self.IrrigationState.IDLE
            logger.info(f"{'Started' if state == 1 else 'Stopped'} pump manually")
            self._dashboard_updater.update_active_section("Pompa została uruchomiona ręcznie" if state == 1 else "Urządzenie jest bezczynne")
    def choose_section(self, section_number: int): # Manual section choosing, mqtt handler
        if section_number < 1 or section_number > 5:
            logger.error(f"Invalid section number: {section_number}")
            return
        self._chosen_section = f"section{section_number}"
        logger.info(f"Chosen section: {self._chosen_section}")
    def start_selected_section(self, state: int): # Manual section control, mqtt handler

        if self._irrigation_state ==  self.IrrigationState.IDLE:
            if self._chosen_section is None:
                self._chosen_section = "section1" # Default to section1 if no section chosen
            self._irrigation_state = self.IrrigationState.MANUAL_SECTION
            self.set_value(self._chosen_section, False)
            self.set_value("pump", False)
            logger.info(f"Started irrigation for {self._chosen_section}")
            self._dashboard_updater.update_active_section(f"Ręcznie uruchomiono sekcję {self._chosen_section[-1]}")
        elif self._irrigation_state == self.IrrigationState.MANUAL_SECTION: 
            self._irrigation_state = self.IrrigationState.IDLE
            self.stop_device()
    def start_manual_irrigation(self):
        if self._irrigation_state != self.IrrigationState.IDLE:
            logger.warning("Cannot start manual irrigation: device is already irrigating")
            return
        self._irrigation_state = self.IrrigationState.IRRIGATING
        self.set_value("pump", False)
        self._start_time = self._time_manager.current_hour_minute
        self._sections_to_irrigate = sorted(self._pin_mapping.keys() - {"pump"})
        self._switch_to_next_section()
    ## MANUAL END
    def stop_device(self):
        all_inactive = { #It is flipped because of relay module, setting pin to ACTIVE actually turns it off
            pin: Value.ACTIVE for pin in self._pin_mapping.values()
        }
        self._gpio.set_values(all_inactive)
        self._start_time = None
        self._time_end = None
        self._irrigation_state = self.IrrigationState.IDLE
        logger.info("Stopped irrigation and set all pins to INACTIVE")
        self._dashboard_updater.update_active_section("Urządzenie jest bezczynne")
        self._dashboard_updater.update_time_interval("") #Just makes it empty on frontend

        for callback in self._callback_on_stop_device:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"Error in stop device callback: {e}")
    def _switch_to_next_section(self):
        if self._sections_to_irrigate:
            self._current_section = self._sections_to_irrigate.pop(0) # popping 1st element of sorted (guaranteed by scheduler) list - modyfing in place so no need to track of index
            self.set_value(self._current_section, False)
            logger.info(f"Started irrigation for {self._current_section} - for {self._scheduler.get_irrigation_time(self._current_section)} minute(s)")
            if self._time_end is None:
                irrigation_time = self._scheduler.get_irrigation_time(self._current_section)
                self._time_end = self._time_manager.add_minutes(self._start_time,irrigation_time)
            self._dashboard_updater.update_active_section(f"Podlewanie sekcji {self._current_section[-1]}")
            self._dashboard_updater.update_time_interval(f"Zmiana sekcji o godzinie {self._time_end} - interwał: {irrigation_time} min") 
        else:
            self.stop_device()
            logger.info("Irrigation sequence completed for all sections")
    def start_irrigation_auto(self):
        #self._daily_schedule -> contains either sections to irrigate or "all" or None 
        # If "all" -> irrigate all sections, if list of sections -> irrigate those sections, if None or empty -> do nothing
        # After starting irrigation, should set a timer for each section based on the schedule and time manager, after timer is up, switch to next section or stop irrigation if no more sections left.
        # TODO: or NOT TODO -> fetch irrigation schedule here instead of day_loop callback -> thinking about it you can't because schedule time also contains START TIME so HOW THE HELLY WOULD THIS FUNCTION KNOW WHEN TO START HAHAH
        # If want to implement schedule changes without day_loop delay watchdog needs to callback set_daily_schedule function of gpio controller and then that function needs to fetch data from scheduler 
        if not self._daily_schedule.sections:
            logger.info("No sections to irrigate, skipping irrigation")
            return
        if self._daily_schedule.sections == ["all"]:
            self._sections_to_irrigate = sorted(self._pin_mapping.keys() - {"pump"}) # If adding some sensor or smth this won't work - workaround maybe sorted(k for k in self._pin_mapping.keys() if k.startswithc("section") - assuming user names sections - sectionX
        else:
            self._sections_to_irrigate = sorted(self._daily_schedule.sections)
        self.set_value("pump", False)
        self._switch_to_next_section()

    def check_if_should_switch_section(self,_):
        if self._irrigation_state != self.IrrigationState.IRRIGATING:
            return
        current_time = self._time_manager.current_hour_minute 
        if current_time >= self._time_end: # When current time is equal to start time + irrigation time for current section
            self._start_time = self._time_end
            self._time_end = None
            self.set_value(self._current_section, True) # Stop current section
            self._switch_to_next_section()

    def check_if_should_start_irrigation(self,_):
        if self._irrigation_state != self.IrrigationState.IDLE:
            logger.warning("Cannot start irrigation: device is not in IDLE state")
            return
        if self._daily_schedule is None:
            logger.warning("Daily schedule not set, cannot check irrigation start")
            return
        if self._time_manager is None:
            logger.warning("Time manager not set, cannot check irrigation start")
            return
        if self._daily_schedule.start_time is None or self._daily_schedule.sections == []:
            return
        current_time = self._time_manager.current_hour_minute
        if current_time == self._daily_schedule.start_time:
            logger.info(f"Starting irrigation sequence at {self._time_manager.current_datetime} - {self._time_manager.current_day_of_week}")
            self._irrigation_state = self.IrrigationState.IRRIGATING
            self._start_time = self._daily_schedule.start_time
            self.start_irrigation_auto()
    def set_daily_schedule(self,new_day): #TODO if want after save file change - add caller as parameter and then if caller is watchdog - get current day from time manager and then fetch schedule from scheduler 
        self._daily_schedule = self._scheduler.get_schedule_for_day(new_day)
        logger.info(f"Received daily schedule: {self._daily_schedule}")
    def cleanup(self):
        if not hasattr(self, '_gpio') or self._gpio is None:
            return
        
        logger.info("Cleaning up GPIO controller")
        try:
            self.stop_device()  # Ensure all devices are stopped before cleanup
            self._gpio.release()
            self._gpio = None
            logger.info("GPIO controller cleaned up")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.cleanup()
        logger.info("GPIO lines released on exit")

