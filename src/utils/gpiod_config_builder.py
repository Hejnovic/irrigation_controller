import gpiod
from gpiod.line import Direction, Value, Bias, Edge, Drive, Clock
import datetime

class GPIOBuilder():
    def __init__(self,config):
        self._name_map:dict[str,int] = {}
        self._config:dict[str,dict[str,str|int]] = config
        self._line_config = self._build_line_config()

    def _build_line_settings(self,cfg:dict,direction:Direction) -> gpiod.LineSettings:
        return  gpiod.LineSettings( #All defaults are taken from gpiod docs
            direction=direction,
            edge_detection=self._resolve_enum(cfg.get("edge_detection"),Edge,Edge.NONE),
            bias=self._resolve_enum(cfg.get("bias"),Bias,Bias.AS_IS),
            drive=self._resolve_enum(cfg.get("drive"),Drive,Drive.PUSH_PULL),   
            active_low=cfg.get("active_low", False), #True from json is True in python
            debounce_period=datetime.timedelta(cfg.get("debounce_period", 0)), #In seconds
            event_clock=self._resolve_enum(cfg.get("event_clock"),Clock,Clock.MONOTONIC),
            output_value=self._resolve_enum(cfg.get("output_value"),Value,Value.INACTIVE),
        )

    def _build_line_config(self):
        line_config: dict[int,gpiod.LineSettings] = {}
        inputs:dict[str,str|int] = self._config.get("inputs",{}).items()

        for name, cfg in inputs:
            pin:int = int(cfg["pin"])
            self._name_map[name] = pin
            line_config[pin]= self._build_line_settings(cfg,Direction.INPUT)
             
        outputs:dict[str,str|int] = self._config.get("outputs",{}).items()
        for name, cfg in outputs:
            pin:int = int(cfg["pin"])
            self._name_map[name] = pin
            line_config[pin]= self._build_line_settings(cfg,Direction.OUTPUT)

        return line_config

    def _resolve_enum(self,value,enum_cls,default):
        if value is None:
            return default
        
        if isinstance(value,str):
            name = value.split(".")[-1] # From "Drive.PUSH_PULL" -> "PUSH_PULL"
            try:
                return enum_cls[name] #Drive["PUSH_PULL"] should resolve to Drive.PUSH_PULL
            except KeyError:
                raise ValueError(f"Enum {enum_cls.__name__} does not have member: {name}")

    def get_name_map(self):
        return self._name_map

    def get_line_config(self):
        return self._line_config

    