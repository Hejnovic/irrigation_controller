from watchfiles import awatch, Change
import logging
from pathlib import Path
from collections.abc import Callable

logger = logging.getLogger(__name__)

class ConfigWatcher:
    def __init__(self,config_dir: str | Path = "config"): ## ../configs but it is nested - eg ../configs/irigation_configs -> configs for irrigation controller
        self._config_dir = Path(config_dir).resolve()
        self._handlers: dict[Path, Callable[[Path], None]] = {}
        self._config_files: dict[str, Path] = {file.name:file for file in self._config_dir.rglob("*") if file.is_file()}
        
    def register_handler(self, filename: str, handler: Callable[[Path], None]):
        if filename not in self._config_files.keys():
            logger.error(f"File {filename} not found in config files")
            return
        handler_path = self._config_files[filename]
        self._handlers[handler_path] =handler
        logger.info(f"Handler: {handler.__name__} is attached to file: {filename}")

    async def start(self):
        logger.info(f"Preloading existing config files on startup")
        ## Can preload existing config on startup of program if files exist
        for file_path, handler in self._handlers.items():
            if Path(file_path).is_file():
                logger.info(f"Preloading config from {file_path} on startup")
                handler(file_path)
        logger.info(f"Starting config watcher on {self._config_dir}")
        await self._watch()


    async def _watch(self):
        async for changes in awatch(self._config_dir,debounce=500,watch_filter = lambda _,p: Path(p).is_file(), recursive=True):
            for change, file_path in changes:
                file_path = Path(file_path)
                if file_path.name.startswith('.') or file_path.name.endswith('~') or '.tmp' in file_path.name:
                    continue
                if change in (Change.added, Change.modified):
                    handler = self._handlers.get(file_path)
                    if handler:
                        logger.info(f"Detected change in {file_path}, invoking handler")
                        handler(file_path)
                    else:
                        logger.info(f"No handler registered for {file_path}")