import os
import json
import telebot
from telebot import types
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
bot = telebot.TeleBot(BOT_TOKEN)

WELCOME_TEXT = "Привет! Я, бот сервера HZMINE. Здесь ты можешь купить донат, ознакомиться с информацией, подать заявку, а также заглянуть в нашу Вики!"

RULES_TEXT = (
    "📜 **Краткая памятка для игроков**\n\n"
    "◦ 6.1. Обидели - подай иск в суд или урегулируй конфликт словами, не мсти сам.\n"
    "◦ 6.2. Вызвали в суд - явись, иначе штраф и заочный приговор.\n"
    "◦ 6.3. Проиграл суд - исполни приговор, иначе Гвардия.\n"
    "◦ 6.4. Долго не исполняешь - администрация может забанить.\n"
    "◦ 6.5. Твинки, лаг-машины, читы и прочий ширпотреб - бан без суда.\n\n"
    "📖 Пожалуйста, ознакомься с полными правилами сервера.\n"
    "🔗 [Группа сервера в Telegram](https://t.me/+t7H-lnggVsQyYjMy)"
)

APPLICATION_EXAMPLE = (
    "📝 **Пример заявки:**\n\n"
    "1. Твой Minecraft ник:\n"
    "2. Возраст:\n"
    "3. Опыт игры:\n"
    "4. Почему хочешь играть у нас?\n"
    "5. Твой Telegram для связи:\n\n"
    "👉 **Ответь на это сообщение (Reply) своим заполненным текстом**, и я перешлю его администрации."
)

def load_wiki():
    try:
        with open('wiki.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return "ERROR_FILE_NOT_FOUND"
    except json.JSONDecodeError as e:
        return f"ERROR_JSON: {e}"
    except Exception as e:
        return f"ERROR_UNKNOWN: {e}"

def get_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("💎 HZMINE+", callback_data="donate", style="primary"))
    markup.add(types.InlineKeyboardButton("🚀 С чего начать?", callback_data="start_guide", style="primary"))
    markup.add(types.InlineKeyboardButton("📚 Вики", callback_data="open_wiki", style="primary"))
    markup.add(types.InlineKeyboardButton("📨 Подать заявку", callback_data="apply", style="primary"))
    return markup

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, WELCOME_TEXT, reply_markup=get_main_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "donate":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "💎 Приобрести донат можно по ссылке:\nhttps://hzmine.millida.trade")

    elif call.data == "start_guide":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, RULES_TEXT, parse_mode='Markdown', disable_web_page_preview=False)

    elif call.data == "apply":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, APPLICATION_EXAMPLE, parse_mode='Markdown')
        bot.register_next_step_handler(msg, forward_application)

    elif call.data == "open_wiki":
        # Отправляем ответ, чтобы убрать часики
        bot.answer_callback_query(call.id)
        
        # Читаем файл
        wiki_data = load_wiki()
        
        # Проверяем, что вернулось
        if wiki_data == "ERROR_FILE_NOT_FOUND":
            bot.send_message(call.message.chat.id, "⚠️ ТЕСТ: Бот не может найти файл `wiki.json` в папке!")
            return
        elif isinstance(wiki_data, str) and wiki_data.startswith("ERROR"):
            bot.send_message(call.message.chat.id, f"⚠️ ТЕСТ: Ошибка в файле:\n{wiki_data}")
            return
        
        # Если дошли сюда - файл прочитан успешно
        try:
            markup = types.InlineKeyboardMarkup(row_width=1)
            for pack_name in wiki_data.keys():
                btn = types.InlineKeyboardButton(pack_name, callback_data=f"wiki_pack_{pack_name}", style="primary")
                markup.add(btn)
            
            markup.add(types.InlineKeyboardButton("⬅️ Назад в меню", callback_data="wiki_back", style="primary"))
            
            bot.edit_message_text("📚 **Выбери датапак/мод:**", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup, parse_mode='Markdown')
            
        except Exception as e:
            # Если произошла ошибка при построении кнопок, пишем в телеграм!
            bot.send_message(call.message.chat.id, f"⚠️ ТЕСТ: Ошибка при создании кнопок:\n{type(e).__name__}: {e}")

    elif call.data.startswith("wiki_pack_"):
        pack_name = call.data.replace("wiki_pack_", "")
        wiki_data = load_wiki()
        
        if isinstance(wiki_data, dict) and pack_name in wiki_data:
            markup = types.InlineKeyboardMarkup(row_width=1)
            for item_name in wiki_data[pack_name].keys():
                btn = types.InlineKeyboardButton(item_name, callback_data=f"wiki_item_{pack_name}|{item_name}", style="primary")
                markup.add(btn)
            
            markup.add(types.InlineKeyboardButton("⬅️ К разделам", callback_data="open_wiki", style="primary"))
            
            bot.answer_callback_query(call.id)
            bot.edit_message_text(f"📦 **Раздел: {pack_name}**\nВыбери предмет:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup, parse_mode='Markdown')

    elif call.data.startswith("wiki_item_"):
        data = call.data.replace("wiki_item_", "")
        pack_name, item_name = data.split("|", 1)
        
        wiki_data = load_wiki()
        if isinstance(wiki_data, dict) and pack_name in wiki_data and item_name in wiki_data[pack_name]:
            item_info = wiki_data[pack_name][item_name]
            desc = item_info.get("desc", "Нет описания.")
            craft = item_info.get("craft", "Нет информации о крафте.")
            
            text = f"📦 **{pack_name}** | 🛠 **{item_name}**\n\n📝 **Описание:**\n{desc}\n\n⚒ **Как получить/крафт:**\n{craft}"
            
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(types.InlineKeyboardButton("⬅️ Назад к предметам", callback_data=f"wiki_pack_{pack_name}", style="primary"))
            
            bot.answer_callback_query(call.id)
            bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup, parse_mode='Markdown')

    elif call.data == "wiki_back":
        bot.answer_callback_query(call.id)
        bot.edit_message_text(WELCOME_TEXT, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=get_main_keyboard(), parse_mode='Markdown')

def forward_application(message):
    if message.reply_to_message:
        user = message.from_user
        username = f"@{user.username}" if user.username else "нет username"
        admin_text = f"📨 **Новая заявка!**\n\nОт: {user.first_name} ({username})\nID: `{user.id}`\n\n**Текст заявки:**\n{message.text}"
        try:
            bot.send_message(ADMIN_ID, admin_text, parse_mode='Markdown')
            bot.send_message(message.chat.id, "✅ Твоя заявка отправлена администрации. Ожидай ответа!")
        except Exception as e:
            bot.send_message(message.chat.id, "❌ Не удалось отправить заявку. Попробуй позже.")
    else:
        bot.send_message(message.chat.id, "⚠️ Пожалуйста, ответь (Reply) именно на сообщение с примером заявки.")

if __name__ == '__main__':
    if not BOT_TOKEN:
        print("ОШИБКА: Не найден BOT_TOKEN.")
    else:
        print("Бот запущен...")
        bot.infinity_polling()
