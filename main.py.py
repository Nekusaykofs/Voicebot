import os
import requests
import asyncio
import psycopg2
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from urllib.parse import urlparse

# --- Настройки ---
API_KEY = os.getenv("ELEVEN_API_KEY")  # Задай переменную окружения
VOICE_ID_MASHA = 'EDpEYNf6XIeKYRzYcx4I'  # Маша
VOICE_ID_DENIS = '0BcDz9UPwL3MpsnTeUlO'  # Денис
VOICE_ID_OGE = 'MWyJiWDobXN8FX3CJTdE'    # Олег
VOICE_ID_ANYA = 'rxEz5E7hIAPk7D3bXwf6'   # Аня
API_TOKEN = os.getenv("BOT_TOKEN")       # Токен задаётся через переменные окружения
ADMIN_ID = 6728899517

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# --- База данных PostgreSQL ---
DATABASE_URL = "postgresql://voicebot_user:XwkxGeGZaJPpNIUtR63lyHgaBNPhpdIv@dpg-d0av319r0fns73cv672g-a/voicebot"
url = urlparse(DATABASE_URL)
conn = psycopg2.connect(
    database=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port
)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id BIGINT PRIMARY KEY
    )
''')
conn.commit()

# --- Клавиатуры ---
main_kb = ReplyKeyboardMarkup(resize_keyboard=True)
main_kb.add(
    KeyboardButton("🗣 Озвучить текст"),
    KeyboardButton("🎧 Заменить голос"),
    KeyboardButton("📖 Инструкция")
)

voice_kb = ReplyKeyboardMarkup(resize_keyboard=True)
voice_kb.add(
    KeyboardButton("Маша"),
    KeyboardButton("Денис"),
    KeyboardButton("Олег"),
    KeyboardButton("Аня"),
    KeyboardButton("⬅️ Назад")
)

back_kb = ReplyKeyboardMarkup(resize_keyboard=True)
back_kb.add(KeyboardButton("⬅️ Назад"))

instruction_kb = ReplyKeyboardMarkup(resize_keyboard=True)
instruction_kb.add(KeyboardButton("⬅️ Назад"))

# --- Переменные ---
selected_voice = {}

# --- Настройка эмоций ---
def get_emotion_settings(text):
    if '😂' in text or '🤣' in text or '😄' in text:
        return 0.3, 0.9
    elif '😢' in text or '😭' in text or '💔' in text:
        return 0.7, 0.5
    elif '😡' in text or '🤬' in text:
        return 0.8, 0.6
    elif '😊' in text or '❤️' in text or '🥰' in text:
        return 0.4, 0.8
    else:
        return 0.5, 0.75

instruction_text = (
    "Как использовать смайлики для озвучки с эмоциями:\n\n"
    "Просто добавь смайлики в текст, и голос будет меняться в зависимости от настроения:\n"
    "- Весёлое: 😄😂🤣\n"
    "- Грустное: 😢😭💔\n"
    "- Злое: 😡🤬\n"
    "- Тёплое: 😊❤️🥰\n\n"
    "Пример: \"Привет! Как дела? 😂\" — озвучка будет весёлой.\n\n"
    "📖 Инструкция по замене голоса:\n"
    "1. Четко говорите.\n2. Минимум фона.\n3. Нормальная тональность.\n4. Плавная речь.\n5. Простые фразы."
)

# --- Команды ---
@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    user_id = message.from_user.id
    cursor.execute('INSERT INTO users (id) VALUES (%s) ON CONFLICT DO NOTHING', (user_id,))
    conn.commit()

    welcome = (
        "Добро пожаловать в бот 🎤🎧\n\n"
        "Я умею озвучивать текст разными голосами и менять голос в сообщениях.\n"
        "Выбери действие ниже и попробуй! 😊"
    )
    await message.answer(welcome, reply_markup=main_kb)

@dp.message_handler(commands=['broadcast'])
async def broadcast_cmd(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Нет прав.")
        return

    text = message.text.replace("/broadcast", "").strip()
    if not text:
        await message.answer("Добавь текст после команды.")
        return

    cursor.execute("SELECT id FROM users")
    users = cursor.fetchall()
    sent = 0
    for user in users:
        try:
            await bot.send_message(user[0], text)
            sent += 1
            await asyncio.sleep(0.1)
        except Exception as e:
            print(f"Не отправлено {user[0]}: {e}")
    await message.answer(f"✅ Отправлено {sent} пользователям.")

@dp.message_handler(lambda msg: msg.text == "🗣 Озвучить текст")
async def tts_request(message: types.Message):
    await message.answer("Выбери голос и отправь текст:", reply_markup=voice_kb)

@dp.message_handler(lambda msg: msg.text == "🎧 Заменить голос")
async def vc_request(message: types.Message):
    await message.answer("Выбери голос для замены и отправь голосовое:", reply_markup=voice_kb)

@dp.message_handler(lambda msg: msg.text == "📖 Инструкция")
async def instruction(message: types.Message):
    await message.answer(instruction_text, reply_markup=instruction_kb)

@dp.message_handler(lambda msg: msg.text == "⬅️ Назад")
async def back_to_main(message: types.Message):
    await message.answer("Выбери действие:", reply_markup=main_kb)

@dp.message_handler(lambda msg: msg.text in ["Маша", "Денис", "Олег", "Аня"])
async def handle_voice_choice(message: types.Message):
    selected_voice[message.from_user.id] = message.text
    await message.answer(f"Выбран голос: {message.text}. Отправь текст:", reply_markup=back_kb)

@dp.message_handler(lambda msg: msg.text not in ["🗣 Озвучить текст", "🎧 Заменить голос", "⬅️ Назад", "Маша", "Денис", "Олег", "Аня", "📖 Инструкция"])
async def handle_text(message: types.Message):
    voice = selected_voice.get(message.from_user.id)
    if not voice:
        await message.answer("Сначала выбери голос.")
        return

    text = message.text
    stability, similarity = get_emotion_settings(text)

    headers = {
        'xi-api-key': API_KEY,
        'Content-Type': 'application/json'
    }

    data = {
        'text': text,
        'model_id': 'eleven_multilingual_v2',
        'voice_settings': {
            'stability': stability,
            'similarity_boost': similarity
        }
    }

    voice_map = {
        "Маша": VOICE_ID_MASHA,
        "Денис": VOICE_ID_DENIS,
        "Олег": VOICE_ID_OGE,
        "Аня": VOICE_ID_ANYA
    }

    response = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_map[voice]}",
        headers=headers,
        json=data
    )

    if response.status_code == 200:
        with open('output.mp3', 'wb') as f:
            f.write(response.content)
        with open('output.mp3', 'rb') as f:
            await message.answer_voice(f)
    else:
        await message.answer(f"Ошибка озвучивания: {response.status_code}")

@dp.message_handler(content_types=['voice'])
async def handle_voice(message: types.Message):
    voice = selected_voice.get(message.from_user.id)
    if not voice:
        await message.answer("Сначала выбери голос для замены.")
        return

    file_info = await bot.get_file(message.voice.file_id)
    file_url = f"https://api.telegram.org/file/bot{API_TOKEN}/{file_info.file_path}"
    voice_data = requests.get(file_url).content

    headers = { 'xi-api-key': API_KEY }
    files = { 'audio': ('voice_message.ogg', voice_data, 'audio/ogg') }

    voice_map = {
        "Маша": VOICE_ID_MASHA,
        "Денис": VOICE_ID_DENIS,
        "Олег": VOICE_ID_OGE,
        "Аня": VOICE_ID_ANYA
    }

    response = requests.post(
        f"https://api.elevenlabs.io/v1/speech-to-speech/{voice_map[voice]}",
        headers=headers,
        files=files
    )

    if response.status_code == 200:
        with open('converted.mp3', 'wb') as f:
            f.write(response.content)
        with open('converted.mp3', 'rb') as f:
            await message.answer_voice(f)
    else:
        await message.answer(f"Ошибка замены: {response.status_code}, {response.text}")

# --- Запуск ---
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
