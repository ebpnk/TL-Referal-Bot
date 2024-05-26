import json
import telebot
from telebot import types
from handlers import (handle_start, handle_referral_code, handle_enter_referral,
                      handle_view_balance, handle_view_bonuses, handle_my_bonuses,
                      handle_redeem)
import threading
import os

def load_or_create_config():
    default_config = {
        "TOKEN": "YOUR_TELEGRAM_BOT_TOKEN"
    }
    config_path = 'config.json'
    if not os.path.exists(config_path):
        with open(config_path, 'w') as config_file:
            json.dump(default_config, config_file, indent=4)
        print("Created default config.json. Please configure your TOKEN and restart the bot.")
        exit()
    else:
        with open(config_path, 'r') as config_file:
            return json.load(config_file)

config = load_or_create_config()
TOKEN = config['TOKEN']

bot = telebot.TeleBot(TOKEN)

# Регистрация обработчиков сообщений
bot.register_message_handler(lambda message: handle_start(message, bot), commands=['start'])
bot.register_message_handler(lambda message: handle_referral_code(message, bot), func=lambda message: message.text == "Ваш реферальный код")
bot.register_message_handler(lambda message: handle_enter_referral(message, bot), func=lambda message: message.text == "Ввести реферальный код")
bot.register_message_handler(lambda message: handle_view_balance(message, bot), func=lambda message: message.text == "Ваш баланс")
bot.register_message_handler(lambda message: handle_view_bonuses(message, bot), func=lambda message: message.text == "Бонусы")
bot.register_message_handler(lambda message: handle_my_bonuses(message, bot), func=lambda message: message.text == "Мои бонусы")

# Регистрация коллбэк обработчика
@bot.callback_query_handler(func=lambda call: call.data.startswith('redeem_'))
def callback_handle_redeem(call):
    handle_redeem(call, bot)

@bot.message_handler(func=lambda message: True, content_types=['text'])
def unknown_command(message):
    bot.send_message(message.chat.id, "Неизвестная команда. Возвращаем вас в главное меню.")
    handle_start(message, bot)  # Вызов функции, которая выводит основное меню

def run_bot():
    bot.polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
