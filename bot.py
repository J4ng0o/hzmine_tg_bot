import os
import json
import telebot
from telebot import types
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID_RAW = os.getenv("ADMIN_ID", "0")

try:
    ADMIN_ID = int(ADMIN_ID_RAW)
except (TypeError, ValueError):
    print(f"!!! ADMIN_ID некорректен: {ADMIN_ID_RAW!r}, использую 0")
    ADMIN_ID = 0

print(f"DEBUG: BOT_TOKEN set={bool(BOT_TOKEN)}, ADMIN_ID={ADMIN_ID}")

bot = telebot.TeleBot(BOT_TOKEN)

# Множество chat_id, которые сейчас в процессе подачи заявки
waiting_for_application = set()

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
    "Всю необходимую информацию - версию и IP сервера - вы найдете в канале «Важная инфа».\n\n"
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
    "4. Почему хочешь играть именно у нас?\n\n"
    "**Отправь следующим сообщением свой заполненный текст.**\n"
    "Или нажми «Отмена», чтобы вернуться в меню."
)


def get_wiki():
    try:
        with open('wiki.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"!!! ОШИБКА ЧТЕНИЯ WIKI.JSON: {repr(e)}")
        return {}


def is_item(value):
    """Предмет — это dict с ключами desc/craft (или image)."""
    return isinstance(value, dict) and ("desc" in value or "craft" in value)


def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("Подать заявку", callback_data="apply"),
        types.InlineKeyboardButton("С чего начать?", callback_data="start_guide"),
        types.InlineKeyboardButton("Вики", callback_data="wiki"),
        types.InlineKeyboardButton("HZMINE+", callback_data="donate")
    )
    return markup


def safe_delete(chat_id, message_id):
    """Безопасное удаление сообщения, чтобы бот не падал, если оно старое."""
    try:
        bot.delete_message(chat_id, message_id)
    except Exception:
        pass


def send_main_menu(chat_id, delete_message_id=None):
    """Отправляет главное меню (с картинкой, если есть) и опционально удаляет старое сообщение."""
    photo = os.path.join("images", "hello.png")
    if os.path.exists(photo):
        with open(photo, 'rb') as f:
            bot.send_photo(chat_id, f, caption=WELCOME_TEXT, reply_markup=main_menu())
    else:
        bot.send_message(chat_id, WELCOME_TEXT, reply_markup=main_menu())
    if delete_message_id:
        safe_delete(chat_id, delete_message_id)


@bot.message_handler(commands=['start'])
def start_cmd(message):
    # Если пользователь в процессе заявки — /start отменяет её
    waiting_for_application.discard(message.chat.id)
    send_main_menu(message.chat.id)


@bot.message_handler(func=lambda m: m.chat.id in waiting_for_application, content_types=['text'])
def process_application(message):
    """Ловит текст заявки, пока пользователь в состоянии ожидания."""
    waiting_for_application.discard(message.chat.id)

    user = message.from_user
    username = f"@{user.username}" if user.username else "нет username"

    admin_text = (
        f"📩 Новая заявка!\n\n"
        f"От: {user.first_name} ({username})\n"
        f"ID: {user.id}\n\n"
        f"Текст заявки:\n{message.text}"
    )

    if ADMIN_ID == 0:
        print("!!! ADMIN_ID = 0 — заявка не отправлена.")
        bot.send_message(
            message.chat.id,
            "⚠️ Администратор не настроен. Сообщи об этом в чате сервера."
        )
        return

    try:
        # Без parse_mode, чтобы символы в тексте заявки не ломали разметку
        bot.send_message(ADMIN_ID, admin_text)
        bot.send_message(message.chat.id, "✅ Заявка отправлена администрации.")
    except Exception as e:
        print(f"!!! ОШИБКА ОТПРАВКИ ЗАЯВКИ: {repr(e)}")
        bot.send_message(message.chat.id, "Ошибка отправки. Попробуй позже.")


@bot.message_handler(
    func=lambda m: m.chat.id in waiting_for_application,
    content_types=['photo', 'video', 'sticker', 'voice', 'document', 'audio']
)
def process_application_wrong_type(message):
    """Если в состоянии заявки пришло не текстовое сообщение — просим текст."""
    bot.send_message(
        message.chat.id,
        "Пожалуйста, отправь заявку текстом. Или нажми «Отмена», чтобы вернуться в меню."
    )


