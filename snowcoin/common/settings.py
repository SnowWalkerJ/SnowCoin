import os
from configparser import ConfigParser


WORKSPACE = os.path.expanduser('~/.snowcoin/')
CONFIG_PATH = os.path.join(WORKSPACE, 'config.ini')


def create_config():
    os.mkdir(WORKSPACE)
    config = ConfigParser()
    config['mongodb'] = {
        'host': 'localhost',
        'port': 27017,
        'database': 'snowcoin',
        'collection': 'snowcoin',
    }
    config['redis'] = {
        'host': 'localhost',
        'port': 6379,
        'db': 0,
    }
    with open(CONFIG_PATH, "w") as f:
        config.write(f)
    return config


def get_config():
    if not os.path.exists(CONFIG_PATH):
        config = create_config()
    else:
        config = ConfigParser()
        config.read(CONFIG_PATH)
    return config


CONFIG = get_config()
