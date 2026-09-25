import asyncio
import os
import urllib.parse
import aiohttp
import google.generativeai as genai
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, BufferedInputFile

TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Память для диалога (в проде заменим на БД)
history = {}

@dp.message(CommandStart())
async def start(msg: Message):
    await msg.answer(
        "Привет! Я твой AI-художник и помощник.\n\n"
        "🎨 Напиши «нарисуй кота в космосе» — я нарисую картинку.\n"
        "💬 Напиши любой вопрос — я отвечу."
    )

@dp.message(F.text)
async def handle(msg: Message):
    uid = msg.from_user.id
    text = msg.text.strip()

    # --- Генерация картинки ---
    if text.lower().startswith(("нарисуй", "нарисовать", "draw", "картинку", "picture")):
        prompt = text
        for word in ["нарисуй", "нарисовать", "draw", "картинку", "picture"]:
            prompt = prompt.lower().replace(word, "", 1).strip()
        if not prompt:
            prompt = "красивый пейзаж"

        await msg.answer("🎨 Рисую... Это займёт 5–10 секунд.")

        url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=1024&height=1024&nologo=true"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=60) as resp:
                    if resp.status == 200:
                        img_data = await resp.read()
                        photo = BufferedInputFile(img_data, filename="image.jpg")
                        await msg.answer_photo(photo, caption=f"🎨 {prompt}")
                    else:
                        await msg.answer("😔 Не получилось нарисовать. Попробуй ещё раз.")
        except Exception as e:
            await msg.answer("😔 Ошибка при генерации картинки.")
        return

    # --- Ответ на вопрос через Gemini ---
    history.setdefault(uid, [])
    history[uid].append({"role": "user", "parts": [text]})

    try:
        response = await asyncio.to_thread(model.generate_content, history[uid])
        answer = response.text
        history[uid].append({"role": "model", "parts": [answer]})

        # Ограничиваем историю 20 сообщениями
        if len(history[uid]) > 20:
            history[uid] = history[uid][-20:]

        await msg.answer(answer)
    except Exception as e:
        await msg.answer("😔 Не получилось ответить. Попробуй позже.")

async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
