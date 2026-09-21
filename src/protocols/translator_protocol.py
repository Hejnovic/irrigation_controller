from typing import Protocol

class TranslatorProtocol(Protocol):
    def set_locale(self, locale)-> None:
        ...

    def translate(self, key:str, **kwargs) -> str:
        ...