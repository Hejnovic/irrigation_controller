from typing import Protocol

class DashboardUpdaterProtocol(Protocol):

    def set_mqqt_manager(self,mqtt_manager) -> None:
        ...

    def set_time_manager(self,time_manager) -> None:
        ...

    def update_datetime(self,_) -> None:
        ...

    def update_active_section(self,state,**kwargs) -> None:
        ...

    def update_time_interval(self,time_end,irrigation_time) -> None:
        ...

    def update_schedule(self,schedule) -> None:
        ...

    def reset_dashboard_buttons(self) -> None:
        ...