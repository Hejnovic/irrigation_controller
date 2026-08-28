import sys
import pytest
from unittest.mock import MagicMock

sys.modules["gpiod"] = MagicMock()
sys.modules["gpiod.line"] = MagicMock()
sys.modules["gpiod.chip"] = MagicMock()
sys.modules["gpiod.line_request"] = MagicMock()
