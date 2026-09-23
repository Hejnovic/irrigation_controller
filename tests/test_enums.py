from src.utils.enums import MQTTTopics
import pytest
from unittest.mock import Mock

def test_mqtttopics_return_topic_and_downlink_prefix():

    #Act & Assert
    assert MQTTTopics.RUN_PUMP.downlink == "downlink/ds/runPump"
    assert MQTTTopics.RUN_PUMP.topic == "ds/runPump"
