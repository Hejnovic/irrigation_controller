from typing import Protocol

class MqttManagerProtocol(Protocol):

    def connect(self,username,password,broker_adress,broker_port,tls_enabled):
        ...

    def is_connected(self):
        ...

    def disconnect(self):
        ...

    def publish(self,topic,payload,qos,retain):
        ...

    def set_on_connect(self,on_connect_callback):
        ...

    def set_on_message(self,on_message_callback):
        ...

    def set_on_disconnect(self,on_disconnect_callback):
        ...

    def set_on_publish(self,on_publish_callback):
        ...

    def subscribe(self,topics) -> None:
        ...
