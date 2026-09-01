from typing import Protocol

class MqttManagerProtocol(Protocol):

    def connect(self):
        ...

    def is_connected(self):
        ...

    def disconnect(self):
        ...

    def publish(self,topic,payload,qos,retain):
        ...

    def on_connect(self,on_connect_callback):
        ...

    def on_message(self,on_message_callback):
        ...

    def on_disconnect(self,on_disconnect_callback):
        ...

    def on_publish(self,on_publish_callback):
        ...