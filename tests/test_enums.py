from src.utils.enums import MQTTTopics
import pytest
from unittest.mock import Mock

def test_mqtttopics_return_topic_and_downlink_prefix():

    #Act & Assert
    assert MQTTTopics.RUN_PUMP.downlink == "downlink/ds/runPump"
    assert MQTTTopics.RUN_PUMP.topic == "ds/runPump"

def test_mqtttopics_return_subscribe_topics_list():

    #Act & Assert
    assert MQTTTopics.get_topics_list() == [('ds/runPump', 2), ('ds/choosingSection', 1), ('ds/startSection', 2), ('ds/stopDevice', 2), ('ds/startIrigation', 2), ('ds/activeSection', 1), ('ds/currentSchedule',1), ('ds/timeInterval',1), ('ds/deviceTime',0),]