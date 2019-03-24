import discord
import logging
import colorlog


def setup_custom_logger(name):
    handler = logging.StreamHandler()
    handler.setFormatter(colorlog.LevelFormatter(
        fmt={
            'DEBUG': '{log_color}[{levelname}:{module}] {message}',
            'INFO': '{log_color}{message}',
            'WARNING': '{log_color}{levelname}: {message}',
            'ERROR': '{log_color}[{levelname}:{module}] {message}',
            'CRITICAL': '{log_color}[{levelname}:{module}] {message}',
        },
        datefmt=None,
        reset=True,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'white',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red,bg_white',
        },
        secondary_log_colors={},
        style='{'))

    logger = logging.getLogger(name)
    
    # Change to INFO
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    return logger

def setup_discord_logger(path):
    logger = logging.getLogger("discord")
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(filename=path.format("discord.log"), encoding="utf-8", mode="w")
    handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
    logger.addHandler(handler)

def set_logger_level(logger, level):
    dict = {"CRITICAL": 50, "ERROR": 40, "WARNING": 30, "INFO": 20, "DEBUG": 10, "NOTSET": 0}
    logger.setLevel(dict.get(level, 20))
    print("Set logger level to: {}".format(level))
