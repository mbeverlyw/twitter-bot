from time import sleep
import configparser
from .base import Scraper
from .db_handler import Database
from .log_handler import logger

CONFIG_PATH = "data/config.ini"

def run():
    # Setup Logger
    log = logger(__name__)

    # Initialize Config
    log.info('Initializing Configuration')

    config = __init_config()

    log.info('Configuration Set')

    # Initialize Database
    log.info('Initializing DB')

    db = Database('sqlite', dbname='data/bot.db')
    db.create_db_tables()

    log.info('DB Set')

    # Initialize Scraper 
    log.info('Initializing Scraper')
    scraper = Scraper(config, db)
    log.info('Scraper Set')

    '''
    Continuously go to Twitter notifications and process
        notifications directed to bot appropriately.
    '''
    log.info('Proceeding to bot actions..')

    while 1:
        scraper.goto_mentions(process_mentions=True)
        sleep(12)
    

def __init_config():
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)

    return config



if __name__ == "__main__":
    main()

