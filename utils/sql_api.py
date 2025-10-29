import sqlite3 as sq
import os
from utils import my_logger
from datetime import datetime as dt

users_db = f"{os.path.dirname(__file__)}/data/users/users_db.db".replace("\\", "/")

_connect = None

def setup():
    global _connect
    my_logger.info("Stated connect to db")
    _connect = sq.connect(users_db)

    cur_us = _connect.cursor()

    cur_us.execute("""CREATE TABLE IF NOT EXISTS users(
        tg_id INTEGER PRIMARY KEY,
        tg_first_name TEXT,
        tg_last_name TEXT,
        tg_user_name TEXT,
        worked_class TEXT,
        first_visit TEXT,
        last_visit TEXT,
        is_admin INTEGER,
        is_baned INTEGER,
        ban_time TEXT,
        ban_time_left TEXT,
        ban_reason TEXT,
        donated_money REAL)
    """)

    cur_us.execute("""CREATE TABLE IF NOT EXISTS newsletter(
    chat_id INTEGER PRIMARY KEY,
    time TEXT,
    class TEXT)""")

    _connect.commit()
    my_logger.info("Users db created/exist")


def update_user_data(message_from_user, klass=None,
                     is_admin=None, is_baned=None,
                     ban_time_left=None, # minute
                     ban_reason=None,
                     donated_money=None):
    
    tg_id = int(message_from_user.chat.id)
    tg_first_name = str(message_from_user.chat.first_name)
    tg_last_name = str(message_from_user.chat.last_name)
    tg_user_name = str(message_from_user.chat.username)


    # Получаем текущее время в формате строки
    current_time = dt.now().strftime("%Y-%m-%d %H:%M:%S")


    if is_baned==1: ban_time = current_time


    cur_us = _connect.cursor()

    # 1. Проверяем существует ли пользователь
    cur_us.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,))
    user_data = cur_us.fetchone()

    if not user_data:
        # 2. Если пользователь новый - вставляем новую запись
        cur_us.execute("""
            INSERT INTO users (
                tg_id, tg_first_name, tg_last_name, tg_user_name,
                worked_class, first_visit, last_visit,
                is_admin, is_baned, ban_time, ban_time_left, ban_reason, donated_money
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            tg_id, tg_first_name, tg_last_name, tg_user_name,
            klass, current_time, current_time,
            is_admin or 0, is_baned or 0,
            ban_time, ban_time_left, ban_reason,
            donated_money or 0.0
        ))
    else:
        # 3. Если пользователь существует - обновляем данные
        cur_us.execute("""
            UPDATE users SET
                tg_first_name = ?,
                tg_last_name = ?,
                tg_user_name = ?,
                worked_class = COALESCE(?, worked_class),
                last_visit = ?,
                is_admin = COALESCE(?, is_admin),
                is_baned = COALESCE(?, is_baned),
                ban_time = COALESCE(?, ban_time),
                ban_time_left = COALESCE(?, ban_time_left),
                ban_reason = COALESCE(?, ban_reason),
                donated_money = COALESCE(?, donated_money)
            WHERE tg_id = ?
        """, (
            tg_first_name, tg_last_name, tg_user_name,
            klass, current_time,
            is_admin, is_baned, ban_time, ban_time_left, ban_reason, donated_money,
            tg_id
        ))

    _connect.commit()


def get_user_data(message):

    tg_id = int(message.from_user.id)

    try:
        with _connect as conn_us:
            cur_us = conn_us.cursor()

            cur_us.execute("""
                SELECT * FROM users WHERE tg_id = ?
            """, (tg_id,))

            user_data = cur_us.fetchone()

            if user_data:
                # Более универсальный способ для любого количества столбцов
                columns = [description[0] for description in cur_us.description]
                return dict(zip(columns, user_data))
            else:
                return None

    except sq.Error as e:
        my_logger.error(e)
        return None


def get_user_count():
    cur_us = _connect.cursor()

    cur_us.execute("SELECT COUNT(*) FROM users;")
    result = cur_us.fetchone()
    count = result[0]

    _connect.commit()

    return count


def get_all_sql_users():
    cur_us = _connect.cursor()

    cur_us.execute("SELECT * FROM users;")
    result = cur_us.fetchall()

    _connect.commit()

    file = f"{os.path.dirname(__file__)}/data/.temp/all.txt".replace('\\', '/')

    with open(file, "w", encoding="utf-8") as f:
        text = ""

        for user in result:

            line = ""
            for obj in user[:7]:
                line += str(obj) + "\t"
            text += line + "\n"
        f.write(text)

    return file


def get_all_users_id():
    cur_us = _connect.cursor()

    cur_us.execute("SELECT tg_id FROM users;")
    result = cur_us.fetchall()
    result = [item[0] for item in result]


    _connect.commit()

    return result
    #return [7804831715]


def add_time(chat_id, time):
    #cur_us = _connect.cursor()

    #cur_us.execute("""
    #INSERT INTO newsletter (
    #chat_id, time) VALUES (?, ?)""", (chat_id, time))

    #_connect.commit()
    pass

setup()