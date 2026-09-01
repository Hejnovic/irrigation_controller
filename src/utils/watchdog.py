from watchfiles import awatch, Change
import logging
from pathlib import Path
from collections.abc import Callable

logger = logging.getLogger(__name__)

class ConfigWatcher:
    def __init__(self,config_dir: str | Path = "config"): ## ../configs but it is nested - eg ../configs/irigation_configs -> configs for irrigation controller
        self._config_dir = Path(config_dir).resolve()
        self._handlers: dict[Path, Callable[[Path], None]] = {}
        
    def register_handler(self, filename: str, handler: Callable[[Path], None]):
        for file_path in self._config_dir.rglob(filename):
            self._handlers[file_path] = handler
            logger.debug(f"Registered handler for {file_path}")

    async def start(self):
        logger.info(f"Preloading existing config files on startup")
        ## Can preload existing config on startup of program if files exist
        for file_path, handler in self._handlers.items():
            if Path(file_path).is_file():
                logger.info(f"Preloading config from {file_path} on startup")
                handler(file_path)
        logger.info(f"Starting config watcher on {self._config_dir}")
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
    