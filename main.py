from telebot import *
import ws_parser
from ws_parser import norm_schedule
from ws_parser import run_auto_update
import threading as th
import time
from utils.sql_use import *
from utils import api
from utils.get_schedule import *
from utils import my_logger

#password = input("PASSWORD > ")
api = api.get_api() #password

opened_to_users = True

admin_id = 6983370282

bot = telebot.TeleBot(api, parse_mode="HTML")

run_auto_update()


choice_class_text = "📖 Выбрать класс"
choice_class_again_text = "◀️ Выбрать класс заново"
donate_text = "💸 Донат"
help_text = "❓ Написать в поддержку"
settings_text = "⚙️ Настройки"
classes_text = "классы"


site = "https://nextler.ru/6zk8zL1lsy.html?companyid=-mzPgPOgmP0hOUbHwopNk&tableid=-DpPW1Nus2Ypi6avVpfzu"


START_MESSAGE = """👋 Привет {user_first_name}
На сайте расписания школы трудно найти свой класс?
<a href="https://nextler.ru/6zk8zL1lsy.html?companyid=-mzPgPOgmP0hOUbHwopNk&tableid=-DpPW1Nus2Ypi6avVpfzu">Сайт</a> долго грузит?

Я помогу тебе!
Тебе всего лишь надо выбрать свой класс, для этого используй клавиатуру👇"""

HELP_MESSAGE = """Справка по боту:
/start - Перезапустить бота (Придётся заново выбрать класс)
/help - Получить эту справку
/proposal - Написать в поддержку

Дни недели/классы отображаются в соответствии с расписанием школы.
Если какого-то дня/класса нет в меню выбора, значит его нет и в расписании на сайте"""

FROM_CHAT_START_MESSAGE = """Всем привет!
Админу: 
/set_class (Установить класс для получения расписания)
/set_newsletter_time (Задать время рассылки. Напиши данную команду и через пробел время в часах)
/disable_newsletter_time (Отменить рассылку в это время. Напиши данную команду и через пробел время в часах)"""

HELPER_MESSAGE = "Напишите своё обращение:"
CHOICE_PARALLEL_MESSAGE = "Выберете параллель👇"
CHOICE_CLASS_MESSAGE = "Выберете класс👇"
SAVE_CLASS_MESSAGE = """Сохранено!
Выбирайте день недели и получайте расписание👇"""


def main():
   bot.polling(none_stop=True)
   time.sleep(utils.get_settings("telegram_bot", "stop_time_h") * 60 * 60)
   bot.stop_polling()
   import os

   os._exit(0)

@bot.message_handler(commands=["start"])
def start_func(message):
    update_user_data(message)
    user_data = get_user_data(message)
    my_logger.info(f"{user_data['tg_id']} used START MESSAGE FUNC")

    #from users
    markup_menu_buttons = types.ReplyKeyboardMarkup(resize_keyboard=True)
    choice_class_menu_button = types.KeyboardButton(choice_class_text)
    #donate_menu_button = types.KeyboardButton(donate_text)
    help_menu_button = types.KeyboardButton(help_text)
    #settings_menu_button = types.KeyboardButton(settings_text)

    markup_menu_buttons.row(choice_class_menu_button)
    markup_menu_buttons.row(help_menu_button)#, donate_menu_button)
    #markup_menu_buttons.row(settings_menu_button)



    if not opened_to_users:
        if user_data["is_admin"] == 1:
            bot.send_message(user_data["tg_id"], START_MESSAGE.format(user_first_name=user_data["tg_first_name"]), reply_markup=markup_menu_buttons)
    else:
        if message.chat.type not in ["group", "supergroup"]:
            bot.send_message(user_data["tg_id"], START_MESSAGE.format(user_first_name=user_data["tg_first_name"]), reply_markup=markup_menu_buttons)
        else:
            chat_member = bot.get_chat_member(message.chat.id, message.from_user.id)
            if chat_member.status in ["creator", "administrator"]:
                msg = bot.send_message(message.chat.id, "привет админ")
            bot.delete_message(message.chat.id, message.message_id)






@bot.message_handler(commands=["help"])
def help_func(message):
    update_user_data(message)
    user_data = get_user_data(message)
    my_logger.info(f"{user_data['tg_id']} used HELP MESSAGE FUNC")



    if opened_to_users or user_data["is_admin"] == 1:
        bot.send_message(message.from_user.id, HELP_MESSAGE)



@bot.message_handler(commands=["get_user_count"])
def get_users_count(message):
    update_user_data(message)
    user_data = get_user_data(message)
    my_logger.info(f"{user_data['tg_id']} used GET USER COUNT FUNC")

    if user_data["is_admin"] == 1:
        bot.reply_to(message, f"{get_user_count()} пользователей")

@bot.message_handler(commands=["get_all_users"])
def get_all_users(message):
    update_user_data(message)
    user_data = get_user_data(message)
    my_logger.info(f"{user_data['tg_id']} used GET ALL USERS FUNC")

    if user_data["is_admin"] == 1:
        with open(get_all_sql_users(), "r", encoding="utf-8") as f:
            bot.send_document(message.from_user.id, f)

@bot.message_handler(commands=["post"])
def post1(message):
    update_user_data(message)
    user_data = get_user_data(message)
    my_logger.info(f"{user_data['tg_id']} used POST FUNC")

    if user_data["is_admin"] == 1:
        bot.reply_to(message, "✅\nНапиши пост!")
        bot.register_next_step_handler(message, post2)

