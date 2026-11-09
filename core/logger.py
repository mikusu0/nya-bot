import logging
import os
import logging.handlers

os.makedirs("data", exist_ok=True)
path = "data/bot.log"

def setup_logger():
    logger = logging.getLogger("discord_bot")
    logger.setLevel(logging.DEBUG)
    
    open(path, "w", encoding="utf-8").close()  # truncate

    file_handler = logging.handlers.RotatingFileHandler(
        path,
        maxBytes=32 * 1024 * 1024,  # 32 MB
        backupCount=1,
        encoding="utf-8",
        mode="a"
    )

    console_handler = logging.StreamHandler()

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        "%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(fmt)
    console_handler.setFormatter(fmt)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.propagate = False

    discord_logger = logging.getLogger("discord")
    discord_logger.setLevel(logging.DEBUG)
    discord_logger.addHandler(file_handler)
    # discord_logger.addHandler(console_handler)
    discord_logger.propagate = False  # prevent duplicate messages

    discord_http_logger = logging.getLogger("discord.http")
    discord_http_logger.setLevel(logging.DEBUG)
    discord_http_logger.addHandler(file_handler)
    # discord_http_logger.addHandler(console_handler)
    discord_http_logger.propagate = False

    return logger

logger = setup_logger()
