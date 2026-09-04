import paho.mqtt.client as mqtt
from paho.mqtt.enums import MQTTProtocolVersion
import logging

logger = logging.getLogger(__name__) 
##TODO Total rework - it is now just paho.mqtt wrapper that is not even good
class MQTTManager:
 
    def __init__(self, broker_address:str, broker_port:int, username: str ="", password: str="", tls_enabled:bool=False, client_version=MQTTProtocolVersion.MQTTv311, callback=mqtt.CallbackAPIVersion.VERSION2, userdata=None):
        self._broker_address = broker_address
        self._broker_port = broker_port
        self._username = username
        self._password = password
        self._client = mqtt.Client(callback,protocol=client_version,userdata=userdata)
        self._client.reconnect_delay_set(min_delay=1, max_delay=120)
        self._unnacked_messages: set[mqtt.MQTTMessageInfo] = set() 
        if username and password:
            self._client.username_pw_set(username, password)
            logger.info("MQTT client configured with username and password")
        if tls_enabled:
            self._client.tls_set()
            logger.info("MQTT client configured to use TLS")

    def connect(self):
        try:
            self._client.connect(self._broker_address, self._broker_port)
            logger.info(f"Connected to MQTT broker at {self._broker_address}:{self._broker_port}")
            self._client.loop_start()
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            raise
    def is_connected(self):
        return self._client.is_connected()
    def disconnect(self):
        self._client.disconnect()
        logger.info("Disconnected from MQTT broker")
    
    def publish(self,topic,payload,qos=0,retain=False):
        msg_info = self._client.publish(topic,payload,qos,retain)
        if qos > 0:
            self._unnacked_messages.add(msg_info.mid)
            msg_info.wait_for_publish()
        logger.info(f"Published message to topic {topic}")

    def on_connect(self, on_connect_callback):
        self._client.on_connect = on_connect_callback
    def on_message(self, on_message_callback):
        self._client.on_message = on_message_callback
    def on_disconnect(self, on_disconnect_callback):
        self._client.on_disconnect = on_disconnect_callback
    def on_publish(self, on_publish_callback):
        self._client.on_publish = on_publish_callback
