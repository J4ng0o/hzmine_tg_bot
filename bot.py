import telebot
from telebot import types

BOT_TOKEN = "7412378342:AAHRXPec0CnkgdaAepRCUsmGOloBYsRZ51k"
ADMIN_ID = 5393418168

bot = telebot.TeleBot(BOT_TOKEN)

WELCOME_TEXT = (
    "Привет! Я, бот сервера HZMINE. Здесь ты можешь ознакомиться со своим профилем, "
    "купить донат, а так же ознакомиться с самой важной информацией, необходимой для игры на сервере."
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

def get_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_profile = types.InlineKeyboardButton("👤 Мой профиль", callback_data="profile", style="primary")
    btn_donate = types.InlineKeyboardButton("💎 HZMINE+", callback_data="donate", style="primary")
    btn_start_guide = types.InlineKeyboardButton("🚀 С чего начать?", callback_data="start_guide", style="primary")
    btn_apply = types.InlineKeyboardButton("📨 Подать заявку", callback_data="apply", style="primary")
    markup.add(btn_profile, btn_donate, btn_start_guide, btn_apply)
    return markup

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, WELCOME_TEXT, reply_markup=get_main_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "profile":
        profile_text = (
            f"👤 **Твой профиль**\n\n"
            f"Никнейм: *не привязан*\n"
            f"Подписка: ❌ Нет\n"
            f"Доступные пины: 0\n\n"
            f"(Чтобы привязать ник, обратитесь к администрации или используйте команду привязки, если она есть)"
        )
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, profile_text, parse_mode='Markdown')

    elif call.data == "donate":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "💎 Приобрести донат можно по ссылке:\nhttps://hzmine.millida.trade")

    elif call.data == "start_guide":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, RULES_TEXT, parse_mode='Markdown', disable_web_page_preview=False)

    elif call.data == "apply":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, APPLICATION_EXAMPLE, parse_mode='Markdown')
        bot.register_next_step_handler(msg, forward_application)


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
            print(f"Ошибка отправки админу: {e}")
    else:
        bot.send_message(message.chat.id, "⚠️ Пожалуйста, ответь (Reply) именно на сообщение с примером заявки, чтобы я мог её переслать.")

if __name__ == '__main__':
    print("Бот запущен...")
    bot.infinity_polling()
