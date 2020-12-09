from time import sleep
import configparser
from .base import Scraper
from .db_handler import Database
from .log_handler import logger

CONFIG_PATH = "data/config.ini"

def initialize():
    # Setup Logger
    log = logger(__name__)

    # Initialize Config
    config = __init_config()

    # Initialize Database
    db_type = config.get('Database', 'type')
    db_uri = config.get('Database', 'uri')

    db = Database(db_type, dbname=db_uri)


    # Initialize Scraper 
    scraper = Scraper(config, db)    

    return scraper
    

def __init_config():
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)
    
    return config
