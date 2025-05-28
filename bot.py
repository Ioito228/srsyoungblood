import telebot
import sqlite3

BOT_TOKEN = '7747575425:AAGs7v5mRHLovz4kn-DMMmp6g3sLrpLBGv4'
bot = telebot.TeleBot(BOT_TOKEN)
ADMIN_ID = 1010301976
DB_FILE = 'users.db'


def create_connection():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            telegram_id INTEGER UNIQUE,
            name TEXT,
            city TEXT,
            sport TEXT,
            age INTEGER,
            concerts TEXT,
            reason TEXT,
            abilities TEXT,
            about TEXT,
            contact TEXT
        )
    ''')
    conn.commit()
    return conn


@bot.message_handler(commands=['start'])
def start_command(message):
    conn = create_connection()
    cursor = conn.cursor()
    telegram_id = message.from_user.id

    try:
        cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        existing_user = cursor.fetchone()

        if existing_user:
            bot.send_message(message.chat.id, f"Привет, {existing_user[2]} из {existing_user[3]}! Кажется, я тебя уже знаю. Если хочешь изменить данные, используй команду /update_info.")
        else:
            msg = bot.send_message(message.chat.id, 'Привет! Заполни заявку на вступление в "Young Blood" Как тебя зовут?')
            bot.register_next_step_handler(msg, get_name)

    except Exception as e:
        bot.send_message(message.chat.id, f"Произошла ошибка: {e}")
    finally:
        conn.close()


def get_name(message):
    try:
        telegram_id = message.from_user.id
        name = message.text
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (telegram_id, name) VALUES (?, ?)", (telegram_id, name))
        conn.commit()
        msg = bot.send_message(message.chat.id, f"Приятно познакомиться, {name}! Из какого ты города?")
        bot.register_next_step_handler(msg, get_city)
    except sqlite3.IntegrityError:
        bot.send_message(
            message.chat.id, "Кажется, я тебя уже знаю. Если хочешь изменить данные, используй команду /update_info.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Произошла ошибка: {e}")
    finally:
        conn.close()


def get_data(message, field_name, next_function, question):
    try:
        telegram_id = message.from_user.id
        data = message.text
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute(f"UPDATE users SET {field_name} = ? WHERE telegram_id = ?", (data, telegram_id))
        conn.commit()
        msg = bot.send_message(message.chat.id, question)
        bot.register_next_step_handler(msg, next_function)
    except Exception as e:
        bot.send_message(message.chat.id, f"Произошла ошибка: {e}")
    finally:
        conn.close()

# Цепочка вызовов функций get_data
def get_city(message):
    get_data(message, "city", get_sport, "Каким спортом ты занимался?")

def get_sport(message):
    get_data(message, "sport", get_age, "Твой возраст, вес, рост.")

def get_age(message):
    get_data(message, "age", get_concerts, "На каких концертах ты присутствовал?")

def get_concerts(message):
    get_data(message, "concerts", get_reason, "Зачем ты хочешь вступить в команду?")

def get_reason(message):
    get_data(message, "reason", get_abilities, "Что ты умеешь такого, что будет полезно команде?")

def get_abilities(message):
    get_data(message, "abilities", get_about, "Можешь рассказать что-нибудь ещё о себе?")

def get_about(message):
    get_data(message, "about", get_contact, "Оставить ТГ (для связи)")

def get_contact(message):
    get_data(message, "contact", finish, "Твоя анкета отправлена! Если ты нам подходишь,в ближайшее время с тобой свяжутся.")
    try:
        telegram_id = message.from_user.id
        contact = message.text
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET contact = ? WHERE telegram_id = ?", (contact, telegram_id))
        conn.commit()

        # Отправляем уведомление админу
        cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        user_data = cursor.fetchone()

        info_message = f"Новая заявка от пользователя {user_data[2]} (ID: {telegram_id}):\n\n"
        fields = ["Как зовут?", "Из какого  города?", "Каким спортом занимался?", "Возраст, вес, рост.", "На каких концертах присутствовал?", "Зачем  хочешь вступить в команду?", "Что умеешь такого, что будет полезно команде?", "Можешь рассказать что-нибудь ещё о себе?", "Оставить ТГ"]
        for i in range(2, len(user_data)):
            info_message += f"{fields[i - 2]}: {user_data[i]}\n"

        keyboard = telebot.types.InlineKeyboardMarkup()
        accept_button = telebot.types.InlineKeyboardButton("Принять", callback_data=f"accept_{telegram_id}")
        reject_button = telebot.types.InlineKeyboardButton("Отклонить", callback_data=f"reject_{telegram_id}")
        keyboard.add(accept_button, reject_button)

        bot.send_message(ADMIN_ID, info_message, reply_markup=keyboard)
        bot.send_message(message.chat.id,
                         "Спасибо! Я сохранил всю информацию. Ожидайте ответа администратора.")  # изменил сообщение

    except Exception as e:
        bot.send_message(message.chat.id, f"Произошла ошибка: {e}")
    finally:
        conn.close()

def finish(message):
     bot.send_message(message.chat.id, "Если хочешь изменить данные, используй команду /update_info.")



@bot.message_handler(commands=['update_info'])
def update_info_command(message):
    msg = bot.send_message(message.chat.id, "Что вы хотите обновить?\n"
                                              "/name - Имя\n"
                                              "/city - Город\n"
                                              "/sport - спорт\n"
                                              "/age - Возраст\n"
                                              "/concerts - Концерты\n"
                                              "/reason - Причина вступления\n"
                                              "/abilities - Способности\n"
                                              "/about - О себе\n"
                                              "/contact - Контактная информация")



def update_data(message, field_name):
    try:
        telegram_id = message.from_user.id
        data = message.text
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute(f"UPDATE users SET {field_name} = ? WHERE telegram_id = ?", (data, telegram_id))
        conn.commit()
        bot.send_message(message.chat.id, f"{field_name.capitalize()} обновлен(о).")
    except Exception as e:
        bot.send_message(message.chat.id, f"Произошла ошибка: {e}")
    finally:
        conn.close()


@bot.message_handler(commands=['name', 'city', 'sport', 'age', 'concerts', 'reason', 'abilities', 'about', 'contact'])
def update_fields(message):
    field_name = message.text[1:]
    msg = bot.send_message(message.chat.id, f"Введите новое значение для {field_name.capitalize()}:")
    bot.register_next_step_handler(msg, lambda m: update_data(m, field_name))


@bot.message_handler(commands=['show_user_info'])
def show_user_info(message):
    if message.from_user.id == ADMIN_ID:
        try:
            telegram_id = message.text.split()[1]
            conn = create_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
            user_data = cursor.fetchone()

            if user_data:
                # Форматируем вывод информации
                info_message = f"Информация о пользователе {user_data[2]} (ID: {telegram_id}):\n\n"
                fields = ["Как зовут?", "Из какого  города?", "Каким спортом занимался?", "Возраст, вес, рост.", "На каких концертах присутствовал?", "Зачем  хочешь вступить в команду?", "Что умеешь такого, что будет полезно команде?", "Можешь рассказать что-нибудь ещё о себе?", "Оставить ТГ"]
                for i in range(2, len(user_data)):
                    info_message += f"{fields[i-2]}: {user_data[i]}\n"

                bot.send_message(ADMIN_ID, info_message)

            else:
                bot.send_message(ADMIN_ID, f"Пользователь с ID {telegram_id} не найден.")

        except (IndexError, TypeError):
            bot.send_message(ADMIN_ID, "Введите команду в формате /show_user_info <telegram_id>")
        except Exception as e:
            bot.send_message(ADMIN_ID, f"Произошла ошибка: {e}")
        finally:
            conn.close()
    else:
        bot.send_message(message.chat.id, "У вас нет прав доступа к этой команде.")
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.message:
        if call.data.startswith("accept_"):
            telegram_id = int(call.data.split("_")[1])
            try:
                bot.send_message(telegram_id, "Заявка принята. Добро пожаловать в команду, скоро с вами свяжутся!")
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Заявка принята!")
            except telebot.apihelper.ApiException as e:
                if e.result_json['description'] == 'Forbidden: bot was blocked by the user':
                    bot.send_message(ADMIN_ID, f'Пользователь {telegram_id} заблокировал бота, сообщите ему лично')
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Заявка принята, но пользователь заблокировал бота.")
                else:
                    bot.send_message(ADMIN_ID, f'Ошибка при отправке сообщения: {e}')

        elif call.data.startswith("reject_"):
            telegram_id = int(call.data.split("_")[1])
            try:
                bot.send_message(telegram_id, "Ваша заявка отклонена.")
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Заявка отклонена.")
            except telebot.apihelper.ApiException as e:
                if e.result_json['description'] == 'Forbidden: bot was blocked by the user':
                    bot.send_message(ADMIN_ID, f'Пользователь {telegram_id} заблокировал бота, сообщите ему лично')
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Заявка отклонена, но пользователь заблокировал бота.")
                else:
                    bot.send_message(ADMIN_ID, f'Ошибка при отправке сообщения: {e}')





bot.infinity_polling()