import sqlite3 as sq
import os
from utils import my_logger

admin_db = f"{os.path.dirname(__file__)}\\data\\users\\admins_db.db"
users_db = f"{os.path.dirname(__file__)}\\data\\users\\users_db.db"

def setup():
    my_logger.info("Stated connect to db`s")
    conn_ad = sq.connect(admin_db)
    conn_us = sq.connect(users_db)

    cur_ad = conn_ad.cursor()
    cur_us = conn_us.cursor()

    cur_us.execute("""CREATE TABLE IF NOT EXISTS users(
        user_id INTEGER PRIMARY KEY,
        user_name TEXT,
        user_name_tag TEXT,
        worked_class TEXT,
        first_visit TEXT,
        last_visit TEXT)
    """)
    my_logger.info("Users db created/exist")

    cur_ad.execute("""CREATE TABLE IF NOT EXISTS admins(
        user_id INTEGER PRIMARY KEY,
        user_name TEXT,
        user_name_tag TEXT,
        worked_class TEXT,
        first_visit TEXT,
        last_visit TEXT)
    """)
    my_logger.info("Admins db created/exist")

setup()