from telebot import *
from ws_parser import norm_schedule
from ws_parser import run_auto_update
from utils import sql_use
from utils import api


password = input("PASSWORD > ")
api = api.get_api(password)


bot = telebot.TeleBot(api, parse_mode="HTML")

run_auto_update()

bot.send_message(6983370282, text=norm_schedule("8К", "tuesday"))

@bot.message_handler(func=lambda message: True)
def echo_message(message):
    if message.from_user.id == 6983370282:
        bot.reply_to(message, message.text)

        sql_use.update_user_data(message_from_user=message)

bot.infinity_polling()