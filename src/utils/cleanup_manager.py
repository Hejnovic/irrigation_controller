import signal
import atexit
import sys
import logging
logger = logging.getLogger(__name__)
class CleanupManager:

    def __init__(self):
        self.cleanup_callbacks = []
        self._register_handlers()
    
    def register(self, callback):
        logger.info(f"Registered cleanup callback: {callback.__name__}")
        self.cleanup_callbacks.append(callback)
    
    def _register_handlers(self):
        self._cleaned_up = False
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, cleaning up...")
            self.cleanup_all()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        atexit.register(self.cleanup_all)
    
    def cleanup_all(self):
        if self._cleaned_up:
            return
        self._cleaned_up = True 
        for callback in self.cleanup_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Cleanup error: {e}")