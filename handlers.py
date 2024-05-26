from telebot import types
import random
import string
import json

def handle_start(message, bot):
    user_id = message.chat.id
    user_data = load_user_data()
    if str(user_id) in user_data:
        bot.send_message(user_id, "Вы уже зарегистрированы.")
    else:
        referral_code = generate_referral_code()
        user_data[str(user_id)] = {"referral_code": referral_code, "balance": 0, "used_codes": []}
        save_user_data(user_data)
        bot.send_message(user_id, f"Вы зарегистрированы. Ваш реферальный код: {referral_code}")
    show_menu(message, bot)

def show_menu(message, bot):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton("Ваш реферальный код"), types.KeyboardButton("Ввести реферальный код"), types.KeyboardButton("Ваши баллы"))
    bot.send_message(message.chat.id, "Выберите опцию:", reply_markup=markup)

def generate_referral_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def handle_referral_code(message, bot):
    user_id = message.chat.id
    user_data = load_user_data()
    referral_code = user_data[str(user_id)]["referral_code"]
    bot.send_message(message.chat.id, f"Ваш уникальный реферальный код: {referral_code}")

def handle_enter_referral(message, bot):
    msg = bot.send_message(message.chat.id, "Введите реферальный код друга:")
    bot.register_next_step_handler(msg, lambda message: process_referral_code(message, bot))

def process_referral_code(message, bot):
    user_id = str(message.chat.id)
    entered_code = message.text.strip()
    user_data = load_user_data()

    # Загружаем данные пользователя, если он зарегистрирован, иначе просим зарегистрироваться
    if user_id not in user_data:
        bot.send_message(user_id, "Вы не зарегистрированы. Пожалуйста, зарегистрируйтесь, используя команду /start.")
        return

    current_user = user_data[user_id]
    user_code = current_user["referral_code"]

    # Проверяем, что введенный код не совпадает с собственным кодом пользователя
    if entered_code == user_code:
        bot.send_message(user_id, "Вы не можете использовать свой собственный реферальный код.")
        return

    # Проверяем, существует ли введенный код в системе
    if not any(entered_code == data["referral_code"] for data in user_data.values()):
        bot.send_message(user_id, "Введенный реферальный код не существует.")
        return

    # Проверяем, использовал ли пользователь этот код ранее
    if entered_code in current_user.get("used_codes", []):
        bot.send_message(user_id, "Вы уже использовали этот реферальный код.")
        return

    # Добавляем код в список использованных и увеличиваем баланс на 1
    current_user.setdefault("used_codes", []).append(entered_code)
    current_user["balance"] = current_user.get("balance", 0) + 1

    save_user_data(user_data)
    bot.send_message(user_id, f"Реферальный код успешно применен! Вам начислен 1 балл. Ваш текущий баланс: {current_user['balance']}")


def handle_view_balance(message, bot):
    user_id = str(message.chat.id)  # Приводим user_id к строке
    user_data = load_user_data()
    if user_id in user_data:  # Проверяем, есть ли user_id как строка в user_data
        balance = user_data[user_id].get("balance", 0)
        bot.send_message(user_id, f"Ваш баланс баллов: {balance}")
    else:
        bot.send_message(user_id, "Вы не зарегистрированы. Пожалуйста, используйте команду /start для регистрации.")


def handle_view_bonuses(message, bot):
    user_id = str(message.chat.id)
    user_data = load_user_data()
    if user_id in user_data:
        bonuses = load_bonuses()
        if bonuses["bonuses"]:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            # Сортировка для гарантии, что все пункты будут обработаны
            for points in sorted(bonuses["bonuses"], key=lambda x: int(x)):
                description = bonuses["bonuses"][points]["description"]
                button_label = f"{points} баллов - {description}"
                markup.add(types.KeyboardButton(button_label))
            markup.add(types.KeyboardButton("Назад"))  # Добавляем кнопку "Назад"
            bot.send_message(user_id, "Выберите количество баллов для использования:", reply_markup=markup)
            bot.register_next_step_handler(message, lambda message: process_bonus_selection(message, bot))
        else:
            bot.send_message(user_id, "В данный момент бонусы не доступны.")
    else:
        bot.send_message(user_id, "Вы не зарегистрированы. Пожалуйста, используйте команду /start для регистрации.")


