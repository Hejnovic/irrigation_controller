
from enum import IntEnum
class IrrigationState(IntEnum):
        IDLE = 0
        IRRIGATING = 1
        MANUAL_PUMP = 2
        MANUAL_SECTION = 3
        ERROR = 4 #Not much useful without hardware monitoring tools