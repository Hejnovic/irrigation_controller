from .json_loader import load_json_file
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class Translator:
    def __init__(self,translation_dir: Path):
        self._default_locale = {
            "device_idle": "Device is idle",
            "pump_running_manual": "Pump is running in manual mode",
            "section_running_manual": "Manually running section number {section}",
            "section_running_auto": "Irrigating section {section}",
            "error": "Error has occured - for more infomration check logs",
            "time_interval_auto": "Change of section at {time_end} - interval: {time_interval} min",
            "daily_schedule": "Start: {start_time}, sections: {sections}",
            "daily_schedule_empty": "Day without irrigation"
            }
        self._locale = None
        self._translations: dict[str,dict[str,str]] = {}

        for path in Path(translation_dir).rglob("*.json"):
            with open(path) as f:
                data = load_json_file(path)
                #Type checking
                if not isinstance(data,dict):
                    return
                self._translations[path.stem] = data
            logger.info(f"Loaded existing translations to memory: {self._translations.keys()}")

    def set_locale(self, locale:str)-> None:
        locale_lc = locale.lower()
        if locale_lc not in self._translations:
            logger.warning("Provided locale does not exist")
            return
        self._locale = locale_lc
        logger.info(f"Locale set to {locale_lc}")

    def translate(self, key:str, **kwargs) -> str:
        text = self._translations.get(self._locale).get(key) or self._default_locale.get(key) #Use selected locale - if does not exist will use default one

        if text is None:
            logger.warning(f"Missing translation for key: {key}")
            return key

        if not kwargs:
            return text

        try:
            return text.format(**kwargs)
        except (KeyError,ValueError): #Will just return plain text with placeholders instead of blowing up whole app
            return text 