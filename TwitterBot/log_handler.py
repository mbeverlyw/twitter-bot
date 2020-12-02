import logging
from logging.handlers import RotatingFileHandler

def logger(name):
    # Set up logfile and message logging.
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Create the rotating file handler. Limit the size to 1000000Bytes ~ 1MB .
    handler = RotatingFileHandler(
        "bot.log", 
        mode='a+', maxBytes=1000000, backupCount=1, 
        encoding='utf-8', delay=0)
    handler.setLevel(logging.DEBUG)

    # Create a formatter.
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s {%(pathname)s:%(lineno)d} - %(levelname)s - %(message)s')

    # Add handler and formatter.
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
