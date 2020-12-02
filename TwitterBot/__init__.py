from time import sleep
import configparser
from .base import Scraper
from .db_handler import Database

CONFIG_PATH = "data/config.ini"

def run():
    # Initialize Config
    config = __init_config()

    # Initialize Database
    db = Database('sqlite', dbname='data/bot.db')
    db.create_db_tables()

    # Initialize Scraper 
    scraper = Scraper(config, db)

    '''
    Continuously go to Twitter notifications and process
        notifications directed to bot appropriately.
    '''
    while 1:
        scraper.goto_mentions(process_mentions=True)
        sleep(12)

def __init_config():
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)

    return config



if __name__ == "__main__":
    main()

