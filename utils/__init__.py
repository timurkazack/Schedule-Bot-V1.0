import json
import os
from datetime import datetime as dt
from .my_logger import *
from .error_logger import *
from .normalizer_data_from_server import *
from .get_schedule import *
from .sql_use import *
from .api import *

def get_settings(module, setting):

    with open(f"{os.path.dirname(__file__)}\\settings.json", "r", encoding="utf-8") as f:
        if not setting: return json.load(f)[module]
        else: return json.load(f)[module][setting]




def setup():



    dirs = [f"{os.path.dirname(__file__)}\\data",
            f"{os.path.dirname(__file__)}\\data\\logs",
            f"{os.path.dirname(__file__)}\\data\\.temp",
            f"{os.path.dirname(__file__)}\\data\\caches"]

    for dir in dirs:
        try:
            os.makedirs(dir, exist_ok=True)

        except Exception as e:
            logger.error(f"Error Index: {error_logger.search_error_index(e)}")

        finally:
            logger.info(f"{dir} finally exist/created!")
