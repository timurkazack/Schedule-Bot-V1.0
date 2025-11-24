import utils.sql_api as sq

def update_user_data(message_from_user, klass=None,
                     is_admin=None, is_baned=None,
                     ban_time_left=None,
                     ban_reason=None,
                     donated_money=None):
   
   # Обновляет данные о пользователе
   # ! message       - Сообщение из бота (telebot)
   #   klass         - Класс рассписания
   #   is_admin      - Изменение статуса админа (0/1)
   #   is_banned     - Изменение статуса бана (0/1)
   #   ban_time_left - Время бана (в минутах)
   #   ban_reason    - Причина бана
   #   donated_money - Заплаченые деньги


   return sq.update_user_data(message_from_user, klass,
                     is_admin, is_baned,
                     ban_time_left,
                     ban_reason,
                     donated_money)


def get_user_data(message, _tg_id=None):
   
    # Возвращает данные пользователя
    # ! message - Сообщение из бота (telebot)


   return sq.get_user_data(message, _tg_id)


def get_users_by_class(klass):
   
   # Возвращает пользователей по классу


   return sq.get_users_by_class(klass)

def get_users_count():
   
   # Возвращает кол-во пользователей


   return sq.get_user_count()


def get_all_users_data():
   
   # Возвращает файл со всеми данными всех пользователей


   return sq.get_all_sql_users()


def get_all_users_ids():
   
   # Возвращает все id всех пользователей


   return sq.get_all_users_id()


def get_ban_users_list():

   # Возвращает отцентрованный список забанненых файлом


   return sq.get_ban_users_list()


def stop_db():

   # Завершает соеденение с бд


   return sq.stop()