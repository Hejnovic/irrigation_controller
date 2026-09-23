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
            edge_detection=cfg.get("edge_detection", Edge.NONE),
            bias=cfg.get("bias", Bias.AS_IS),
            drive=cfg.get("drive", Drive.PUSH_PULL),   
            active_low=cfg.get("active_low", False),
            debounce_period=cfg.get("debounce_period", datetime.timedelta(0)),
            event_clock=cfg.get("event_clock", Clock.MONOTONIC),
            output_value=cfg.get("output_value", Value.INACTIVE),
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

    def get_name_map(self):
        return self._name_map

    def get_line_config(self):
        return self._line_config

    