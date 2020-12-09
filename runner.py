import TwitterBot
from time import sleep

if __name__ == "__main__":

    # Runs twitter bot
    bot = TwitterBot.initialize()


    '''
    Continuously go to Twitter notifications and process
        notifications directed to bot appropriately.
    '''
    while 1:
        # Goto Notifications and process mentions.
        bot.goto_notifications(process_mentions=True)
        sleep(12)
