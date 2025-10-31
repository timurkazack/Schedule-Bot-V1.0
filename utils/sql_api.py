import sqlite3 as sq
import os
import threading
from utils import my_logger
from datetime import datetime as dt
from contextlib import contextmanager

# Путь к базе данных пользователей
users_db = f"{os.path.dirname(__file__)}/data/users/users_db.db".replace("\\", "/")

# Локальное хранилище для соединений (по одному на поток)
_thread_local = threading.local()

def get_connection():
    """
    Получение соединения с базой данных для текущего потока
    """
    if not hasattr(_thread_local, "connection"):
        _thread_local.connection = sq.connect(users_db, check_same_thread=False)
        _thread_local.connection.row_factory = sq.Row
    return _thread_local.connection

@contextmanager
def get_cursor():
    """
    Контекстный менеджер для работы с курсором
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()

def setup():
    """
    Инициализация базы данных: создание необходимых таблиц
    """
    try:
        my_logger.info("Starting connection to database")
        
        with get_cursor() as cur_us:
            # Создание таблицы пользователей, если она не существует
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

            # Создание таблицы рассылки, если она не существует
            cur_us.execute("""CREATE TABLE IF NOT EXISTS newsletter(
                chat_id INTEGER PRIMARY KEY,
                time TEXT,
                class TEXT)""")

        my_logger.info("Users database created/exists")
        
    except sq.Error as e:
        my_logger.error(f"Database setup error: {e}")
        raise

def update_user_data(message_from_user, klass=None,
                     is_admin=None, is_baned=None,
                     ban_time_left=None,  # в минутах
                     ban_reason=None,
                     donated_money=None,
                     _tg_id=None,
                     _tg_first_name=None,
                     _tg_last_name=None,
                     _tg_user_name=None
                     ):
    """
    Обновление или создание данных пользователя
    
    Args:
        message_from_user: Объект сообщения от пользователя
        klass: Класс пользователя
        is_admin: Флаг администратора (0/1)
        is_baned: Флаг блокировки (0/1)
        ban_time_left: Время блокировки в минутах
        ban_reason: Причина блокировки
        donated_money: Сумма пожертвований
    """
    try:
        # Извлечение данных из объекта сообщения
        if message_from_user:
            tg_id = int(message_from_user.chat.id)
            tg_first_name = str(message_from_user.chat.first_name)
            tg_last_name = str(message_from_user.chat.last_name)
            tg_user_name = str(message_from_user.chat.username)
        else:
            tg_id = _tg_id
            tg_first_name = _tg_first_name
            tg_last_name = _tg_last_name
            tg_user_name = _tg_user_name

        # Получение текущего времени в формате строки
        current_time = dt.now().strftime("%Y-%m-%d %H:%M:%S")

        # Установка времени блокировки, если пользователь заблокирован
        ban_time = current_time if is_baned == 1 else None

        with get_cursor() as cur_us:
            # Проверяем существование пользователя
            cur_us.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,))
            user_data = cur_us.fetchone()

            if not user_data:
                # Создание новой записи для нового пользователя
                my_logger.info(f"Creating new user record for ID: {tg_id}")
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
                # Обновление существующей записи пользователя
                my_logger.info(f"Updating existing user record for ID: {tg_id}")
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

        my_logger.info(f"User data successfully updated for ID: {tg_id}")
        
    except sq.Error as e:
        my_logger.error(f"Error updating user data for ID {tg_id}: {e}")
        raise
    except Exception as e:
        my_logger.error(f"Unexpected error in update_user_data: {e}")
        raise

def get_user_data(message):
    """
    Получение данных пользователя по ID из сообщения
    
    Args:
        message: Объект сообщения от пользователя
        
    Returns:
        dict: Словарь с данными пользователя или None, если пользователь не найден
    """
    tg_id = int(message.from_user.id)

    try:
        with get_cursor() as cur_us:
            cur_us.execute("""
                SELECT * FROM users WHERE tg_id = ?
            """, (tg_id,))

            user_data = cur_us.fetchone()

            if user_data:
                # Преобразование результата в словарь с именами колонок
                return dict(user_data)
            else:
                my_logger.info(f"User not found with ID: {tg_id}")
                return None

    except sq.Error as e:
        my_logger.error(f"Database error in get_user_data for ID {tg_id}: {e}")
        return None
    except Exception as e:
        my_logger.error(f"Unexpected error in get_user_data: {e}")
        return None

def get_user_count():
    """
    Получение общего количества пользователей в базе данных
    
    Returns:
        int: Количество пользователей
    """
    try:
        with get_cursor() as cur_us:
            cur_us.execute("SELECT COUNT(*) FROM users;")
            result = cur_us.fetchone()
            count = result[0]

        my_logger.info(f"Retrieved user count: {count}")
        return count
        
    except sq.Error as e:
        my_logger.error(f"Error getting user count: {e}")
        return 0

def get_all_sql_users():
    """
    Экспорт всех пользователей в текстовый файл
    
    Returns:
        str: Путь к созданному файлу с данными пользователей
    """
    try:
        with get_cursor() as cur_us:
            cur_us.execute("SELECT * FROM users;")
            result = cur_us.fetchall()

        # Создание временного файла для экспорта
        file = f"{os.path.dirname(__file__)}/data/.temp/all.txt".replace('\\', '/')
        
        # Создание директории, если она не существует
        os.makedirs(os.path.dirname(file), exist_ok=True)

        with open(file, "w", encoding="utf-8") as f:
            text = ""
            for user in result:
                line = ""
                # Запись первых 7 полей пользователя
                for obj in user[:7]:
                    line += str(obj) + "\t"
                text += line + "\n"
            f.write(text)

        my_logger.info(f"User data exported to: {file}")
        return file
        
    except sq.Error as e:
        my_logger.error(f"Database error in get_all_sql_users: {e}")
        raise
    except Exception as e:
        my_logger.error(f"File operation error in get_all_sql_users: {e}")
        raise

def get_all_users_id():
    """
    Получение списка всех ID пользователей
    
    Returns:
        list: Список ID пользователей
    """
    try:
        with get_cursor() as cur_us:
            cur_us.execute("SELECT tg_id FROM users;")
            result = cur_us.fetchall()
            
        # Преобразование результата в плоский список
        user_ids = [item[0] for item in result]
        
        my_logger.info(f"Retrieved {len(user_ids)} user IDs")
        return user_ids
        
    except sq.Error as e:
        my_logger.error(f"Error getting all user IDs: {e}")
        return []
    except Exception as e:
        my_logger.error(f"Unexpected error in get_all_users_id: {e}")
        return []

def add_time(chat_id, time):
    """
    Функция для добавления времени рассылки (временно не реализована)
    
    Args:
        chat_id: ID чата
        time: Время рассылки
    """
    my_logger.warning("add_time function is not implemented yet")
    pass

def close_connections():
    """
    Закрытие всех соединений с базой данных
    """
    if hasattr(_thread_local, "connection"):
        _thread_local.connection.close()
        delattr(_thread_local, "connection")

def stop():
    """
    Остановка модуля базы данных
    """
    close_connections()

# Инициализация базы данных при импорте модуля
try:
    setup()
except Exception as e:
    my_logger.critical(f"Failed to initialize database: {e}")
    raise