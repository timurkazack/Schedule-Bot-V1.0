from telebot import *
from ws_parser import norm_schedule
from ws_parser import run_auto_update
import ws_parser
from utils.sql_use import *
from utils import api
from utils.get_schedule import *


#password = input("PASSWORD > ")
api = api.get_api() #password

opened_to_users = False

bot = telebot.TeleBot(api)  # , parse_mode="HTML")

run_auto_update()


choice_class_text = "📖 Выбрать класс"
donate_text = "💸 Донат"
help_text = "❓ Написать в поддержку"
settings_text = "⚙️ Настройки"
classes_text = "классы"


#@bot.message_handler(func=lambda message: True)
#def echo_message(message):
#    if message.from_user.id == 6983370282:
#        bot.reply_to(message, "⚙️📖")
#        bot.send_message(6983370282, text=norm_schedule("8К", "thursday"))
#
#        sql_use.update_user_data(message_from_user=message, is_admin=True)



@bot.message_handler(commands=["start"])
def start_func(message):
    update_user_data(message)
    user_data = get_user_data(message)

    msg = """
        START TEXT MESSAGE
    """

    markup_menu_buttons = types.ReplyKeyboardMarkup(resize_keyboard=True)
    choice_class_menu_button = types.KeyboardButton(choice_class_text)
    donate_menu_button = types.KeyboardButton(donate_text)
    help_menu_button = types.KeyboardButton(help_text)
    settings_menu_button = types.KeyboardButton(settings_text)

    markup_menu_buttons.row(choice_class_menu_button)
    #markup_menu_buttons.row(help_menu_button, donate_menu_button)
    #markup_menu_buttons.row(settings_menu_button)

    if not opened_to_users:
        if user_data["is_admin"] == 1:
            bot.send_message(message.from_user.id, msg, reply_markup=markup_menu_buttons)
    else:
        bot.send_message(message.from_user.id, msg, reply_markup=markup_menu_buttons)


@bot.message_handler(commands=["help"])
def help_func(message):
    update_user_data(message)
    user_data = get_user_data(message)

    msg = """
        HELP TEXT MESSAGE
    """


    if not opened_to_users:
        if user_data["is_admin"] == 1:
            bot.send_message(message.from_user.id, msg)
    else:
        bot.send_message(message.from_user.id, msg)





@bot.message_handler(commands=["upd"])
def upd_admin_func(message):
    update_user_data(message)
    user_data = get_user_data(message)

    if user_data["is_admin"] == 1:
        bot.reply_to(message, "✅")
        ws_parser.get_data_from_server()

@bot.message_handler(commands=["aus"])
def aus_admin_func(message):
    update_user_data(message)
    user_data = get_user_data(message)

    if user_data["is_admin"] == 1:
        bot.reply_to(message, "✅")
        ws_parser.updates = False if ws_parser.updates else True





@bot.message_handler(func=lambda message: message.text == choice_class_text)
def get_choice_parallel(message):
    update_user_data(message)
    user_data = get_user_data(message)

    msg = "Выберете параллель:"

    markup_parallel = types.ReplyKeyboardMarkup(resize_keyboard=True)

    buttons = []

    for parallel in get_classes():
        buttons.append(
            types.KeyboardButton(parallel + f" {classes_text}"))

    markup_parallel.add(*buttons)


    if not opened_to_users:
        if user_data["is_admin"] == 1:
            bot.send_message(message.from_user.id, msg, reply_markup=markup_parallel)
    else:
        bot.send_message(message.from_user.id, msg, reply_markup=markup_parallel)


@bot.message_handler(func=lambda message: message.text in [f"{key} {classes_text}" for key in get_classes()])
def get_choice_class(message):
    update_user_data(message)
    user_data = get_user_data(message)

    msg = "Выберете класс:"

    markup_class = types.ReplyKeyboardMarkup(resize_keyboard=True)

    buttons = []

    for klass in get_classes()[message.text.replace(f" {classes_text}", "")]:
        buttons.append(
            types.KeyboardButton(klass))

    markup_class.add(*buttons)

    if not opened_to_users:
        if user_data["is_admin"] == 1:
            bot.send_message(message.from_user.id, msg, reply_markup=markup_class)
    else:
        bot.send_message(message.from_user.id, msg, reply_markup=markup_class)


@bot.message_handler(func=lambda message: any(message.text in classes for classes in get_classes().values()))
def save_choice_class(message):
    update_user_data(message, klass=message.text)
    user_data = get_user_data(message)

    msg = """Сохранено!\nДля получения расписания воспользуетесь кнопками выбора дня недели.\n(Дни недели отображаются 
    в соответствии с расписанием школы.\nЕсли какого то дня нет в меню выбора, значит его нет и в расписании на 
    сайте)"""

    markup_days = types.ReplyKeyboardMarkup(resize_keyboard=True)

    buttons = []

    for day in russian_days():
        buttons.append(
            types.KeyboardButton(day))

    markup_days.add(*buttons)
    if not opened_to_users:
        if user_data["is_admin"] == 1:
            bot.send_message(message.from_user.id, msg, reply_markup=markup_days)
    else:
        bot.send_message(message.from_user.id, msg, reply_markup=markup_days)


@bot.message_handler(func=lambda message: message.text in russian_days())
def get_schedule_for_user(message):
    user_data = get_user_data(message)


    if not opened_to_users:
        if user_data["is_admin"] == 1:
            bot.send_message(message.from_user.id,
                             norm_schedule(user_data["worked_class"], get_ru_day_to_en(message.text)),
                             parse_mode="HTML")
    else:
        bot.send_message(message.from_user.id,
                         norm_schedule(user_data["worked_class"], get_ru_day_to_en(message.text)),
                         parse_mode="HTML")

bot.infinity_polling()