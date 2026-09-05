from ..protocols.mqtt_client_protocol import MqttClientProtocol
import logging
import threading
from collections.abc import Callable
logger = logging.getLogger(__name__) 

class MQTTManager:
    def __init__(self, client: MqttClientProtocol,broker_address:str, broker_port:int,username: str, password: str,tls_enabled: bool = False):
        self._broker_address = broker_address
        self._broker_port = broker_port
        self._username = username
        self._password = password
        self._client = client
        self._tls_enabled = tls_enabled
        self._on_delivered_cb:dict[int,Callable[[bool], None]] = {}
        self._timers: dict[int,threading.Timer]  = {}
        self._client.set_on_publish(self._on_delivered)

    def connect(self) -> None:
        self._client.connect(self._username,self._password,self._broker_address,self._broker_port,self._tls_enabled)
        logger.info(f"Client connected at {self._broker_address}:{self._broker_port}")

    def is_connected(self):
        return self._client.is_connected()

    def disconnect(self):
        self._client.disconnect()
        logger.info("Disconnected from MQTT broker")
    
    def publish(self,topic,payload,*,on_delivered: Callable[[bool],None] | None = None,qos=0,retain=False, timeout:float = 10.0)->int:
        mid = self._client.publish(topic,payload,qos,retain)
        if qos > 0 and on_delivered:
            timer = threading.Timer(timeout,self._timeout_delivery,args=(mid,))
            timer.start()
            self._on_delivered_cb[mid] = on_delivered
            self._timers[mid] = timer 
        elif qos == 0 and on_delivered:
            on_delivered(True)
        logger.info(f"Published message to topic {topic}")
        return mid
    
    def set_on_connect(self, on_connect_callback):
        self._client.set_on_connect = on_connect_callback
        logger.info("On connect callback has been set")

    def set_on_message(self, on_message_callback):
        self._client.set_on_message = on_message_callback
        logger.info("On message callback has been set")

    def set_on_disconnect(self, on_disconnect_callback):
        self._client.set_on_disconnect = on_disconnect_callback
        logger.info("On disconnect callback has been set")

    def subscribe(self,topics) -> None:
        self._client.subscribe(topics)
        logger.info(f"Client has subscribed to the topics {topics}")

    #Function runs when client recives on publish callback
    def _on_delivered(self,mid:int)-> None:
        callback = self._on_delivered_cb.pop(mid,None)
        timer = self._timers.pop(mid,None)
        if callback:
            callback(True)
        if timer:
            timer.cancel()

    #Timeout message after x seconds so it does not stay pernamently as not delivered
    def _timeout_delivery(self,mid:int) -> None:
        callback = self._on_delivered_cb.pop(mid,None)
        self._timers.pop(mid,None)
        if callback:
            callback(False)