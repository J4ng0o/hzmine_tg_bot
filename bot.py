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

# --- ТЕКСТЫ ---
WELCOME_TEXT = (
    "Привет! Я, бот сервера HZMINE. Здесь ты можешь купить донат, "
    "ознакомиться с самой важной информацией для игры на сервере, "
    "подать заявку на вступление, а также заглянуть в нашу Вики по предметам!"
)

RULES_TEXT = (
    "◦ **Как попасть на сервер?**\n\n"
    "Первым делом стоит подать заявку на вступление. Сделать это можно прямо здесь, в этом же боте.\n"
    "После отправки заявки дождитесь её рассмотрения. С вами свяжутся, либо сразу добавят в конфу сервера.\n"
    "Как только вы окажетесь в беседе, обязательно ознакомьтесь с правилами. При желании можно установить моды. "
    "Всю необходимую информацию — версию и IP сервера — вы найдете в канале «Важная инфа».\n\n"
    "◦ **Что делать дальше?**\n\n"
    "Начинать на любом SMP-сервере стоит не с гонки за ресурсами, а с адаптации к сообществу. "
    "Мир уже обжит другими игроками, поэтому ваша главная задача в первые часы - не потеряться, "
    "не нарушить чужие границы и понять, как здесь всё устроено.\n"
    "Чтобы освоиться, вы можете:\n"
    "• Пообщаться с игроками в чате или войсчате;\n"
    "• Прогуляться по спавну и осмотреться.\n\n"
    "Механики на сервере в основном интуитивные. Но если возникнут вопросы - не стесняйтесь "
    "заглядывать в вики в этом же боте или просто обращаться за помощью к другим игрокам."
)

APPLICATION_EXAMPLE = (
    "📝 **Пример заявки:**\n\n"
    "1. Ваш никнейм:\n"
    "2. Некоторые пожелания или цели игры на сервере:\n"
    "3. Опыт игры на подобных SMP серверах (если есть):\n"
    "4. Почему хочешь играть именно у нас?\n"
    "**Ответь на это сообщение (Reply) своим заполненным текстом**, и я перешлю его администрации."
)

# --- ФУНКЦИИ ---
def load_wiki():
    try:
        with open('wiki.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def get_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("HZMINE+", callback_data="donate"))
    markup.add(types.InlineKeyboardButton("С чего начать?", callback_data="start_guide"))
    markup.add(types.InlineKeyboardButton("Вики", callback_data="open_wiki"))
    markup.add(types.InlineKeyboardButton("Подать заявку", callback_data="apply"))
    return markup

@bot.message_handler(commands=['start'])
def start_message(message):
    photo_path = os.path.join("images", "welcome.png") 

    if os.path.exists(photo_path):
        with open(photo_path, 'rb') as photo:
            bot.send_photo(
                chat_id=message.chat.id, 
                photo=photo, 
                caption=WELCOME_TEXT, 
                reply_markup=get_main_keyboard()
            )
    else:
        bot.send_message(message.chat.id, WELCOME_TEXT, reply_markup=get_main_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "donate":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "Приобрести HZMINE+ можно по ссылке:\n    https://hzmine.millida.trade")

    elif call.data == "start_guide":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, RULES_TEXT, parse_mode='Markdown', disable_web_page_preview=False)

    elif call.data == "apply":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, APPLICATION_EXAMPLE, parse_mode='Markdown')
        bot.register_next_step_handler(msg, forward_application)

    elif call.data == "open_wiki":
        bot.answer_callback_query(call.id)
        wiki_data = load_wiki()
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        for i, pack_name in enumerate(wiki_data.keys()):
            markup.add(types.InlineKeyboardButton(pack_name, callback_data=f"wpk_{i}"))
        
        markup.add(types.InlineKeyboardButton("⬅️ Назад в меню", callback_data="wiki_back"))
        bot.edit_message_text("📚 **Выбери датапак/мод:**", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup, parse_mode='Markdown')

    elif call.data.startswith("wpk_"):
        pack_idx = int(call.data.replace("wpk_", ""))
        wiki_data = load_wiki()
        pack_names = list(wiki_data.keys())
        
        if pack_idx < len(pack_names):
            pack_name = pack_names[pack_idx]
            markup = types.InlineKeyboardMarkup(row_width=1)
            
            for j, item_name in enumerate(wiki_data[pack_name].keys()):
                markup.add(types.InlineKeyboardButton(item_name, callback_data=f"wpi_{pack_idx}_{j}"))
            
            markup.add(types.InlineKeyboardButton("⬅️ К разделам", callback_data="open_wiki"))
            bot.answer_callback_query(call.id)
            bot.edit_message_text(f"📦 **Раздел: {pack_name}**\nВыбери предмет:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup, parse_mode='Markdown')

    elif call.data.startswith("wpi_"):
        parts = call.data.replace("wpi_", "").split("_")
        pack_idx, item_idx = int(parts[0]), int(parts[1])
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
                
                text = f"📦 **{pack_name}** | 🛠 **{item_name}**\n\n📝 **Описание:**\n{desc}\n\n⚒ **Как получить/крафт:**\n{craft}"
                
                markup = types.InlineKeyboardMarkup(row_width=1)
                markup.add(types.InlineKeyboardButton("⬅️ Назад к предметам", callback_data=f"wpk_{pack_idx}"))
                bot.answer_callback_query(call.id)
                
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

def forward_application(message):
    if message.reply_to_message:
        user = message.from_user
        username = f"@{user.username}" if user.username else "нет username"
        admin_text = f"📨 **Новая заявка!**\n\nОт: {user.first_name} ({username})\nID: `{user.id}`\n\n**Текст заявки:**\n{message.text}"
        
        try:
            bot.send_message(ADMIN_ID, admin_text, parse_mode='Markdown')
            bot.send_message(message.chat.id, "✅ Твоя заявка отправлена администрации. Ожидай ответа!")
        except Exception:
            bot.send_message(message.chat.id, "❌ Не удалось отправить заявку. Попробуй позже.")
    else:
        bot.send_message(message.chat.id, "⚠️ Пожалуйста, ответь (Reply) именно на сообщение с примером заявки.")

# --- ЗАПУСК ---
if __name__ == '__main__':
    print("Бот запущен...")
    bot.infinity_polling()
