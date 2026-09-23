from typing import Protocol

class GPIOBuilder(Protocol):
    def __init__(self,config):
        ...

    def _build_line_settings(self,cfg,direction):
        ...

    def _build_line_config(self):
        ...

    def get_name_map(self):
        ...

    def get_line_config(self):
        ...