def post2(message):
    user_data = get_user_data(message)

    if user_data["is_admin"] == 1:
        am = bot.send_message(admin_id, "START")

        ids = get_all_users_id()

        for id in ids:
            time.sleep(0.5)
            bot.forward_message(id, user_data['tg_id'], message.message_id)
            my_logger.info(f"Forward post to {id} [{ids.index(id)+1}/{len(ids)}]")

            bot.edit_message_text(f"[{ids.index(id)+1}/{len(ids)}]", admin_id, am.message_id)

        logger.info("Forwards complete")
        bot.edit_message_text("COMPLETE", admin_id, am.message_id)


@bot.message_handler(commands=["stop"])
def stop_admin_func(message):
    update_user_data(message)
    user_data = get_user_data(message)
    my_logger.info(f"{user_data['tg_id']} used STOP FUNC")

    if user_data["is_admin"] == 1:
        bot.reply_to(message, "✅")
        bot.stop_polling()
        import os

        os._exit(0)


@bot.message_handler(commands=["upd"])
def upd_admin_func(message):
    update_user_data(message)
    user_data = get_user_data(message)
    my_logger.info(f"{user_data['tg_id']} used UPD FUNC")

    if user_data["is_admin"] == 1:
        bot.reply_to(message, "✅")
        ws_parser.get_data_from_server()

@bot.message_handler(commands=["aus"])
def aus_admin_func(message):
    update_user_data(message)
    user_data = get_user_data(message)
    my_logger.info(f"{user_data['tg_id']} used AUTO UPDATE SWAP FUNC")

    if user_data["is_admin"] == 1:
        bot.reply_to(message, "✅")
        ws_parser.updates = False if ws_parser.updates else True




@bot.message_handler(func=lambda message: message.text == help_text)
def get_help_contact(message):
    update_user_data(message)
    user_data = get_user_data(message)
    my_logger.info(f"{user_data['tg_id']} used GET HELP FUNC")


    if opened_to_users or user_data["is_admin"] == 1:
        bot.send_message(message.from_user.id, HELPER_MESSAGE)
        bot.register_next_step_handler(message, send_to_admin_helper_message)


@bot.message_handler(commands=["proposal"])
def send_to_admin_helper_message(message):
    update_user_data(message)
    user_data = get_user_data(message)
    my_logger.info(f"{user_data['tg_id']} used GET HELP FUNC 2")


    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Ответить", callback_data=f"help_{message.from_user.id}"),
        types.InlineKeyboardButton("Забанить", callback_data=f"ban_{message.from_user.id}"))


    if opened_to_users or user_data["is_admin"] == 1:
        bot.send_message(admin_id, f"Новое обращение ({message.from_user.id}):\n{message.text}")#, reply_markup=markup)
        bot.send_message(message.from_user.id, "Отправлено.")





@bot.message_handler(func=lambda message: message.text == choice_class_text or message.text == choice_class_again_text)
def get_choice_parallel(message):
    update_user_data(message)
    user_data = get_user_data(message)
    my_logger.info(f"{user_data['tg_id']} used CHOICE PARALLEL FUNC")


    markup_parallel = types.ReplyKeyboardMarkup(resize_keyboard=True)

    buttons = []

    for parallel in get_classes():
        buttons.append(
            types.KeyboardButton(parallel + f" {classes_text}"))

    markup_parallel.add(*buttons)


    if opened_to_users or user_data["is_admin"] == 1:
        bot.send_message(message.from_user.id, CHOICE_PARALLEL_MESSAGE, reply_markup=markup_parallel)






@bot.message_handler(func=lambda message: message.text in [f"{key} {classes_text}" for key in get_classes()])
def get_choice_class(message):
    update_user_data(message)
    user_data = get_user_data(message)
    my_logger.info(f"{user_data['tg_id']} used CHOICE CLASS FUNC and choice {message.text}")


    markup_class = types.ReplyKeyboardMarkup(resize_keyboard=True)

    buttons = []

    for klass in get_classes()[message.text.replace(f" {classes_text}", "")]:
        buttons.append(
            types.KeyboardButton(klass))

    markup_class.add(*buttons)

    if opened_to_users or user_data["is_admin"] == 1:
        bot.send_message(message.from_user.id, CHOICE_CLASS_MESSAGE, reply_markup=markup_class)


@bot.message_handler(func=lambda message: any(message.text in classes for classes in get_classes().values()))
def save_choice_class(message):
    update_user_data(message, klass=message.text)
    user_data = get_user_data(message)
    my_logger.info(f"{user_data['tg_id']} used SAVE CHOICE CLASS FUNC and choice {message.text}")


    markup_days = types.ReplyKeyboardMarkup(resize_keyboard=True)

    buttons = []

    for day in russian_days():
        buttons.append(
            types.KeyboardButton(day))

    markup_days.add(*buttons)
    markup_days.row(choice_class_again_text)

    if opened_to_users or user_data["is_admin"] == 1:
        bot.send_message(message.from_user.id, SAVE_CLASS_MESSAGE, reply_markup=markup_days)


@bot.message_handler(func=lambda message: message.text in russian_days())
def get_schedule_for_user(message):
    update_user_data(message)
    user_data = get_user_data(message)
    my_logger.info(f"{user_data['tg_id']} used GET SCHEDULE FUNC and choice {message.text}")

    ru_day = message.text
    en_day = get_ru_day_to_en(ru_day)

    if opened_to_users or user_data["is_admin"] == 1:
        bot.send_message(message.from_user.id,
                         norm_schedule(user_data["worked_class"], en_day))


bot.remove_webhook()
th1 = th.Thread(target = main)
th1.start()