import logging
import logging.config
from pathlib import Path
def load_logging_config_yml(logger: logging.Logger):
    config_file: str = "placeholder.yml"
    import sys
    if '--log-config' in sys.argv:
        idx = sys.argv.index('--log-config')
        if idx + 1 < len(sys.argv):
            config_file = sys.argv[idx+1]

    if Path(config_file).exists():
        import yaml
        with open(config_file, 'r',encoding='utf-8') as f:
            config = yaml.safe_load(f)
            if config:
                logging.config.dictConfig(config)
                logger.info(f"Logging config loaded from {config_file}")
                return

    logging.basicConfig(level=logging.INFO)
    logger.warning(f"Logging config file: {config_file} not found - using basic config")