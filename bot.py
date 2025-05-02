import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler

# Токен от BotFather
TOKEN = '7722308657:AAFtXDvLCWg0v107SGtqbBTwPXlhFuU0jOU'

# Настройка логов
logging.basicConfig(level=logging.INFO)

# Состояния
ASKING, ANSWERING = range(2)

# Хранилище тестов
tests = []
user_data = {}

def parse_test_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read().strip().split('\n\n')
    questions = []
    for block in content:
        lines = block.strip().split('\n')
        if not lines:
            continue
        q_text = lines[0].replace('ВОПРОС:', '').strip()
        options = [line for line in lines if line.startswith(('а)', 'б)', 'в)', 'г)'))]
        answer_line = next((line for line in lines if line.startswith('ОТВЕТ:')), None)
        answer = answer_line.replace('ОТВЕТ:', '').strip() if answer_line else '?'
        questions.append({'question': q_text, 'options': options, 'answer': answer})
    return questions

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Привет! Пришли мне файл с тестами в формате .txt.")

def handle_text_file(update: Update, context: CallbackContext):
    file = update.message.document.get_file()
    file_path = f"{file.file_id}.txt"
    file.download(file_path)

    global tests
    tests = parse_test_file(file_path)
    user_data[update.effective_user.id] = {'index': 0, 'score': 0}

    update.message.reply_text("Файл получен! Начинаем тест.")
    return ask_question(update, context)

def ask_question(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    data = user_data.get(user_id)
    if data['index'] >= len(tests):
        score = data['score']
        update.message.reply_text(f"Тест завершён. Ты правильно ответил(а) на {score} из {len(tests)}.")
        return ConversationHandler.END

    current = tests[data['index']]
    reply_markup = ReplyKeyboardMarkup(
        [[opt[:1] for opt in current['options']]], one_time_keyboard=True, resize_keyboard=True
    )
    question_text = f"{current['question']}\n" + "\n".join(current['options'])
    update.message.reply_text(question_text, reply_markup=reply_markup)
    return ANSWERING

def handle_answer(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    data = user_data.get(user_id)
    current = tests[data['index']]
    user_answer = update.message.text.strip().lower()
    correct = current['answer'].lower()

    if user_answer == correct:
        update.message.reply_text("Правильно!")
        data['score'] += 1
    else:
        update.message.reply_text(f"Неправильно. Правильный ответ: {correct}")

    data['index'] += 1
    return ask_question(update, context)

def cancel(update: Update, context: CallbackContext):
    update.message.reply_text("Тестирование отменено.")
    return ConversationHandler.END

def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.document.mime_type("text/plain"), handle_text_file)],
        states={
            ASKING: [MessageHandler(Filters.text & ~Filters.command, ask_question)],
            ANSWERING: [MessageHandler(Filters.text & ~Filters.command, handle_answer)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
