from dataclasses import dataclass

@dataclass
class ScheduleEntry:
    start_time: str | None # eg "04:00" - None no start
    sections: list[str] | None