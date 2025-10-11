import json
import os

ERROR_LIST_PATH = f"{os.path.dirname(__file__)}/data/error_list.json".replace("\\", "/")

def add_error_to_list(error):
    error = str(error)
    with open(ERROR_LIST_PATH, "r", encoding="utf-8") as f:
        errors = json.load(f)

    num = str(len(errors.keys()))

    errors[error] = num

    with open(ERROR_LIST_PATH, "w", encoding="utf-8") as f:
        json.dump(errors, f, indent=2, ensure_ascii=False)
    return num

def search_error_index(error):

    with open(ERROR_LIST_PATH, "r", encoding="utf-8") as f:
        errors = json.load(f)

    if error in errors.keys():
        return errors[error]
    else:
        return add_error_to_list(error)