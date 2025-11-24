from utils import logger as lg
from utils import normalizer_data_from_server
from utils import get_schedule as gs
import utils
import time
import textwrap as tw
import threading as thread
import websocket as wsocket


is_update = False
latest_cache = None
updates = True
trigger_func = None

lg.info("WS Parser started!")


def get_data_from_server():
    global is_update
    global latest_cache
    try:

        is_update = True

        lg.info("Getting data from server")
        ws = wsocket.WebSocket()

        lg.debug("Connect to URL")
        ws.connect(url=utils.get_settings("websocket_parser", "url"))

        data_str_line = ""

        lg.debug(f"Getting message from server: {ws.recv()}")

        lg.debug(f"Sending message to server: {utils.get_settings('websocket_parser', 'messages')[0]}")
        ws.send(utils.get_settings("websocket_parser", "messages")[0])

        lg.debug(f"Sending message to server: {utils.get_settings('websocket_parser', 'messages')[1]}")
        ws.send(utils.get_settings("websocket_parser", "messages")[1])

        lg.debug(f"Getting message from server: {ws.recv()}")

        data_message_count = int(ws.recv())
        lg.debug(f"Getting message from server: {data_message_count}")

        for message_num in range(data_message_count):
            now_data_line = ws.recv()
            data_str_line += now_data_line
            lg.debug(f"Getting message from server: {now_data_line}")

        lg.debug("Connection close")
        ws.close()

        lg.debug(f"Out data: {data_str_line}")

        out_from_func, redacted_chedules = normalizer_data_from_server(data_str_line)

        if out_from_func:
            latest_cache = out_from_func
        
        if redacted_chedules:
            trigger_func(redacted_chedules)

    except Exception as e:
        lg.error(e)
        is_update = False
    finally:
        lg.info("Data received from server")
        is_update = False


def auto_update():
    if updates:
        get_data_from_server()
        time.sleep(utils.get_settings("websocket_parser", "update_timeout_m") * 60)
    else:
        time.sleep(15)

    auto_update()



def norm_schedule(klass, day):

    """Расп. для 7К на Вторник:
    №. Кабинет | Предмет
    1. 107В    | Геометрия
    2. 306Ж    | ВПР по английскомуe языку
    3. 306А    | История
    4. 308Г    | Русский язык
    5. 201В    | География
    6. с/зал   | Физкультура
    7. с/зал   | Физкультура"""


    schedule = gs.get_day(klass, day)
    if schedule is None:
        return f"❌ Расписание для класса {klass} на {day} не найдено"

    days_tr = utils.get_settings("info", "days")

    special_ch = "<code>"
    special_ch1 = "</code>"
    label = f"Расп. для {klass} на {days_tr[day]}:\n"
    label += "№. Кабинет  | Предмет\n"

    fill = ""

    for lesson in schedule.keys():
        lesson_num = lesson[:2]

        room = schedule[lesson].split("/") if len(schedule[lesson]) > 8 else schedule[lesson]
        if type(room) == list:
            for x in range(len(room)):
                room[x] = room[x] + (" "*(8 - len(room[x])))
        else: room = room + (" "*(8 - len(room)))

        lesson_list = tw.fill(lesson[3:], width=16).split("\n")


        if type(room) != list and len(lesson_list) == 1:
            fill += f"{lesson_num} {room} | {lesson_list[0]}\n"

        elif type(room) == list and len(lesson_list) == 1:
            fill += f"{lesson_num} {room[0]} | {lesson_list[0]}\n"

            for i in range(1,
                           len(room)):
                fill += f"|  {room[i]} |\n"


        elif type(room) == list and len(lesson_list) != 1:

            fill += f"{lesson_num} {room[0]} | {lesson_list[0]}\n"

            # Начинаем со ВТОРОЙ строки (i=1), так как первая уже выведена

            for i in range(1, max(len(room), len(lesson_list))):

                fill += "|  "  # Начинаем новую строку таблицы

                # Выводим кабинет, если он есть на этой строке

                if i < len(room):

                    fill += f"{room[i]} | "

                else:

                    fill += f"{' ' * 8} | "

                # Выводим часть названия урока, если она есть на этой строке

                if i < len(lesson_list):

                    fill += f"{lesson_list[i]}\n"

                else:

                    fill += "\n"

        elif type(room) == str and len(lesson_list) != 1:
            fill += f"{lesson_num} {room} | {lesson_list[0]}\n"

            for i in range(1, len(lesson_list)):
                fill += f"|  {' ' * 8} | {lesson_list[i]}\n"


    return special_ch + label + fill + special_ch1


def run_auto_update():
    th = thread.Thread(target=auto_update, daemon=True)
    if not th.is_alive():
        th.start()

#print(norm_schedule("7К", "monday"))
#get_data_from_server()