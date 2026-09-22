from typing import Protocol

class DashboardUpdaterProtocol(Protocol):

    def set_mqqt_manager(self,mqtt_manager):
        ...

    def set_time_manager(self,time_manager):
        ...

    def update_datetime(self,_):
        ...

    def update_active_section(self,state,**kwargs):
        ...

    def update_time_interval(self,time_end,irrigation_time):
        ...

    def update_schedule(self,schedule):
        ...

    def reset_dashboard_buttons(self):
        ...

    def load_locales(self,locales):
        ...