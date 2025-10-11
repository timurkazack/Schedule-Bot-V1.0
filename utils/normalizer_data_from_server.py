import os
import json
import hashlib
from utils import my_logger
from datetime import datetime as dt



def hyphen_r(text):
    # Если все символы это дефис или пробел, то заменить на три дефиса;
    # Если нет, то вернуть text.
    try:
        if text.strip() and all(char == '-' for char in text)\
                or all(char == ' ' for char in text):
            return '---'
        return text


    except Exception as e:
        my_logger.error(e)
        return text



def sort_classes(classes):

    out = {}

    parallel_sort = sorted(classes.keys(), key=int)

    for par in parallel_sort:
        out[par] = classes[par]


    return out



def normalizer_data_from_server(data):
    try:

        my_logger.info("Start schedule normalization")

        # Пути для папки с кешами, к temp файлу и конечному файлу кеша
        cache_path = f"{os.path.dirname(__file__)}/data/caches/".replace("\\", "/")
        temp_file_name = f"{os.path.dirname(__file__)}/data/.temp/{dt.now().strftime('%Y-%m-%d_%H-%M-%S')}.json".replace("\\", "/")
        out_file_name = f"{cache_path}{dt.now().strftime('%Y-%m-%d_%H-%M')}.json".replace("\\", "/")

        # Здесь нормализация расписания из str строки данных в json
        # через write который убирает "", затем уже открываем это как json
        with open(temp_file_name, "w", encoding="utf-8") as f:
            f.write(data)

        with open(temp_file_name, "r", encoding="utf-8") as f:
            json_data = json.load(f)["d"]["b"]["d"]["records"]

        # Удаляем temp файл
        os.remove(temp_file_name)

        # Структура кеша:
        # "time"          > Время получения и обработки кеша
        # "md5"           > md5 сумма расписания (нужно для проверки одинаковости расписания)
        # "classes_count" > Кол-во классов
        # "classes_list"  > Все классы отсортированные по (параллель1: [класс1, класс2], параллель2)
        # "days"          > Дни используемые в этом расписании
        # "schedule"      > Само расписание
        normal_json = {}
        normal_json["time"] = str(dt.now())
        normal_json["md5"] = hashlib.md5(data.encode("utf-8")).hexdigest()
        normal_json["classes_count"] = len(json_data.keys())
        normal_json["classes_list"] = {}
        normal_json["days"] = []
        normal_json["schedule"] = {}


        # Проверка на одинаковость нового и старого расписания, если нет то сохраняем, если да то дроп
        caches = os.listdir(cache_path)
        if caches:
            caches = [os.path.join(cache_path, file) for file in caches]
            caches = [file for file in caches if os.path.isfile(file)]

            last_file = max(caches, key=os.path.getctime)

            with open(last_file, "r", encoding="utf-8") as f:
                md5 = json.load(f)["md5"]

            if md5 == normal_json["md5"]:
                my_logger.info("Schedule is the same. Cancel.")
                return None


        # Цикл по классам
        for cl_cur in list(json_data.values()):

            # Проверка на наличие параллели соответствующей текущему классу
            # Если параллели нет, то создаём с текущим классом
            # Если есть то просто сохраняем текущий класс в параллель
            if cl_cur["grade"][:-1] not in normal_json["classes_list"]:
                normal_json["classes_list"][cl_cur["grade"][:-1]] = [cl_cur["grade"]]
                normal_json["schedule"][cl_cur["grade"]] = {}

            else:
                normal_json["classes_list"][cl_cur["grade"][:-1]].append(cl_cur["grade"])
                normal_json["schedule"][cl_cur["grade"]] = {}


            # Цикл по предметам в текущем классе
            for cl_sub in cl_cur["subjects"].values():

                # Проверка на наличие дня в "days" (см. в структуре кеша)
                if cl_sub["subjectDay"].lower() not in normal_json["days"]:
                    normal_json["days"].append(cl_sub["subjectDay"].lower())

                # Проверка на наличие дня в полу обработанном расписании
                if cl_sub["subjectDay"].lower() not in normal_json["schedule"][cl_cur["grade"]]:
                    normal_json["schedule"][cl_cur["grade"]][cl_sub["subjectDay"].lower()] = {}

                # Сохранение в кеше структуры: Предмет: Кабинет
                normal_json['schedule'][cl_cur['grade']][cl_sub['subjectDay'].lower()][
                    (f"{len(normal_json['schedule'][cl_cur['grade']][cl_sub['subjectDay'].lower()])+1}. "
                     f"{hyphen_r(cl_sub['lesson'])}")] = hyphen_r(cl_sub['room'])




        normal_json["classes_list"] = sort_classes(normal_json["classes_list"])

        # Сохранение
        with open(out_file_name, "w", encoding="utf-8") as f:
            json.dump(normal_json, f, ensure_ascii=False, indent=2)
            my_logger.info("Schedule normalized")
            return out_file_name


    except Exception as e:
        my_logger.error(e)