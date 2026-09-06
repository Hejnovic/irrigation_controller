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

def test_publish_calls_callback_on_qos_0():
    #Arrange
    mqtt_mock_client = Mock(spec=MqttClientProtocol)
    mqtt_manager = MQTTManager(mqtt_mock_client,"abc",1883,"user","pw",True)
    mqtt_mock_client.publish.return_value = 7
    on_delivered = Mock()

    #Act
    mid = mqtt_manager.publish("topic","haha",on_delivered= on_delivered,qos=0)

    #Assert
    on_delivered.assert_called_once_with(True)

def test_publish_starts_timer():
    #Arrange
    mqtt_mock_client = Mock(spec=MqttClientProtocol)
    mqtt_manager = MQTTManager(mqtt_mock_client,"abc",1883,"user","pw",True)
    timeout_delivery_mock = Mock()
    mqtt_manager._timeout_delivery= timeout_delivery_mock
    callback = Mock()
    mqtt_mock_client.publish.return_value = 15

    #Act
    with patch('src.core.mqtt_manager.threading.Timer') as TimerMock:
        mqtt_manager.publish("topic","msg",on_delivered=callback,qos=2)

    #Assert
    TimerMock.assert_called_once_with(10,timeout_delivery_mock,args=(15,))
    TimerMock.return_value.start.assert_called_once()


## SET ON X TESTS
@pytest.mark.parametrize("method",["set_on_connect","set_on_message","set_on_disconnect"])
def test_set_on_connect_calls_set_on_connect(method):
    #Arrange
    mqtt_mock_client = Mock(spec=MqttClientProtocol)
    mqtt_manager = MQTTManager(mqtt_mock_client,"abc",1883,"user","pw",True)
    on_callback = Mock(__name__ = "callback")

    #Act
    getattr(mqtt_manager,method)(on_callback)

    #Assert
    getattr(mqtt_mock_client,method).assert_called_once_with(on_callback)

@pytest.mark.parametrize("method",["set_on_connect","set_on_message","set_on_disconnect"])
def test_set_on_x_does_not_assign_non_callable(method):
    #Arrange
    mqtt_mock_client = Mock(spec=MqttClientProtocol)
    mqtt_manager = MQTTManager(mqtt_mock_client,"abc",1883,"user","pw",True)
    on_not_a_callback = 17

    #Act
    getattr(mqtt_manager,method)(on_not_a_callback)

    #Assert
    getattr(mqtt_mock_client,method).assert_not_called()

## SUBSCRIBE TESTS
def test_subscribe_calls_subscribe():
    #Arrange
    mqtt_mock_client = Mock(spec=MqttClientProtocol)
    mqtt_manager = MQTTManager(mqtt_mock_client,"abc",1883,"user","pw",True)
    topics = ["topic1","topic2"]

    #Act
    mqtt_manager.subscribe(topics)

    #Arrange
    mqtt_mock_client.subscribe.assert_called_with(topics)


## ON DELIVERED TESTS
def test_on_delivered_calls_callback():
    #Arrange
    mqtt_mock_client = Mock(spec=MqttClientProtocol)
    mqtt_manager = MQTTManager(mqtt_mock_client,"abc",1883,"user","pw",True)
    callback = Mock()
    mqtt_manager._on_delivered_cb[15] = callback

    #Act
    mqtt_manager._on_delivered(15)

    #Assert
    callback.assert_called_once_with(True)

def test_on_delivered_does_not_callback_when_it_does_not_exist():
    #Arrange
    mqtt_mock_client = Mock(spec=MqttClientProtocol)
    mqtt_manager = MQTTManager(mqtt_mock_client,"abc",1883,"user","pw",True)
    callback = Mock()

    #Act
    mqtt_manager._on_delivered(15)

    #Assert
    callback.assert_not_called()

def test_on_delivered_cancel_timer():
    #Arrange
    mqtt_mock_client = Mock(spec=MqttClientProtocol)
    mqtt_manager = MQTTManager(mqtt_mock_client,"abc",1883,"user","pw",True)
    callback = Mock()
    timer = Mock()
    mqtt_manager._on_delivered_cb[15] = callback
    mqtt_manager._timers[15] = timer

    #Act
    mqtt_manager._on_delivered(15)

    #Assert
    timer.cancel.assert_called_once()

def test_on_delivered_does_not_cancel_timer_when_it_does_not_exist():
    #Arrange
    mqtt_mock_client = Mock(spec=MqttClientProtocol)
    mqtt_manager = MQTTManager(mqtt_mock_client,"abc",1883,"user","pw",True)
    timer = Mock()


    #Act
    mqtt_manager._on_delivered(15)

    #Assert
    timer.cancel.assert_not_called()

## TOMEOUT DELIVERY TESTS
def test_timeout_delivery_calls_callback():
    #Arrange
    mqtt_mock_client = Mock(spec=MqttClientProtocol)
    mqtt_manager = MQTTManager(mqtt_mock_client,"abc",1883,"user","pw",True)
    callback = Mock()
    mqtt_manager._on_delivered_cb[15] = callback

    #Act
    mqtt_manager._timeout_delivery(15)

    #Assert
    callback.assert_called_once_with(False)

def test_timeout_delivery_pops_timer():
    #Arrange
    mqtt_mock_client = Mock(spec=MqttClientProtocol)
    mqtt_manager = MQTTManager(mqtt_mock_client,"abc",1883,"user","pw",True)
    callback = Mock()
    timer = Mock()
    mqtt_manager._on_delivered_cb[15] = callback
    mqtt_manager._timers[15] = timer

    #Act
    mqtt_manager._timeout_delivery(15)

    #Assert
    assert len(mqtt_manager._timers) == 0