@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    # --- HZMINE+ ---
    if call.data == "donate":
        photo = os.path.join("images", "donate.png")
        text = (
            "Помимо нашей поддержки вы получаете:\n\n"
            "◦ **Команды:** /sit, /lay, /spin, /crawl, /hat, /piss - найди своё место в этом мире\n\n"
            "◦ **Пин HZMINE+** - метка, которая выделит тебя среди других\n\n"
            "◦ **Больше пинов за ивенты** - твой вклад в события заметят\n\n"
            "◦ **Новые инструменты для творчества** - возможность управлять block_display, item_display, манекенами, арморстендами, text_display\n\n"
            "Функционал будет пополняться со временем, но сохранять свою нейтральность и не давать преимущество.\n\n"
            "Приобрести HZMINE+ можно [тут](https://hzmine.millida.trade)"
        )
        markup = types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("Назад", callback_data="back")
        )

        if os.path.exists(photo):
            with open(photo, 'rb') as f:
                bot.send_photo(
                    call.message.chat.id, f, caption=text,
                    parse_mode='Markdown', reply_markup=markup
                )
            safe_delete(call.message.chat.id, call.message.message_id)
        else:
            bot.send_message(
                call.message.chat.id, text,
                parse_mode='Markdown', reply_markup=markup
            )
            safe_delete(call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)

    # --- Подать заявку ---
    elif call.data == "apply":
        markup = types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("Отмена", callback_data="back")
        )
        bot.send_message(call.message.chat.id, APPLICATION_EXAMPLE, parse_mode='Markdown', reply_markup=markup)
        waiting_for_application.add(call.message.chat.id)
        safe_delete(call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)

    # --- Вики (главное меню) ---
    elif call.data == "wiki":
        data = get_wiki()
        if not data:
            bot.answer_callback_query(call.id, "Вики пуста или файл поврежден.")
            return

        markup = types.InlineKeyboardMarkup(row_width=1)
        for i, pack in enumerate(data.keys()):
            markup.add(types.InlineKeyboardButton(pack, callback_data=f"wp_{i}"))
        markup.add(types.InlineKeyboardButton("Назад", callback_data="back"))

        bot.send_message(call.message.chat.id, "Выбери датапак/плагин:", reply_markup=markup)
        safe_delete(call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)

    # --- Вики (выбор раздела/предмета внутри пакета) ---
    elif call.data.startswith("wp_"):
        data = get_wiki()
        try:
            pack_idx = int(call.data.replace("wp_", ""))
            pack_name = list(data.keys())[pack_idx]
            section = data[pack_name]

            first_key = list(section.keys())[0] if section else None
            is_sub = bool(first_key) and not is_item(section[first_key])

            markup = types.InlineKeyboardMarkup(row_width=1)

            if is_sub:
                for i, sub in enumerate(section.keys()):
                    markup.add(types.InlineKeyboardButton(sub, callback_data=f"ws_{pack_idx}_{i}"))
                markup.add(types.InlineKeyboardButton("Назад", callback_data="wiki"))
                text = f"{pack_name}\nВыбери раздел:"
            else:
                for i, item in enumerate(section.keys()):
                    markup.add(types.InlineKeyboardButton(item, callback_data=f"wi_{pack_idx}_{i}"))
                markup.add(types.InlineKeyboardButton("Назад", callback_data="wiki"))
                text = f"{pack_name}\nВыбери предмет:"

            bot.send_message(call.message.chat.id, text, reply_markup=markup)
            safe_delete(call.message.chat.id, call.message.message_id)
        except (IndexError, KeyError, ValueError) as e:
            print(f"!!! ОШИБКА WP CALLBACK {call.data}: {repr(e)}")
            bot.answer_callback_query(call.id, "Ошибка вики.")
            return

        bot.answer_callback_query(call.id)

    # --- Вики (выбор предмета внутри подраздела) ---
    elif call.data.startswith("ws_"):
        data = get_wiki()
        try:
            _, p_idx, s_idx = call.data.split("_")
            p_idx, s_idx = int(p_idx), int(s_idx)

            pack_name = list(data.keys())[p_idx]
            sub_name = list(data[pack_name].keys())[s_idx]
            sub_section = data[pack_name][sub_name]

            if not all(is_item(v) for v in sub_section.values()):
                bot.answer_callback_query(call.id, "Ошибка структуры вики.")
                return

            markup = types.InlineKeyboardMarkup(row_width=1)
            for i, item in enumerate(sub_section.keys()):
                markup.add(types.InlineKeyboardButton(item, callback_data=f"wi_{p_idx}_{s_idx}_{i}"))
            markup.add(types.InlineKeyboardButton("Назад", callback_data=f"wp_{p_idx}"))

            text = f"{pack_name} | {sub_name}\nВыбери предмет:"

            bot.send_message(call.message.chat.id, text, reply_markup=markup)
            safe_delete(call.message.chat.id, call.message.message_id)
        except (IndexError, KeyError, ValueError) as e:
            print(f"!!! ОШИБКА WS CALLBACK {call.data}: {repr(e)}")
            bot.answer_callback_query(call.id, "Ошибка вики.")
            return

        bot.answer_callback_query(call.id)

    # --- Вики (карточка предмета) ---
    elif call.data.startswith("wi_"):
        data = get_wiki()
        try:
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

            if not is_item(item):
                bot.answer_callback_query(call.id, "Это не предмет.")
                return

            text = f"{title}\n\nОписание:\n{item.get('desc', '-')}\n\nКрафт:\n{item.get('craft', '-')}"
            markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("Назад", callback_data=back))

            image_name = item.get("image", "")
            photo = os.path.join("images", image_name) if image_name else None

            if photo and os.path.exists(photo):
                with open(photo, 'rb') as f:
                    bot.send_photo(call.message.chat.id, f, caption=text, reply_markup=markup)
            else:
                bot.send_message(call.message.chat.id, text, reply_markup=markup)

            safe_delete(call.message.chat.id, call.message.message_id)
            bot.answer_callback_query(call.id)

        except (IndexError, KeyError, ValueError) as e:
            print(f"!!! ОШИБКА WI CALLBACK {call.data}: {repr(e)}")
            bot.answer_callback_query(call.id, "Ошибка вики. Попробуй ещё раз.")
            return

    # --- Назад в главное меню / Отмена заявки ---
    elif call.data == "back":
        # Отменяем ожидание заявки, если оно было
        waiting_for_application.discard(call.message.chat.id)
        send_main_menu(call.message.chat.id, delete_message_id=call.message.message_id)
        bot.answer_callback_query(call.id)


if __name__ == '__main__':
    bot.infinity_polling()
