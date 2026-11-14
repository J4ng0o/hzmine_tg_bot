import os
import json
import telebot
from telebot import types
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

bot = telebot.TeleBot(BOT_TOKEN)

WELCOME_TEXT = (
    "Привет! Я, бот сервера HZMINE. Здесь ты можешь купить HZMINE+, "
    "ознакомиться с самой важной информацией для игры на сервере, "
    "подать заявку на вступление, а так же узнать с чего начать!"
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


def get_wiki():
    try:
        with open('wiki.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("HZMINE+", callback_data="donate"),
        types.InlineKeyboardButton("С чего начать?", callback_data="start_guide"),
        types.InlineKeyboardButton("Вики", callback_data="wiki"),
        types.InlineKeyboardButton("Подать заявку", callback_data="apply")
    )
    return markup


@bot.message_handler(commands=['start'])
def start_cmd(message):
    photo = os.path.join("images", "welcome.png")
    if os.path.exists(photo):
        with open(photo, 'rb') as f:
            bot.send_photo(message.chat.id, f, caption=WELCOME_TEXT, reply_markup=main_menu())
    else:
        bot.send_message(message.chat.id, WELCOME_TEXT, reply_markup=main_menu())


@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    if call.data == "donate":
        photo = os.path.join("images", "donate.png")
        text = "Приобрести HZMINE+ можно [тут](https://hzmine.millida.trade)"
        if os.path.exists(photo):
            with open(photo, 'rb') as f:
                bot.send_photo(call.message.chat.id, f, caption=text, parse_mode='Markdown')
        else:
            bot.send_message(call.message.chat.id, text, parse_mode='Markdown')

    elif call.data == "start_guide":
        bot.send_message(call.message.chat.id, RULES_TEXT, parse_mode='Markdown')
        
    elif call.data == "apply":
        msg = bot.send_message(call.message.chat.id, APPLICATION_EXAMPLE, parse_mode='Markdown')
        bot.register_next_step_handler(msg, process_application)

    elif call.data == "wiki":
        data = get_wiki()
        if not data:
            bot.answer_callback_query(call.id, "Вики пуста.")
            return
            
        markup = types.InlineKeyboardMarkup(row_width=1)
        for i, pack in enumerate(data.keys()):
            markup.add(types.InlineKeyboardButton(pack, callback_data=f"wp_{i}"))
        markup.add(types.InlineKeyboardButton("Назад", callback_data="back"))
        
        bot.edit_message_text("Выбери датапак/плагин:", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data.startswith("wp_"):
        data = get_wiki()
        pack_idx = int(call.data.replace("wp_", ""))
        pack_name = list(data.keys())[pack_idx]
        section = data[pack_name]
        
        first_key = list(section.keys())[0] if section else None
        is_sub = isinstance(section.get(first_key), dict) if first_key else False
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        if is_sub:
            for i, sub in enumerate(section.keys()):
                markup.add(types.InlineKeyboardButton(sub, callback_data=f"ws_{pack_idx}_{i}"))
            markup.add(types.InlineKeyboardButton("Назад", callback_data="wiki"))
            bot.edit_message_text(f"{pack_name}\nВыбери раздел:", call.message.chat.id, call.message.message_id, reply_markup=markup)
        else:
            for i, item in enumerate(section.keys()):
                markup.add(types.InlineKeyboardButton(item, callback_data=f"wi_{pack_idx}_{i}"))
            markup.add(types.InlineKeyboardButton("Назад", callback_data="wiki"))
            bot.edit_message_text(f"{pack_name}\nВыбери предмет:", call.message.chat.id, call.message.message_id, reply_markup=markup)
            
        bot.answer_callback_query(call.id)

    elif call.data.startswith("ws_"):
        data = get_wiki()
        _, p_idx, s_idx = call.data.split("_")
        p_idx, s_idx = int(p_idx), int(s_idx)
        
        pack_name = list(data.keys())[p_idx]
        sub_name = list(data[pack_name].keys())[s_idx]
        sub_section = data[pack_name][sub_name]
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        for i, item in enumerate(sub_section.keys()):
            markup.add(types.InlineKeyboardButton(item, callback_data=f"wi_{p_idx}_{s_idx}_{i}"))
        markup.add(types.InlineKeyboardButton("Назад", callback_data=f"wp_{p_idx}"))
        
        bot.edit_message_text(f"{pack_name} | {sub_name}\nВыбери предмет:", call.message.chat.id, call.message.message_id, reply_markup=markup)
        bot.answer_callback_query(call.id)

    elif call.data.startswith("wi_"):
        data = get_wiki()
        parts = call.data.split("_")[1:]
        
        if len(parts) == 2:
            p_idx, i_idx = int(parts[0]), int(parts[1])
            s_idx = None
        else:
            p_idx, s_idx, i_idx = int(parts[0]), int(parts[1]), int(parts[2])
            
        pack_name = list(data.keys())[p_idx]
        
        if s_idx is not None:
            sub_name = list(data[pack_name].keys())[s_idx]
            item_name = list(data[pack_name][sub_name].keys())[i_idx]
            item = data[pack_name][sub_name][item_name]
            back = f"ws_{p_idx}_{s_idx}"
            title = f"{pack_name} | {sub_name} | {item_name}"
        else:
            item_name = list(data[pack_name].keys())[i_idx]
            item = data[pack_name][item_name]
            back = f"wp_{p_idx}"
            title = f"{pack_name} | {item_name}"
            
        text = f"{title}\n\nОписание:\n{item.get('desc', '-')}\n\nКрафт:\n{item.get('craft', '-')}"
        markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("Назад", callback_data=back))
        
        photo = os.path.join("images", item.get("image", ""))
        if item.get("image") and os.path.exists(photo):
            with open(photo, 'rb') as f:
                bot.send_photo(call.message.chat.id, f, caption=text, reply_markup=markup)
            bot.delete_message(call.message.chat.id, call.message.message_id)
        else:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
            
        bot.answer_callback_query(call.id)

    elif call.data == "back":
        photo = os.path.join("images", "welcome.png")
        if os.path.exists(photo):
            with open(photo, 'rb') as f:
                bot.send_photo(call.message.chat.id, f, caption=WELCOME_TEXT, reply_markup=main_menu())
            bot.delete_message(call.message.chat.id, call.message.message_id)
        else:
            bot.edit_message_text(WELCOME_TEXT, call.message.chat.id, call.message.message_id, reply_markup=main_menu())
        bot.answer_callback_query(call.id)


def process_application(message):
    if not message.reply_to_message:
        bot.send_message(message.chat.id, "Ответь на сообщение с примером заявки.")
        return

    user = message.from_user
    username = f"@{user.username}" if user.username else "нет username"
    
    admin_text = (
        f"Новая заявка!\n\n"
        f"От: {user.first_name} ({username})\n"
        f"ID: {user.id}\n\n"
        f"Текст заявки:\n{message.text}"
    )
    
    try:
        bot.send_message(ADMIN_ID, admin_text)
        bot.send_message(message.chat.id, "Заявка отправлена.")
    except Exception:
        bot.send_message(message.chat.id, "Ошибка отправки. Попробуй позже.")


if __name__ == '__main__':
    bot.infinity_polling()
