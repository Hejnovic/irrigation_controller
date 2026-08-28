from datetime import datetime, timedelta
import logging
logger = logging.getLogger(__name__)
# To not waste network resources, should create events that other components can add callbacks to instead of having all components check time every second. 
class TimeManager:
    def __init__(self):
        self._current_day = None
        self._start_time = None
        self._current_minute = None
        self._update_day_callbacks = []
        self._update_minute_callbacks = []

    @property
    def time_now(self):
        return datetime.now().timestamp()
    @property
    def elapsed_time(self):
        if self._start_time is None:
            return 0.0
        return datetime.now().timestamp() - self._start_time
    
    
    def reset_timer(self):
        self._start_time = datetime.now().timestamp()
    @property
    def current_day_of_week(self):
        return datetime.now().strftime("%A")
    @property
    def current_month(self):
        return datetime.now().strftime("%B")
    @property
    def current_datetime(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M") 
    @property
    def current_hour_minute(self):
        return datetime.now().strftime("%H:%M")
    @property
    def current_minute(self):
        return datetime.now().minute
    def set_callback_on_day_change(self, callback):
        if callback not in self._update_day_callbacks:
            self._update_day_callbacks.append(callback)
            logger.info(f"Registered day change callback: {callback.__name__}")
    def set_callback_on_minute_change(self, callback):
        if callback not in self._update_minute_callbacks:
            self._update_minute_callbacks.append(callback)
            logger.info(f"Registered minute change callback: {callback.__name__}")
    def add_minutes(self,time, minutes: int) -> str:
        return (datetime.strptime(time, "%H:%M") + timedelta(minutes=minutes)).strftime("%H:%M")
    def update_day(self):  
        new_day = self.current_day_of_week
        logger.debug(f"Checking for day change: current day is {self._current_day}, new day is {new_day}")
        if new_day != self._current_day:
            logger.info(f"Day changed from {self._current_day} to {new_day}")
            self._current_day = new_day
            for callback in self._update_day_callbacks:
                try:
                    callback(new_day)
                except Exception as e:
                    logger.error(f"Error in day change callback: {e}")

    def update_time(self):
        new_minute = self.current_minute
        if new_minute != self._current_minute:
            logger.debug(f"Minute changed from {self._current_minute} to {new_minute}")
            self._current_minute = new_minute
            for callback in self._update_minute_callbacks:
                try:
                    callback(new_minute)
                except Exception as e:
                    logger.error(f"Error in time change callback: {e}")