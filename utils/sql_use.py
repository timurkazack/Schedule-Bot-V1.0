import sqlite3 as sq
import os
from telebot import *
from utils import my_logger
from datetime import datetime as dt

users_db = f"{os.path.dirname(__file__)}\\data\\users\\users_db.db"

def setup():
    my_logger.info("Stated connect to db")
    conn_us = sq.connect(users_db)

    cur_us = conn_us.cursor()

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
        donated_money REAL)
    """)


    conn_us.commit()
    conn_us.close()
    my_logger.info("Users db created/exist")


def update_user_data(message_from_user, klass=None,
                     is_admin=None, is_baned=None,
                     ban_time=None, ban_time_left=None,
                     donated_money=None):
    tg_id = int(message_from_user.from_user.id)
    tg_first_name = str(message_from_user.from_user.first_name)
    tg_last_name = str(message_from_user.from_user.last_name)
    tg_user_name = str(message_from_user.from_user.username)

    # Получаем текущее время в формате строки
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn_us = sq.connect(users_db)
    cur_us = conn_us.cursor()

    # 1. Проверяем существует ли пользователь
    cur_us.execute("SELECT tg_id FROM users WHERE tg_id = ?", (tg_id,))
    user_exists = cur_us.fetchone() is not None

    if not user_exists:
        # 2. Если пользователь новый - вставляем новую запись
        cur_us.execute("""
            INSERT INTO users (
                tg_id, tg_first_name, tg_last_name, tg_user_name,
                worked_class, first_visit, last_visit,
                is_admin, is_baned, ban_time, ban_time_left, donated_money
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            tg_id, tg_first_name, tg_last_name, tg_user_name,
            klass, current_time, current_time,  # first_visit и last_visit = текущее время
            is_admin or 0, is_baned or 0,  # значения по умолчанию если None
            ban_time, ban_time_left,
            donated_money or 0.0  # значение по умолчанию если None
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
                donated_money = COALESCE(?, donated_money)
            WHERE tg_id = ?
        """, (
            tg_first_name, tg_last_name, tg_user_name,
            klass, current_time,  # обновляем last_visit
            is_admin, is_baned, ban_time, ban_time_left, donated_money,
            tg_id
        ))

    conn_us.commit()
    conn_us.close()


def get_user_data(message):

    tg_id = int(message.from_user.id)

    try:
        with sq.connect(users_db) as conn_us:
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
        my_logger.error(e, "sql")
        return None

def test():
    pass

setup()