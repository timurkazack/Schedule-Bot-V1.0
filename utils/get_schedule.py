import json
import os

def get_classes():
    cache_path = f"{os.path.dirname(__file__)}\\data\\caches\\"
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
    cache_path = f"{os.path.dirname(__file__)}\\data\\caches\\"
    caches = os.listdir(cache_path)

    if caches:
        caches = [os.path.join(cache_path, file) for file in caches]
        caches = [file for file in caches if os.path.isfile(file)]

        last_file = max(caches, key=os.path.getctime)
    else:
        return None

    with open(last_file, "r", encoding="utf-8") as f:
        return json.load(f)["schedule"][klass][day]

def get_days():
    cache_path = f"{os.path.dirname(__file__)}\\data\\caches\\"
    caches = os.listdir(cache_path)

    if caches:
        caches = [os.path.join(cache_path, file) for file in caches]
        caches = [file for file in caches if os.path.isfile(file)]

        last_file = max(caches, key=os.path.getctime)
    else:
        return None

    with open(last_file, "r", encoding="utf-8") as f:
        return json.load(f)["days"]