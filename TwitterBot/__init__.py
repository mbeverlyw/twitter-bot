from .base import Scraper
from .db_handler import Database
from time import sleep


def main():
    # Initialize Database
    db = Database('sqlite', dbname='data/bot.db')
    db.create_db_tables()

    # Establish twitter login credentials
    handle = input("Twitter Handle: @")
    password = input("Enter Password:")

    # Initialize Scraper 
    scraper = Scraper(handle, db)

    # Test Login for Twitter
    scraper.login(password)

    '''
    Continuously go to Twitter notifications and process
        notifications directed to bot appropriately.
    '''
    while 1:
        scraper.goto_mentions(process_mentions=True)
        sleep(12)



if __name__ == "__main__":
    main()

