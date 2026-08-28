from dataclasses import dataclass
from typing import Optional, List
@dataclass
class ScheduleEntry:
    start_time: Optional[str] # eg "04:00" - None no start
    sections: Optional[List[str]]