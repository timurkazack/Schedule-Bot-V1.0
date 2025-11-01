from telebot import *
import ws_parser
from ws_parser import norm_schedule
from ws_parser import run_auto_update
import threading as th
import time
import traceback
import signal
import sys
from utils.sql_use import *
from utils import api
from utils.get_schedule import *
from utils import my_logger



class ScheduleBot:
    def __init__(self):
        self.api = api.get_api()
        self.opened_to_users = True
        self.admin_id = 6983370282
        self.bot = telebot.TeleBot(self.api, parse_mode="HTML")
        self._running = True
        self._stop_event = th.Event()
        
        # Текстовые константы
        self.TEXTS = {
            "choice_class": "📖 Выбрать класс",
            "choice_class_again": "◀️ Выбрать класс заново",
            "donate": "💸 Донат",
            "help": "❓ Написать в поддержку",
            "settings": "⚙️ Настройки",
            "classes": "классы",
            "site": "https://nextler.ru/6zk8zL1lsy.html?companyid=-mzPgPOgmP0hOUbHwopNk&tableid=-DpPW1Nus2Ypi6avVpfzu",
            
            "start_message": """👋 Привет {user_first_name}
На сайте расписания школы трудно найти свой класс?
<a href="https://nextler.ru/6zk8zL1lsy.html?companyid=-mzPgPOgmP0hOUbHwopNk&tableid=-DpPW1Nus2Ypi6avVpfzu">Сайт</a> долго грузит?

Я помогу тебе!
Тебе всего лишь надо выбрать свой класс, для этого используй клавиатуру👇""",
            
            "help_message": """Справка по боту:
/start - Перезапустить бота (Придётся заново выбрать класс)
/help - Получить эту справку
/proposal - Написать в поддержку

Дни недели/классы отображаются в соответствии с расписанием школы.
Если какого-то дня/класса нет в меню выбора, значит его нет и в расписании на сайте""",
            
            "from_chat_start": """Всем привет!
Админу: 
/set_class (Установить класс для получения расписания)
/set_newsletter_time (Задать время рассылки. Напиши данную команду и через пробел время в часах)
/disable_newsletter_time (Отменить рассылку в это время. Напиши данную команду и через пробел время в часах)""",
            
            "helper_message": "Напишите своё обращение:",
            "choice_parallel": "Выберете параллель👇",
            "choice_class": "Выберете класс👇",
            "save_class": "Сохранено!\nВыбирайте день недели и получайте расписание👇"
        }
        
        self._setup_handlers()
        self._setup_signal_handlers()
    


    def _setup_signal_handlers(self):
        """Настройка обработчиков сигналов для graceful shutdown"""
        def signal_handler(signum, frame):
            my_logger.info(f"Received signal {signum}, shutting down...")
            self.stop()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    


    def _setup_handlers(self):
        """Настройка обработчиков сообщений"""
        # Команды
        self.bot.message_handler(commands=["start"])(self._handle_start)
        self.bot.message_handler(commands=["help"])(self._handle_help)
        self.bot.message_handler(commands=["get_users_count"])(self._handle_get_users_count)
        self.bot.message_handler(commands=["get_all_users"])(self._handle_get_all_users)
        self.bot.message_handler(commands=["post"])(self._handle_post)
        self.bot.message_handler(commands=["stop"])(self._handle_stop)
        self.bot.message_handler(commands=["upd"])(self._handle_update)
        self.bot.message_handler(commands=["aus"])(self._handle_auto_update_swap)
        self.bot.message_handler(commands=["otus"])(self._handle_open_to_users_swap)
        #self.bot.message_handler(commands=["ban"])(self._handle_ban_user)
        #self.bot.message_handler(commands=["unban"])(self._handle_unban_user)
        #self.bot.message_handler(commands=["ban_list"])(self._handle_ban_users_list)
        self.bot.message_handler(commands=["proposal"])(self._handle_proposal)
        
        # Текстовые обработчики
        self.bot.message_handler(func=lambda message: message.text == self.TEXTS["help"])
        (self._handle_help_contact)
        self.bot.message_handler(
            func=lambda message: message.text in [self.TEXTS["choice_class"], self.TEXTS["choice_class_again"]])    (self._handle_choice_parallel)
        
        self.bot.message_handler(
            func=lambda message: message.text in [f"{key} {self.TEXTS['classes']}" for key in get_classes()])   (self._handle_choice_class)
        
        self.bot.message_handler(
            func=lambda message: any(message.text in classes for classes in get_classes().values()))    (self._handle_save_class)
        
        self.bot.message_handler(
            func=lambda message: message.text in russian_days())    (self._handle_get_schedule)
        
        # Обработчик обращений
        self.bot.callback_query_handler(
            func=lambda call: call.data[:4]=='help')     (self._handle_admin_help_react_step_1)
    


    def _log_user_action(self, user_data, action, details=""):
        """Логирование действий пользователя"""
        log_message = f"{user_data['tg_id']} used {action}"
        if details:
            log_message += f" and choice {details}"
        my_logger.info(log_message)
    


    def _check_access(self, user_data, message=None):
        """Проверка доступа пользователя"""
        if not self.opened_to_users\
            and user_data.get("is_admin") != 1\
            and user_data.get("is_baned") != 1:
            if message:
                self.bot.reply_to(message, "❌ Бот временно недоступен")
            return False
        
        if message and message.chat.type in ["group", "supergroup"]:
            if user_data.get("is_admin") != 1:
                self.bot.delete_message(message.chat.id, message.message_id)
                return False
        
        return True
    


    def _handle_start(self, message):
        """Обработка команды /start"""
        try:
            update_user_data(message)
            user_data = get_user_data(message)
            self._log_user_action(user_data, "START MESSAGE FUNC")
            
            markup = self._create_main_menu()
            
            if not self._check_access(user_data, message):
                return
            
            if message.chat.type not in ["group", "supergroup"]:
                self.bot.send_message(
                    user_data["tg_id"], 
                    self.TEXTS["start_message"].format(user_first_name=user_data["tg_first_name"]), 
                    reply_markup=markup
                )
            else:
                chat_member = self.bot.get_chat_member(message.chat.id, message.from_user.id)
                if chat_member.status in ["creator", "administrator"]:
                    self.bot.send_message(message.chat.id, "привет админ")
                self.bot.delete_message(message.chat.id, message.message_id)
                
        except Exception as e:
            my_logger.error(f"Error in start handler: {e}\n{traceback.format_exc()}")
            if 'message' in locals():
                self.bot.reply_to(message, "❌ Произошла ошибка при запуске бота")
    


    def _handle_help(self, message):
        """Обработка команды /help"""
        try:
            update_user_data(message)
            user_data = get_user_data(message)
            self._log_user_action(user_data, "HELP MESSAGE FUNC")
            
            if self._check_access(user_data):
                self.bot.send_message(message.from_user.id, self.TEXTS["help_message"])
                
        except Exception as e:
            my_logger.error(f"Error in help handler: {e}\n{traceback.format_exc()}")
            self.bot.reply_to(message, "❌ Произошла ошибка при получении справки")
    


    def _handle_get_users_count(self, message):
        """Обработка команды /get_users_count (только для админа)"""
        try:
            update_user_data(message)
            user_data = get_user_data(message)
            self._log_user_action(user_data, "GET USER COUNT FUNC")
            
            if user_data.get("is_admin") == 1:
                count = get_users_count()
                self.bot.reply_to(message, f"👥 Пользователей: {count}")
                
        except Exception as e:
            my_logger.error(f"Error in get_users_count handler: {e}\n{traceback.format_exc()}")
            self.bot.reply_to(message, "❌ Ошибка при получении количества пользователей")
    


    def _handle_get_all_users(self, message):
        """Обработка команды /get_all_users (только для админа)"""
        try:
            update_user_data(message)
            user_data = get_user_data(message)
            self._log_user_action(user_data, "GET ALL USERS FUNC")
            
            if user_data.get("is_admin") == 1:
                with open(get_all_users_data(), "r", encoding="utf-8") as f:
                    self.bot.send_document(message.from_user.id, f)
                    
        except Exception as e:
            my_logger.error(f"Error in get_all_users handler: {e}\n{traceback.format_exc()}")
            self.bot.reply_to(message, "❌ Ошибка при получении данных пользователей")
    


    def _handle_post(self, message):
        """Обработка команды /post (только для админа)"""
        try:
            update_user_data(message)
            user_data = get_user_data(message)
            self._log_user_action(user_data, "POST FUNC")
            
            if user_data.get("is_admin") == 1:
                self.bot.reply_to(message, "✅\nНапиши пост!")
                self.bot.register_next_step_handler(message, self._handle_post_step2)
                
        except Exception as e:
            my_logger.error(f"Error in post handler: {e}\n{traceback.format_exc()}")
            self.bot.reply_to(message, "❌ Ошибка при создании рассылки")
    


    def _handle_post_step2(self, message):
        """Второй шаг обработки рассылки"""
        try:
            user_data = get_user_data(message)
            
            if user_data.get("is_admin") == 1:
                am = self.bot.send_message(self.admin_id, "🔄 Начинаю рассылку...")
                
                ids = get_all_users_ids()
                success_count = 0
                
                for user_id in ids:
                    try:
                        time.sleep(0.5)
                        self.bot.forward_message(user_id, user_data['tg_id'], message.message_id)
                        success_count += 1
                        my_logger.info(f"Forward post to {user_id} [{ids.index(user_id)+1}/{len(ids)}]")
                        
                        self.bot.edit_message_text(
                            f"📤 [{ids.index(user_id)+1}/{len(ids)}] Успешно: {success_count}", 
                            self.admin_id, 
                            am.message_id
                        )
                    except Exception as e:
                        my_logger.error(f"Failed to send to {user_id}: {e}")
                
                my_logger.info("Forwards complete")
                self.bot.edit_message_text(
                    f"✅ Рассылка завершена! Отправлено: {success_count}/{len(ids)}", 
                    self.admin_id, 
                    am.message_id
                )
                
        except Exception as e:
            my_logger.error(f"Error in post step2: {e}\n{traceback.format_exc()}")
    


    def _handle_stop(self, message):
        """Обработка команды /stop (только для админа)"""
        try:
            update_user_data(message)
            user_data = get_user_data(message)
            self._log_user_action(user_data, "STOP FUNC")
            
            if user_data.get("is_admin") == 1:
                stop_db()
                self.bot.reply_to(message, "🛑 Останавливаю бота...")
                self.stop()
                
        except Exception as e:
            my_logger.error(f"Error in stop handler: {e}\n{traceback.format_exc()}")
    


    def _handle_update(self, message):
        """Обработка команды /upd (только для админа)"""
        try:
            update_user_data(message)
            user_data = get_user_data(message)
            self._log_user_action(user_data, "UPD FUNC")
            
            if user_data.get("is_admin") == 1:
                self.bot.reply_to(message, "🔄 Обновляю расписание...")
                ws_parser.get_data_from_server()
                self.bot.reply_to(message, "✅ Расписание обновлено")
                
        except Exception as e:
            my_logger.error(f"Error in update handler: {e}\n{traceback.format_exc()}")
            self.bot.reply_to(message, "❌ Ошибка при обновлении расписания")



    def _handle_auto_update_swap(self, message):
        """Обработка команды /aus (только для админа)"""
        try:
            update_user_data(message)
            user_data = get_user_data(message)
            self._log_user_action(user_data, "AUTO UPDATE SWAP FUNC")
            
            if user_data.get("is_admin") == 1:
                ws_parser.updates = not ws_parser.updates
                status = "включено" if ws_parser.updates else "выключено"
                self.bot.reply_to(message, f"✅ Автообновление {status}")
                
        except Exception as e:
            my_logger.error(f"Error in auto update swap handler: {e}\n{traceback.format_exc()}")
            self.bot.reply_to(message, "❌ Ошибка при изменении настроек автообновления")



    def _handle_open_to_users_swap(self, message):
        """Обработка команды /otus (только для админа)"""
        try:
            update_user_data(message)
            user_data = get_user_data(message)
            self._log_user_action(user_data, "OPEN TO USERS SWAP FUNC")

            if user_data.get("is_admin") == 1:
                self.opened_to_users = not self.opened_to_users
                status = "включен" if self.opened_to_users else "выключен"
                self.bot.reply_to(message, f"✅ Доступ для пользователей {status}")

        except Exception as e:
            my_logger.error(f"Error in open to users swap handler: {e}\n{traceback.format_exc()}")
            self.bot.reply_to(message, "❌ Ошибка при изменении настроек доступа для пользователей")
    


    '''
    def _handle_ban_user(self, message):
        """Обработка команды /ban {tg_id} {time_m} {reason} (только для админа)"""
        try:
            update_user_data(message)
            user_data = get_user_data(message)
            self._log_user_action(user_data, "BAN USER FUNC")

            if user_data.get("is_admin") == 1:
                arg = message.text.split(" ")
                if len(arg)<4:
                    self.bot.reply_to(message, "Неверное кол-во аргементов")


                user_id = arg[1]
                user_data = get_user_data(message=False, _tg_id=user_id)
                user_first_name = user_data["tg_first_name"]
                user_last_name = user_data["tg_last_name"]
                user_tg_name = user_data["tg_user_name"]
                time_banned = arg[2]
                reason = arg[3]

                update_user_data(message=None,
                                 _tg_id=user_id,
                                 _tg_first_name=user_first_name,
                                 _tg_last_name=user_last_name,
                                 _tg_user_name=user_tg_name,
                                 
                                 is_baned=1,
                                 ban_time_left=time_banned,
                                 ban_reason=reason)
                
            self.bot.send_message(user_id, f"""Внимание!
                                  Вы были заблокированны!
                                  Времяя до разблокировки: {str(time_banned) if time_banned==9999 else 'вечность'}
                                  nПричина: {reason}""")

        except Exception as e:
            my_logger.error(f"Error in ban user handler: {e}\n{traceback.format_exc()}")
            self.bot.reply_to(message, "❌ Ошибка при бане пользователя")



    def _handle_unban_user(self, message):
        """Обработка команды /unban {tg_id} (только для админа)"""
        try:
            update_user_data(message)
            user_data = get_user_data(message)
            self._log_user_action(user_data, "UNBAN USER FUNC")

            if user_data.get("is_admin") == 1:
                pass

        except Exception as e:
            my_logger.error(f"Error in unban user handler: {e}\n{traceback.format_exc()}")
            self.bot.reply_to(message, "❌ Ошибка при разбане пользователя")



    def _handle_ban_users_list(self, message):
        """Обработка команды /ban_list (только для админа)"""
        try:
            update_user_data(message)
            user_data = get_user_data(message)
            self._log_user_action(user_data, "BAN LIST FUNC")

            if user_data.get("is_admin") == 1:
                with open(get_ban_users_list(), "r", encoding="utf-8") as f:
                    self.bot.send_document(self.admin_id, f)
            
        except Exception as e:
            my_logger.error(f"Error in ban list handler: {e}\n{traceback.format_exc()}")
            self.bot.reply_to(message, "❌ Ошибка при обработке списка забаненых пользователей")
            '''



    def _handle_proposal(self, message):
        """Обработка команды /proposal"""
        try:
            update_user_data(message)
            user_data = get_user_data(message)
            #self._log_user_action(user_data, "PROPOSAL FUNC")
            
            if self._check_access(user_data):
                self.bot.send_message(message.from_user.id, self.TEXTS["helper_message"])
                self.bot.register_next_step_handler(message, self._send_to_admin_helper_message)
                
        except Exception as e:
            my_logger.error(f"Error in proposal handler: {e}\n{traceback.format_exc()}")
            self.bot.reply_to(message, "❌ Ошибка при отправке обращения")
    


    def _send_to_admin_helper_message(self, message):
        """Отправка обращения администратору"""
        try:
            update_user_data(message)
            user_data = get_user_data(message)

            if self._check_access(user_data):
                markup = types.InlineKeyboardMarkup()
                markup.add(
                    types.InlineKeyboardButton("Ответить", callback_data=f"help_{message.from_user.id}_{message.message_id}")
                )

                self.bot.send_message(
                    self.admin_id, 
                    f"📩 Новое обращение от {message.from_user.id} ({user_data['tg_first_name']}):\n{message.text}",
                    reply_markup=markup
                )
                self.bot.send_message(message.from_user.id, "✅ Ваше обращение отправлено администратору")

        except Exception as e:
            my_logger.error(f"Error in send to admin helper: {e}\n{traceback.format_exc()}")
            self.bot.reply_to(message, "❌ Ошибка при отправке обращения")



    def _handle_admin_help_react_step_1(self, call):
        """Первый шаг обработки ответа на обращение"""
        try:
            # Получаем данные из callback
            data_parts = call.data.split('_')
            if len(data_parts) != 3:
                return

            user_id = int(data_parts[1])
            message_id = int(data_parts[2])

            # Сохраняем данные для следующего шага
            self.bot.answer_callback_query(call.id, "Напишите ответ пользователю")

            # Регистрируем следующий шаг с передачей user_id
            msg = self.bot.send_message(self.admin_id, "✏️ Введите ответ для пользователя:")
            self.bot.register_next_step_handler(msg, self._handle_admin_help_react_step_2, user_id)

        except Exception as e:
            my_logger.error(f"Error in admin react help 1: {e}\n{traceback.format_exc()}")
            self.bot.send_message(self.admin_id, "❌ Ошибка при обработке ответа на обращение (1)")



    def _handle_admin_help_react_step_2(self, message, user_id):
        """Второй шаг обработки ответа на обращение - отправка ответа пользователю"""
        try:
            # Проверяем, что сообщение от админа
            user_data = get_user_data(message)
            if self._check_access(user_data):

                # Отправляем ответ пользователю
                self.bot.send_message(user_id, f"📩 Ответ от администратора:\n{message.text}")
                self.bot.reply_to(message, "✅ Ответ отправлен пользователю")

        except Exception as e:
            my_logger.error(f"Error in admin react help 2: {e}\n{traceback.format_exc()}")
            self.bot.send_message(self.admin_id, "❌ Ошибка при обработке ответа на обращение (2)")



    def _handle_help_contact(self, message):
        """Обработка кнопки помощи"""
        try:
            update_user_data(message)
            user_data = get_user_data(message)
            self._log_user_action(user_data, "GET HELP FUNC")
            
            if self._check_access(user_data):
                self.bot.send_message(message.from_user.id, self.TEXTS["helper_message"])
                self.bot.register_next_step_handler(message, self._send_to_admin_helper_message)
                
        except Exception as e:
            my_logger.error(f"Error in help contact handler: {e}\n{traceback.format_exc()}")
            self.bot.reply_to(message, "❌ Ошибка при обращении в поддержку")
    


    def _handle_choice_parallel(self, message):
        """Обработка выбора параллели"""
        try:
            update_user_data(message)
            user_data = get_user_data(message)
            self._log_user_action(user_data, "CHOICE PARALLEL FUNC")
            
            if self._check_access(user_data):
                markup = self._create_parallel_markup()
                self.bot.send_message(message.from_user.id, self.TEXTS["choice_parallel"], reply_markup=markup)
                
        except Exception as e:
            my_logger.error(f"Error in choice parallel handler: {e}\n{traceback.format_exc()}")
            self.bot.reply_to(message, "❌ Ошибка при выборе параллели")
    


    def _handle_choice_class(self, message):
        """Обработка выбора класса"""
        try:
            update_user_data(message)
            user_data = get_user_data(message)
            parallel = message.text.replace(f" {self.TEXTS['classes']}", "")
            self._log_user_action(user_data, "CHOICE CLASS FUNC", parallel)
            
            if self._check_access(user_data):
                markup = self._create_class_markup(parallel)
                self.bot.send_message(message.from_user.id, self.TEXTS["choice_class"], reply_markup=markup)
                
        except Exception as e:
            my_logger.error(f"Error in choice class handler: {e}\n{traceback.format_exc()}")
            self.bot.reply_to(message, "❌ Ошибка при выборе класса")
    


    def _handle_save_class(self, message):
        """Сохранение выбранного класса"""
        try:
            update_user_data(message, klass=message.text)
            user_data = get_user_data(message)
            self._log_user_action(user_data, "SAVE CHOICE CLASS FUNC", message.text)
            
            if self._check_access(user_data):
                markup = self._create_days_markup()
                self.bot.send_message(message.from_user.id, self.TEXTS["save_class"], reply_markup=markup)
                
        except Exception as e:
            my_logger.error(f"Error in save class handler: {e}\n{traceback.format_exc()}")
            self.bot.reply_to(message, "❌ Ошибка при сохранении класса")
    


    def _handle_get_schedule(self, message):
        """Получение расписания"""
        try:
            update_user_data(message)
            user_data = get_user_data(message)
            self._log_user_action(user_data, "GET SCHEDULE FUNC", message.text)
            
            if self._check_access(user_data):
                ru_day = message.text
                en_day = get_ru_day_to_en(ru_day)
                
                if not en_day:
                    self.bot.reply_to(message, "❌ Ошибка: день недели не распознан")
                    return
                
                schedule_text = norm_schedule(user_data["worked_class"], en_day)
                self.bot.send_message(message.from_user.id, schedule_text)
                
        except Exception as e:
            my_logger.error(f"Error in get schedule handler: {e}\n{traceback.format_exc()}")
            self.bot.reply_to(message, "❌ Ошибка при получении расписания")
    


    def _create_main_menu(self):
        """Создание главного меню"""
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row(types.KeyboardButton(self.TEXTS["choice_class"]))
        markup.row(types.KeyboardButton(self.TEXTS["help"]))
        return markup
    


    def _create_parallel_markup(self):
        """Создание клавиатуры с параллелями"""
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = [types.KeyboardButton(parallel + f" {self.TEXTS['classes']}") 
                  for parallel in get_classes()]
        markup.add(*buttons)
        return markup
    


    def _create_class_markup(self, parallel):
        """Создание клавиатуры с классами параллели"""
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        classes = get_classes()
        if parallel in classes:
            buttons = [types.KeyboardButton(klass) for klass in classes[parallel]]
            markup.add(*buttons)
        return markup
    


    def _create_days_markup(self):
        """Создание клавиатуры с днями недели"""
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = [types.KeyboardButton(day) for day in russian_days()]
        markup.add(*buttons)
        markup.row(types.KeyboardButton(self.TEXTS["choice_class_again"]))
        return markup
    


    def stop(self):
        """Остановка бота"""
        my_logger.info("Stopping bot...")
        self._running = False
        self._stop_event.set()
        try:
            self.bot.stop_polling()
        except Exception as e:
            my_logger.error(f"Error stopping bot: {e}")
    


    def run(self):
        """Запуск бота"""
        try:
            my_logger.info("Starting bot...")
            run_auto_update()
            self.bot.remove_webhook()
            
            # Запуск в отдельном потоке
            self.bot_thread = th.Thread(target=self._polling_loop, daemon=True)
            self.bot_thread.start()
            
            my_logger.info("Bot started successfully")
            return self._stop_event
            
        except Exception as e:
            my_logger.error(f"Failed to start bot: {e}\n{traceback.format_exc()}")
            raise
    


    def _polling_loop(self):
        """Цикл опроса бота с обработкой исключений"""
        while self._running and not self._stop_event.is_set():
            try:
                my_logger.info("Starting bot polling...")
                self.bot.polling(none_stop=True, timeout=30)
                
            except Exception as e:
                if self._running and not self._stop_event.is_set():
                    my_logger.error(f"Bot polling error: {e}\n{traceback.format_exc()}")
                    my_logger.info("Restarting bot in 10 seconds...")
                    time.sleep(10)
        
        my_logger.info("Bot polling loop stopped")





def main():
    """Основная функция запуска с автоматическим выключением по времени"""
    bot = None
    try:
        bot = ScheduleBot()
        stop_event = bot.run()
        
        # Получаем время остановки из настроек
        stop_time_h = utils.get_settings("telegram_bot", "stop_time_h")
        
        if stop_time_h:
            my_logger.info(f"Bot will auto-stop after {stop_time_h} hours")
            
            # Ожидаем либо сигнала остановки, либо истечения времени
            stopped = stop_event.wait(stop_time_h * 60 * 60)
            
            if stopped:
                my_logger.info("Bot stopped by stop event")
            else:
                my_logger.info(f"Bot auto-stopped after {stop_time_h} hours")
        else:
            my_logger.info("Bot running indefinitely (no stop_time_h setting)")
            # Если время не задано, ждем бесконечно
            stop_event.wait()
            
    except KeyboardInterrupt:
        my_logger.info("Bot stopped by user (Ctrl+C)")
    except Exception as e:
        my_logger.error(f"Fatal error in main: {e}\n{traceback.format_exc()}")
    finally:
        if bot:
            bot.stop()
        my_logger.info("Bot shutdown complete")


if __name__ == "__main__":
    main()