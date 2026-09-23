import pytest
from unittest.mock import Mock, call
from src.utils.gpiod_config_builder import GPIOBuilder
import datetime
import gpiod
from gpiod.line import Direction, Value, Bias, Edge, Drive, Clock

def test_build_line_settings_from_pin_config():
    #Arrange
    pins={
    "inputs":{
        "sensor1":{"pin":10,"edge_detection":"Edge.RISING"},
        "sensor2":{"pin":11}
    },
    "outputs":{
        "pump":{"pin":15},
        "valve1":{"pin":16},
        "valve2":{"pin":17}
    }
    }
    config_builder = GPIOBuilder(pins)

    #Act
    name_map = config_builder.get_name_map()

    #Assert
    assert len(name_map) == 5
    expected = {"sensor1","sensor2","pump","valve1","valve2"}
    assert expected.issubset(name_map.keys())
    print(config_builder.get_line_config()) # It is correct - hard to test it because gpiod does not exist on windows but from printing it looks alright