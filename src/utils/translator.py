from .json_loader import load_json_file
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class Translator:
    def __init__(self,translation_dir: Path):
        self._default_locale = "en"
        self._locale = self._default_locale
        self._translations: dict[str,dict[str,str]] = {}

        for path in Path(translation_dir).rglob("*.json"):
            with open(path) as f:
                data = load_json_file(f)
                #Type checking
                if not isinstance(data,dict):
                    return
                self._translations[path.stem] = data
            logger.info("Loaded existing translations to memory")

    def set_locale(self, locale:str)-> None:
        locale_lc = locale.lower()
        if locale_lc not in self._translations:
            logger.warning("Provided locale does not exist")
            return
        self._locale = locale_lc
        logger.info(f"Locale set to {locale_lc}")

    def translate(self, key:str, **kwargs) -> str:
        text = self._translations.get(self._locale).get(key)

        if text is None:
            return key

        if not kwargs:
            return text

        try:
            return text.format(**kwargs)
        except (KeyError,ValueError): #Will just return plain text with placeholders instead of blowing up whole app
            return text 