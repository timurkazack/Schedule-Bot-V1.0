import os
import json
import hashlib
from . import my_logger
from .get_schedule import get_days
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



def check_redacted_data(new_cache, last_cache):
    redacted_data = {}
    
    if not last_cache:
        return None

    def get_all_classes(cache):
        klasses = []
        for key in cache["classes_list"].keys(): 
            for content in cache["classes_list"][key]:
                klasses.append(content)
        return set(klasses)

    # Получаем все классы из обоих кешей
    new_classes = get_all_classes(new_cache)
    last_classes = get_all_classes(last_cache)
    
    # Объединяем все классы (на случай добавления/удаления классов)
    all_classes = new_classes.union(last_classes)
    
    # Получаем все дни из обоих кешей
    all_days = set(new_cache["days"]).union(set(last_cache["days"]))
    
    # Проверяем изменения для каждого класса и каждого дня
    for class_name in all_classes:
        class_changes = {"subjects": set(), "rooms": set()}
        
        new_class_schedule = new_cache["schedule"].get(class_name, {})
        last_class_schedule = last_cache["schedule"].get(class_name, {})

        # Если класс добавлен или удален - считаем, что изменились предметы по всем дням
        if not new_class_schedule or not last_class_schedule:
            class_changes["subjects"].update(all_days)
        else:
            # Проверяем изменения по дням
            for day in all_days:
                new_day_schedule = new_class_schedule.get(day)
                last_day_schedule = last_class_schedule.get(day)

                # Если день добавлен или удален для этого класса
                if (new_day_schedule is None) != (last_day_schedule is None):
                    class_changes["subjects"].add(day)
                    continue

                if new_day_schedule is None and last_day_schedule is None:
                    continue

                new_day_schedule = new_day_schedule or {}
                last_day_schedule = last_day_schedule or {}

                new_lessons = set(new_day_schedule.keys())
                last_lessons = set(last_day_schedule.keys())

                # Изменение предметов (отличаются ключи уроков)
                if new_lessons != last_lessons:
                    class_changes["subjects"].add(day)

                # Изменение кабинетов (ключи совпадают, но значения разные)
                for lesson in new_lessons.intersection(last_lessons):
                    if new_day_schedule[lesson] != last_day_schedule[lesson]:
                        class_changes["rooms"].add(day)

        cleaned_changes = {
            key: sorted(value) for key, value in class_changes.items() if value
        }

        if cleaned_changes:
            redacted_data[class_name] = cleaned_changes
    
    # Возвращаем None если изменений нет, иначе словарь с изменениями
    return redacted_data if redacted_data else None


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
        last_file = None
        last_cache_data = None

        if caches:
            caches = [os.path.join(cache_path, file) for file in caches]
            caches = [file for file in caches if os.path.isfile(file)]

            last_file = max(caches, key=os.path.getctime)

            with open(last_file, "r", encoding="utf-8") as f:
                last_cache_data = json.load(f)
                md5 = last_cache_data["md5"]

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

        redacted_data = check_redacted_data(normal_json, last_cache_data)

        # Сохранение
        with open(out_file_name, "w", encoding="utf-8") as f:
            json.dump(normal_json, f, ensure_ascii=False, indent=2)
            my_logger.info("Schedule normalized")
            return out_file_name, redacted_data


    except Exception as e:
        my_logger.error(e)