from telebot import *
from ws_parser import norm_schedule
from utils import sql_use

#with open("telegram_bot/api.txt", "r", encoding="utf-8") as f: api = f.read()
api = "8004422788:AAGwMlUOxdTO236TSwydt_R68sxnisYaJVk"
bot = telebot.TeleBot(api, parse_mode="HTML")


bot.send_message(6983370282, text=norm_schedule("5А", "thursday"))

@bot.message_handler(func=lambda message: True)
def echo_message(message):
    if message.from_user.id == 6983370282:
        bot.reply_to(message, message.text)

        sql_use.update_user_data(message_from_user=message)

bot.infinity_polling()