from pymongo import MongoClient
from pymongo.database import Database
from ..common.settings import CONFIG


__mongo = None


def get_mongo() -> Database:
    global __mongo
    if __mongo is None:
        config = CONFIG['mongodb']
        client = MongoClient(host=config['host'], port=config.getint('port'))
        __mongo = client[config['database']]
    return __mongo
