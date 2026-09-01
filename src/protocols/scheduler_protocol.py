from typing import Protocol

class SchedulerProtocol(Protocol):

    def set_time_manager(self,time_manager):
        ...

    def get_irrigation_time(self, section_name):
        ...

    def get_schedule_for_day(self,day_of_week):
        ...

    def set_callback_on_schedule_change(self, callback):
        ...

    def load_schedule_from_json_file(self, json_file_path):
        ...

    def load_irrigation_times_from_json_file(self, json_file_path):
        ...

    def load_winter_months_from_json_file(self, json_file_path):
        ...

    def load_weather_adjustment_from_json_file(self, json_file_path):
        ...