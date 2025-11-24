import json
import os

import utils


def get_classes():
    cache_path = f"{os.path.dirname(__file__)}/data/caches/".replace("\\", "/")
    caches = os.listdir(cache_path)

    if caches:
        caches = [os.path.join(cache_path, file) for file in caches]
        caches = [file for file in caches if os.path.isfile(file)]

        last_file = max(caches, key=os.path.getctime)
    else:
        return None

    with open(last_file, "r", encoding="utf-8") as f:
        return json.load(f)["classes_list"]

def get_day(klass, day):
    cache_path = f"{os.path.dirname(__file__)}/data/caches/".replace("\\", "/")
    caches = os.listdir(cache_path)

    if caches:
        caches = [os.path.join(cache_path, file) for file in caches]
        caches = [file for file in caches if os.path.isfile(file)]

        last_file = max(caches, key=os.path.getctime)
    else:
        return None

    with open(last_file, "r", encoding="utf-8") as f:
        schedule_data = json.load(f)["schedule"]

        # Проверяем, существует ли класс и день
        if klass not in schedule_data:
            return None
        if day not in schedule_data[klass]:
            return None

        return schedule_data[klass][day]



def get_days():
    cache_path = f"{os.path.dirname(__file__)}/data/caches/".replace("\\", "/")
    caches = os.listdir(cache_path)

    if caches:
        caches = [os.path.join(cache_path, file) for file in caches]
        caches = [file for file in caches if os.path.isfile(file)]

        last_file = max(caches, key=os.path.getctime)
    else:
        return None

    with open(last_file, "r", encoding="utf-8") as f:
        return json.load(f)["days"]

def russian_days():
    st_days = utils.get_settings("info", "days")

    days = []

    for day in get_days():
        days.append(st_days[day])

    return days

def get_ru_day_to_en(day):
    st_days = utils.get_settings("info", "days")

    for en_day, ru_day in st_days.items():
        if ru_day == day:
            return en_day.lower()
    return None


def get_en_day_to_ru(day):
    st_days = utils.get_settings("info", "days")
    normalized_day = day.lower() if isinstance(day, str) else day
    return st_days.get(normalized_day, day)