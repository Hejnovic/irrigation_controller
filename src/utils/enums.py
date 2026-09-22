
from enum import IntEnum, StrEnum, Enum
from dataclasses import dataclass
class IrrigationState(IntEnum):
        IDLE = 0
        IRRIGATING = 1
        MANUAL_PUMP = 2
        MANUAL_SECTION = 3
        ERROR = 4 #Not much useful without hardware monitoring tools

@dataclass(frozen=True)
class TopicConfig:
        name:str
        qos: int = 0

class MQTTTopics(Enum):
        RUN_PUMP = TopicConfig("ds/runPump",2)
        CHOOSE_SECTION = TopicConfig("ds/choosingSection",1)
        START_SECTION = TopicConfig("ds/startSection",2)
        STOP_DEVICE = TopicConfig("ds/stopDevice",2)
        START_IRRIGATION = TopicConfig("ds/startIrigation",2)
        ACTIVE_SECTION = TopicConfig("ds/activeSection",1)
        CURRENT_SCHEDULE = TopicConfig("ds/currentSchedule",1)
        TIME_INTERVAL = TopicConfig("ds/timeInterval",1)
        DEVICE_TIME = TopicConfig("ds/deviceTime",0)
        @property
        def downlink(self) -> str:
                return f"downlink/{self.value.name}"
        @property
        def qos(self) -> int:
                return self.value.qos
        @property
        def topic(self) -> str:
                return self.value.name

        @classmethod
        def get_topics_list(cls) -> list[tuple[str,int]]:
                return [(topic.value.name, topic.value.qos) for topic in cls]
                