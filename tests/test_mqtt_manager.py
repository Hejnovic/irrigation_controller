from src.core.mqtt_manager import MQTTManager
from src.protocols.mqtt_client_protocol import MqttClientProtocol
import pytest
from unittest.mock import Mock, call, patch, MagicMock

## CONNECT TESTS
def test_connect_calls_connect():
    #Arrange
    mqtt_mock_client = Mock(spec=MqttClientProtocol)
    mqtt_manager = MQTTManager(mqtt_mock_client,"abc",1883,"user","pw",True)

    #Act
    mqtt_manager.connect()

    #Assert
    mqtt_mock_client.connect.assert_called_with("user","pw","abc",1883,True)

## IS CONNECTED TESTS
def test_is_connected_calls_is_connected():
    #Arrange
    mqtt_mock_client = Mock(spec=MqttClientProtocol)
    mqtt_manager = MQTTManager(mqtt_mock_client,"abc",1883,"user","pw",True)
    mqtt_mock_client.is_connected.return_value = True

    #Act
    is_connected = mqtt_manager.is_connected()

    #Assert
    mqtt_mock_client.is_connected.assert_called_once()
    assert is_connected == True

## DISCONNECT TESTS
def test_disconnect_calls_disconnect():
    #Arrange
    mqtt_mock_client = Mock(spec=MqttClientProtocol)
    mqtt_manager = MQTTManager(mqtt_mock_client,"abc",1883,"user","pw",True)

    #Act
    mqtt_manager.disconnect()

    #Assert
    mqtt_mock_client.disconnect.assert_called_once()

## PUBLISH TESTS
def test_publish_calls_publish():
    #Arrange
    mqtt_mock_client = Mock(spec=MqttClientProtocol)
    mqtt_manager = MQTTManager(mqtt_mock_client,"abc",1883,"user","pw",True)

    #Act
    mqtt_manager.publish("topic","haha")

    #Assert
    mqtt_mock_client.publish.assert_called_once_with("topic","haha",0, False)
    
def test_publish_add_callback_when_qos_greater_than_0():
    #Arrange
    mqtt_mock_client = Mock(spec=MqttClientProtocol)
    mqtt_manager = MQTTManager(mqtt_mock_client,"abc",1883,"user","pw",True)
    mqtt_manager._on_delivered_cb = {}
    mqtt_mock_client.publish.return_value = 7
    on_delivered = Mock()
    
    #Act
    mid = mqtt_manager.publish("topic","haha",on_delivered= on_delivered,qos=1)

    #Assert
    assert mqtt_manager._on_delivered_cb[mid] == on_delivered

def test_publish_add_timer_when_qos_greater_than_0():
    #Arrange
    mqtt_mock_client = Mock(spec=MqttClientProtocol)
    mqtt_manager = MQTTManager(mqtt_mock_client,"abc",1883,"user","pw",True)
    mqtt_mock_client.publish.return_value = 7
    on_delivered = Mock()
    
    #Act
    with patch('src.core.mqtt_manager.threading.Timer') as MockTimer:
        mid = mqtt_manager.publish("topic","haha",on_delivered= on_delivered,qos=1)
        mock_timer = MockTimer.return_value

    #Assert
    assert mqtt_manager._timers[mid] == mock_timer