from datetime import datetime as dt
import logging
import os
from utils import error_logger


logger = None

def setup():
    global logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Формат логирования
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Обработчик для консоли
    console = logging.StreamHandler()
    console.setFormatter(formatter)

    # Обработчик для файла
    log_filename = f"{dt.now().strftime('%Y-%m-%d')}.log"
    file_handler = logging.FileHandler(
        filename=os.path.join(os.path.dirname(__file__) + "\\data\\logs", log_filename),
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    # Добавляем обработчики
    logger.handlers = [console, file_handler]




def info(text):
    logger.info(text)

def debug(text):
    print(text)

def warning(text):
    logger.warning(text)

def error(text):
    logger.exception(f"Error Index: {error_logger.search_error_index(text)}")

def fatal(text):
    logger.fatal(text)


setup()

info("###############################")
info("TEST INFO LOGGING FINALLY")
warning("TEST WARNING LOGGING FINALLY")
error("TEST ERROR LOGGING FINALLY")
fatal("TEST FATAL LOGGING FINALLY")
info("LOGGER STARTED")
info("###############################")
