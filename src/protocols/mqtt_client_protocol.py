from typing import Protocol

class MqttClientProtocol(Protocol):

    def connect(self,username:str,password:str,broker_adress:str,broker_port:int,tls_enabled:bool):
        ...

    def is_connected(self):
        ...

    def disconnect(self):
        ...

    def publish(self,topic,payload,qos,retain) -> int:
        ...

    def set_on_connect(self,on_connect_callback):
        ...

    def set_on_message(self,on_message_callback):
        ...

    def set_on_disconnect(self,on_disconnect_callback):
        ...

    def set_on_publish(self,on_publish_callback):
        ...

    def subscribe(self,topics:list[tuple[str,int]]):
        ...