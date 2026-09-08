
import logging
from collections.abc import Callable
logger = logging.getLogger(__name__) 

class PahoMqttAdapter:
    def __init__(self):
        import paho.mqtt.client as mqtt
        self._mqtt = mqtt
        self._on_publish_cb: Callable[...] | None = None
        self._on_connect_cb: Callable[...] | None = None
        self._on_message_cb: Callable[...] | None = None
        self._on_disconnect_cb: Callable[...] | None = None
        self._client:mqtt.Client = mqtt.Client(self._mqtt.CallbackAPIVersion.VERSION2)
        self._client.on_publish = self._hanle_paho_publish
        self._client.on_connect = self._handle_paho_connect
        self._client.on_message = self._handle_paho_message
        self._client.on_disconnect = self._handle_paho_disconnect

    def connect(self,username,password,broker_adress,broker_port,tls_enabled):
        if(username and password):
            self._client.username_pw_set(username=username,password=password)
            logger.info("MQTT configured with username and password")
        if(tls_enabled):
            self._client.tls_set()
            logger.info("MQTT configured with TSL enabled")
        self._client.connect(host=broker_adress,port=broker_port)
        self._client.loop_start()

    def is_connected(self):
        return self._client.is_connected()
    
    def disconnect(self):
        self._client.disconnect()
        self._client.loop_stop()

    def publish(self,topic,payload,qos=0,retain=False):
        msg_info = self._client.publish(topic,payload,qos,retain)
        return msg_info.mid

    def set_on_connect(self, on_connect_callback):
        self._on_connect_cb = on_connect_callback

    def set_on_message(self, on_message_callback):
        self._on_message_cb = on_message_callback

    def set_on_disconnect(self, on_disconnect_callback):
        self._on_disconnect_cb = on_disconnect_callback

    def set_on_publish(self, on_publish_callback):
        self._on_publish_cb = on_publish_callback

    def subscribe(self, topics):
        self._client.subscribe(topics)

    def _hanle_paho_publish(self,client,userdata,mid,reason_code,properties):
        if self._on_publish_cb:
            self._on_publish_cb(mid)

    def _handle_paho_connect(self,client, userdata, connect_flags, reason_code, properties):
        if self._on_connect_cb:
            self._on_connect_cb(reason_code)

    def _handle_paho_message(self,client,userdata,message):
        if self._on_message_cb:
            self._on_message_cb(message)

    def _handle_paho_disconnect(self,client, userdata, disconnect_flags, reason_code, properties):
        if self._on_disconnect_cb:
            self._on_disconnect_cb(reason_code)