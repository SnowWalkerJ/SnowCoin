from redis import Redis
from ..common.settings import CONFIG


__redis = None

def get_redis() -> Redis:
    global __redis
    if __redis is None:
        config = CONFIG['redis']
        __redis = Redis(
            host=config['host'],
            port=config.getint('port'),
            db=config.getint('db'),
        )
    return __redis
