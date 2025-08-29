from telebot import *
from ws_parser import norm_schedule

with open("telegram_bot/api.txt", "r", encoding="utf-8") as f: api = f.read()

bot = telebot.TeleBot(api, parse_mode="HTML")


bot.send_message(6983370282, text=norm_schedule("5А", "thursday"))