import os
import json
import telebot
from telebot import types
from dotenv import load_dotenv

load_dotenv()

# --- НАСТРОЙКИ ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

bot = telebot.TeleBot(BOT_TOKEN)

WELCOME_TEXT = (
    "Привет! Я, бот сервера HZMINE. Здесь ты можешь купить донат, "
    "ознакомиться с самой важной информацией для игры на сервере, "
    "подать заявку на вступление, а также заглянуть в нашу Вики по предметам!"
)

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
    "3. Опыт игры (сколько лет, на каких серверах):\n"
    "4. Почему хочешь играть именно у нас?\n"
    "5. Твой Telegram для связи:\n\n"
    "👉 **Ответь на это сообщение (Reply) своим заполненным текстом**, и я перешлю его администрации."
)

def load_wiki():
    try:
        with open('wiki.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Ошибка чтения вики: {e}")
        return None

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
    try:
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

        # --- ЛОГИКА ВИКИ ---
        elif call.data == "open_wiki":
            bot.answer_callback_query(call.id)
            wiki_data = load_wiki()
            
            if not isinstance(wiki_data, dict):
                bot.send_message(call.message.chat.id, "⚠️ Ошибка: Файл Вики не найден или поврежден.")
                return

            markup = types.InlineKeyboardMarkup(row_width=1)
            # Передаем индекс раздела (0, 1, 2...), чтобы не превышать лимит символов
            for i, pack_name in enumerate(wiki_data.keys()):
                btn = types.InlineKeyboardButton(pack_name, callback_data=f"wpk_{i}", style="primary")
                markup.add(btn)
            
            markup.add(types.InlineKeyboardButton("⬅️ Назад в меню", callback_data="wiki_back", style="primary"))
            
            bot.edit_message_text("📚 **Выбери датапак/мод:**", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup, parse_mode='Markdown')

        elif call.data.startswith("wpk_"):
            pack_idx = int(call.data.replace("wpk_", ""))
            wiki_data = load_wiki()
            pack_names = list(wiki_data.keys())
            
            if pack_idx < len(pack_names):
                pack_name = pack_names[pack_idx]
                
                markup = types.InlineKeyboardMarkup(row_width=1)
                # Передаем индексы раздела и предмета (например, wpi_2_5)
                for j, item_name in enumerate(wiki_data[pack_name].keys()):
                    btn = types.InlineKeyboardButton(item_name, callback_data=f"wpi_{pack_idx}_{j}", style="primary")
                    markup.add(btn)
                
                markup.add(types.InlineKeyboardButton("⬅️ К разделам", callback_data="open_wiki", style="primary"))
                
                bot.answer_callback_query(call.id)
                bot.edit_message_text(f"📦 **Раздел: {pack_name}**\nВыбери предмет:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup, parse_mode='Markdown')

        elif call.data.startswith("wpi_"):
            parts = call.data.replace("wpi_", "").split("_")
            pack_idx = int(parts[0])
            item_idx = int(parts[1])
            
            wiki_data = load_wiki()
            pack_names = list(wiki_data.keys())
            
            if pack_idx < len(pack_names):
                pack_name = pack_names[pack_idx]
                item_names = list(wiki_data[pack_name].keys())
                
                if item_idx < len(item_names):
                    item_name = item_names[item_idx]
                    item_info = wiki_data[pack_name][item_name]
                    
                    desc = item_info.get("desc", "Нет описания.")
                    craft = item_info.get("craft", "Нет информации о крафте.")
                    image_name = item_info.get("image", "")
                    
                    text = (
                        f"📦 **{pack_name}** | 🛠 **{item_name}**\n\n"
                        f"📝 **Описание:**\n{desc}\n\n"
                        f"⚒ **Как получить/крафт:**\n{craft}"
                    )
                    
                    markup = types.InlineKeyboardMarkup(row_width=1)
                    markup.add(types.InlineKeyboardButton("⬅️ Назад к предметам", callback_data=f"wpk_{pack_idx}", style="primary"))
                    
                    bot.answer_callback_query(call.id)
                    
                    # Безопасная отправка картинки (если она есть)
                    photo_path = os.path.join("images", image_name)
                    if image_name and os.path.exists(photo_path):
                        try:
                            with open(photo_path, 'rb') as photo:
                                bot.send_photo(chat_id=call.message.chat.id, photo=photo, caption=text, reply_markup=markup, parse_mode='Markdown')
                            bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                        except Exception:
                            bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup, parse_mode='Markdown')
                    else:
                        bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup, parse_mode='Markdown')

        elif call.data == "wiki_back":
            bot.answer_callback_query(call.id)
            bot.edit_message_text(WELCOME_TEXT, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=get_main_keyboard(), parse_mode='Markdown')

    except telebot.apihelper.ApiTelegramException as e:
        if "message is not modified" not in str(e).lower():
            print(f"Ошибка Telegram API: {e}")

def forward_application(message):
    if message.reply_to_message:
        user = message.from_user
        username = f"@{user.username}" if user.username else "нет username"

        admin_text = (
            f"📨 **Новая заявка!**\n\n"
            f"От: {user.first_name} ({username})\n"
            f"ID: `{user.id}`\n\n"
            f"**Текст заявки:**\n{message.text}"
        )

        try:
            bot.send_message(ADMIN_ID, admin_text, parse_mode='Markdown')
            bot.send_message(message.chat.id, "✅ Твоя заявка отправлена администрации. Ожидай ответа!")
        except Exception as e:
            bot.send_message(message.chat.id, "❌ Не удалось отправить заявку. Попробуй позже.")
    else:
        bot.send_message(message.chat.id, "⚠️ Пожалуйста, ответь (Reply) именно на сообщение с примером заявки, чтобы я мог её переслать.")

if __name__ == '__main__':
    if not BOT_TOKEN:
        print("ОШИБКА: Не найден BOT_TOKEN.")
    else:
        print("Бот запущен...")
        bot.infinity_polling()
