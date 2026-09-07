from watchfiles import awatch, Change
import logging
from pathlib import Path
from collections.abc import Callable

logger = logging.getLogger(__name__)

class Watchdog:
    def __init__(self,config_dir: str | Path = "config"): ## ../configs but it is nested - eg ../configs/irigation_configs -> configs for irrigation controller
        self._config_dir = Path(config_dir).resolve()
        self._handlers: dict[Path, Callable[[Path], None]] = {}
        self._config_files: dict[str, Path] = {file.name:file for file in self._config_dir.rglob("*") if file.is_file()}
        self._tracking_dict: dict[str,Callable[[Path],None]] = {} #All handlers that were added but file didn't exist yet
        
    def register_handler(self, file_name: str, handler: Callable[[Path], None]):
        if file_name not in self._config_files.keys(): #If file doesn't exist yet should add to future callbacks and then check when new file is added if the name is correct
            self._tracking_dict[file_name] = handler
            logger.warning(f"File {file_name} not found in config files, added to tracking dict")
            return
        if not callable(handler):
            logger.warning(f"Handler can not be non-callable: {handler}")
            return
        handler_path = self._config_files[file_name]
        self._handlers[handler_path] =handler
        logger.info(f"Handler: {handler.__name__} is attached to file: {file_name}")

    def preload_configs(self):
        logger.info(f"Preloading existing config files on startup")
        ## Can preload existing config on startup of program if files exist
        for file_path, handler in self._handlers.items():
            if Path(file_path).is_file():
                logger.info(f"Preloading config from {file_path} on startup")
                handler(file_path)
        logger.info(f"Starting config watcher on {self._config_dir}")

    async def watch(self):
        async for changes in awatch(self._config_dir,debounce=500,watch_filter = lambda _,p: Path(p).is_file(), recursive=True):
            for change, file_path in changes:
                file_path = Path(file_path)
                if file_path.name.startswith('.') or file_path.name.endswith('~') or '.tmp' in file_path.name:
                    continue
                if change is Change.deleted:
                    #Should remove callback when file is deleted
                    handler = self._handlers.get(file_path)
                    if handler:
                        self._handlers.pop(file_path)
                        #But should I add it to tracking dict so the same handler will automatically be assigned to the same file?
                        #When it is like this after removing file it is needed to restart program to track it again - there is no way yet to add callbacks from any GUI
                        logger.info(f"Removed handler for existing file: {file_path.name}")
                    continue
                if change is Change.added: #Though it guarantees new file but atomic swap is registered as .added tmp.replace(file)
                    file_name = file_path.name
                    self._config_files[file_name] = file_path
                    #Check in tracking_dict if there is handler waiting for this file
                    if file_name in self._tracking_dict.keys():
                        self._handlers[file_path] = self._tracking_dict[file_name]
                        self._tracking_dict.pop(file_name)
                        logger.info(f"Added waiting callback to file: {file_name}")
                #Code here handles .modified
                handler = self._handlers.get(file_path)
                if handler:
                    logger.info(f"Detected change {str(change.name)} in {file_path}, invoking handler")
                    handler(file_path)
                else:
                    logger.info(f"No handler registered for {file_path}")