def process_bonus_selection(message, bot):
    user_id = str(message.chat.id)
    if message.text == "Назад":
        show_menu(message, bot)  # Выводим основное меню
        return

    user_data = load_user_data()
    balance = user_data[user_id].get("balance", 0)
    selected_text = message.text.split(' -')[0]  # Извлекаем только баллы
    selected_points = int(selected_text.split()[0])
    
    if selected_points > balance:
        bot.send_message(user_id, "У вас недостаточно баллов.")
    else:
        bonuses = load_bonuses()
        bonus_info = bonuses["bonuses"].get(str(selected_points))
        if bonus_info and bonus_info["codes"]:
            selected_code = random.choice(bonus_info["codes"])
            bonus_info["codes"].remove(selected_code)
            save_bonuses(bonuses)

            user_data[user_id]["balance"] -= selected_points
            user_data[user_id].setdefault("received_bonuses", []).append(selected_code)
            save_user_data(user_data)

            bot.send_message(user_id, f"Вы получили бонус: {selected_code}")
        else:
            bot.send_message(user_id, "Бонусы за эти баллы уже закончились или недоступны.")

    show_menu(message, bot)  # Возвращаем пользователя в главное меню



def handle_redeem(call):
    user_id = str(call.message.chat.id)
    user_data = load_user_data()
    balance = user_data[user_id].get("balance", 0)
    cost = call.data.split('_')[1]
    bonuses = load_bonuses()
    bonus = bonuses["bonuses"][cost]

    if int(cost) <= balance and bonus["codes"]:
        selected_code = random.choice(bonus["codes"])
        bonus["codes"].remove(selected_code)  # Удалить код из списка доступных кодов
        save_bonuses(bonuses)  # Сохранить обновленные данные о бонусах

        user_data[user_id]["balance"] -= int(cost)
        user_data[user_id].setdefault("received_bonuses", []).append(selected_code)
        save_user_data(user_data)
        
        bot.answer_callback_query(call.id, f"Вы получили: {selected_code}")
    else:
        bot.answer_callback_query(call.id, "Недостаточно баллов или коды закончились")

def handle_my_bonuses(message, bot):
    user_id = str(message.chat.id)
    user_data = load_user_data()
    if user_id in user_data and "received_bonuses" in user_data[user_id]:
        bonuses_info = "\n".join(user_data[user_id]["received_bonuses"])
        bot.send_message(user_id, f"Ваши полученные бонусы:\n{bonuses_info}")
    else:
        bot.send_message(user_id, "У вас пока нет полученных бонусов.")


def show_menu(message, bot):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(
        types.KeyboardButton("Ваш реферальный код"),
        types.KeyboardButton("Ввести реферальный код"),
        types.KeyboardButton("Ваш баланс"),
        types.KeyboardButton("Бонусы"),
        types.KeyboardButton("Мои бонусы")  # Новая кнопка
    )
    bot.send_message(message.chat.id, "Выберите опцию:", reply_markup=markup)


def load_bonuses():
    try:
        with open("bonuses.json", "r", encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        bonuses = {
            "bonuses": {
                "5": {"description": "Скидка 5% на следующую покупку", "codes": []},
                "10": {"description": "Бесплатная доставка", "codes": []},
                "20": {"description": "Подарочный сертификат на 500 рублей", "codes": []}
            }
        }
        with open("bonuses.json", "w", encoding='utf-8') as file:
            json.dump(bonuses, file, ensure_ascii=False, indent=4)
        return bonuses

def save_bonuses(data):
    with open("bonuses.json", "w", encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def load_user_data():
    try:
        with open("user_data.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_user_data(data):
    with open("user_data.json", "w") as file:
        json.dump(data, file, indent=4)
