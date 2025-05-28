import telebot
import sqlite3


ADMIN_ID = 1010301976
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
                fields = ["Имя", "Город", "Спорт", "Возраст", "Концерты", "Причина вступления", "Способности", "О себе", "Контакт"]
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




bot.infinity_polling()