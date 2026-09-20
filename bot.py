import asyncio
import json
import os
import random
import re
import shutil
import uuid
from pathlib import Path

import yt_dlp
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    FSInputFile,
)

# =========================
# НАСТРОЙКИ
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не найден в переменных окружения")

DATA_DIR = Path("/data")
DOWNLOAD_DIR = DATA_DIR / "downloads"
USERS_FILE = DATA_DIR / "users.json"

DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# =========================
# ДАННЫЕ
# =========================

pending_links = {}
number_games = {}
quiz_games = {}


def load_users():
    if not USERS_FILE.exists():
        return {}

    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


users = load_users()


def get_user(user_id):
    uid = str(user_id)

    if uid not in users:
        users[uid] = {
            "points": 0,
            "downloads": 0,
        }
        save_users(users)

    return users[uid]


# =========================
# КЛАВИАТУРЫ
# =========================

def main_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📥 Скачать по ссылке",
                    callback_data="download"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎬 Видео",
                    callback_data="video"
                ),
                InlineKeyboardButton(
                    text="🎵 MP3",
                    callback_data="audio"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📸 Instagram",
                    callback_data="instagram"
                ),
                InlineKeyboardButton(
                    text="▶️ YouTube",
                    callback_data="youtube"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🎵 VK",
                    callback_data="vk"
                ),
                InlineKeyboardButton(
                    text="🎵 TikTok",
                    callback_data="tiktok"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🌐 Другие сайты",
                    callback_data="other"
                ),
                InlineKeyboardButton(
                    text="🎬 Фильмы",
                    callback_data="films"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🎮 Игры",
                    callback_data="games"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⚙️ Настройки",
                    callback_data="settings"
                ),
                InlineKeyboardButton(
                    text="❓ Помощь",
                    callback_data="help"
                ),
            ],
        ]
    )


def games_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🧠 Викторина",
                    callback_data="quiz"
                ),
                InlineKeyboardButton(
                    text="🔢 Угадай число",
                    callback_data="guess"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="✊ Камень-ножницы-бумага",
                    callback_data="rps"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🪙 Монетка",
                    callback_data="coin"
                ),
                InlineKeyboardButton(
                    text="🎲 Кубик",
                    callback_data="dice"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🎯 Удача",
                    callback_data="lucky"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🏆 Таблица лидеров",
                    callback_data="leaderboard"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Главное меню",
                    callback_data="back"
                )
            ],
        ]
    )


def rps_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🪨 Камень",
                    callback_data="rps_rock"
                ),
                InlineKeyboardButton(
                    text="📄 Бумага",
                    callback_data="rps_paper"
                ),
                InlineKeyboardButton(
                    text="✂️ Ножницы",
                    callback_data="rps_scissors"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Игры",
                    callback_data="games"
                )
            ],
        ]
    )


def back_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Главное меню",
                    callback_data="back"
                )
            ]
        ]
    )


# =========================
# /START
# =========================

@dp.message(CommandStart())
async def start(message: Message):
    user = get_user(message.from_user.id)

    await message.answer(
        "🚀 <b>UNIVERSAL DOWNLOADER</b>\n\n"
        "Твой универсальный бот для загрузки контента.\n\n"
        "📥 Видео\n"
        "🎵 MP3\n"
        "📸 Instagram\n"
        "▶️ YouTube\n"
        "🎵 VK\n"
        "🎵 TikTok\n"
        "🌐 Другие сайты\n\n"
        "🎮 А ещё здесь есть игры и система очков!\n\n"
        f"🏆 Твои очки: <b>{user['points']}</b>",
        reply_markup=main_menu(),
        parse_mode="HTML",
    )


# =========================
# КНОПКИ
# =========================

@dp.callback_query(F.data == "back")
async def back(callback: CallbackQuery):
    await callback.message.edit_text(
        "🚀 <b>UNIVERSAL DOWNLOADER</b>\n\n"
        "Выбери нужный раздел:",
        reply_markup=main_menu(),
        parse_mode="HTML",
    )
    await callback.answer()


@dp.callback_query(F.data == "download")
async def download_button(callback: CallbackQuery):
    pending_links[callback.from_user.id] = "video"

    await callback.message.answer(
        "📥 <b>Отправь ссылку</b>\n\n"
        "Я определю сайт автоматически и попробую скачать видео.",
        parse_mode="HTML",
    )

    await callback.answer()


@dp.callback_query(F.data == "video")
async def video_button(callback: CallbackQuery):
    pending_links[callback.from_user.id] = "video"

    await callback.message.answer(
        "🎬 <b>Скачивание видео</b>\n\n"
        "Отправь ссылку на видео.\n\n"
        "Я постараюсь скачать максимально доступное качество.",
        parse_mode="HTML",
    )

    await callback.answer()


@dp.callback_query(F.data == "audio")
async def audio_button(callback: CallbackQuery):
    pending_links[callback.from_user.id] = "audio"

    await callback.message.answer(
        "🎵 <b>Конвертация в MP3</b>\n\n"
        "Отправь ссылку на видео.\n\n"
        "⚠️ Для MP3 на сервере должен быть установлен ffmpeg.",
        parse_mode="HTML",
    )

    await callback.answer()


@dp.callback_query(F.data == "instagram")
async def instagram_button(callback: CallbackQuery):
    pending_links[callback.from_user.id] = "video"

    await callback.message.answer(
        "📸 <b>Instagram</b>\n\n"
        "Отправь ссылку на публичный пост или видео.",
        parse_mode="HTML",
    )

    await callback.answer()


@dp.callback_query(F.data == "youtube")
async def youtube_button(callback: CallbackQuery):
    pending_links[callback.from_user.id] = "video"

    await callback.message.answer(
        "▶️ <b>YouTube</b>\n\n"
        "Отправь ссылку на видео.",
        parse_mode="HTML",
    )

    await callback.answer()


@dp.callback_query(F.data == "vk")
async def vk_button(callback: CallbackQuery):
    pending_links[callback.from_user.id] = "video"

    await callback.message.answer(
        "🎵 <b>VK</b>\n\n"
        "Отправь публичную ссылку.",
        parse_mode="HTML",
    )

    await callback.answer()


@dp.callback_query(F.data == "tiktok")
async def tiktok_button(callback: CallbackQuery):
    pending_links[callback.from_user.id] = "video"

    await callback.message.answer(
        "🎵 <b>TikTok</b>\n\n"
        "Отправь ссылку на публичное видео.",
        parse_mode="HTML",
    )

    await callback.answer()


@dp.callback_query(F.data == "other")
async def other_button(callback: CallbackQuery):
    pending_links[callback.from_user.id] = "video"

    await callback.message.answer(
        "🌐 <b>Другие сайты</b>\n\n"
        "Отправь ссылку.\n"
        "Я попробую определить сайт автоматически.",
        parse_mode="HTML",
    )

    await callback.answer()


@dp.callback_query(F.data == "films")
async def films_button(callback: CallbackQuery):
    await callback.message.answer(
        "🎬 <b>Фильмы</b>\n\n"
        "Можно скачивать только фильмы и видео, которые "
        "разрешены правообладателем для скачивания или находятся "
        "в общественном достоянии.\n\n"
        "Отправь разрешённую ссылку.",
        parse_mode="HTML",
    )

    pending_links[callback.from_user.id] = "video"

    await callback.answer()


# =========================
# ИГРЫ
# =========================

@dp.callback_query(F.data == "games")
async def games(callback: CallbackQuery):
    user = get_user(callback.from_user.id)

    await callback.message.edit_text(
        "🎮 <b>ИГРЫ</b>\n\n"
        f"🏆 Твои очки: <b>{user['points']}</b>\n\n"
        "Выбирай игру:",
        reply_markup=games_menu(),
        parse_mode="HTML",
    )

    await callback.answer()


@dp.callback_query(F.data == "coin")
async def coin(callback: CallbackQuery):
    result = random.choice(["🪙 Орёл", "🪙 Решка"])

    user = get_user(callback.from_user.id)
    user["points"] += 1
    save_users(users)

    await callback.message.edit_text(
        f"<b>🪙 Монетка</b>\n\n"
        f"Результат: <b>{result}</b>\n\n"
        f"🏆 +1 очко\n"
        f"Твои очки: {user['points']}",
        reply_markup=games_menu(),
        parse_mode="HTML",
    )

    await callback.answer()


@dp.callback_query(F.data == "dice")
async def dice(callback: CallbackQuery):
    number = random.randint(1, 6)

    user = get_user(callback.from_user.id)
    user["points"] += number
    save_users(users)

    await callback.message.edit_text(
        f"🎲 <b>Кубик</b>\n\n"
        f"Выпало: <b>{number}</b>\n\n"
        f"🏆 +{number} очков\n"
        f"Всего: {user['points']}",
        reply_markup=games_menu(),
        parse_mode="HTML",
    )

    await callback.answer()


@dp.callback_query(F.data == "lucky")
async def lucky(callback: CallbackQuery):
    number = random.randint(1, 100)

    if number >= 90:
        points = 20
        text = "🔥 НЕВЕРОЯТНАЯ УДАЧА!"
    elif number >= 70:
        points = 10
        text = "✨ Отличная удача!"
    elif number >= 40:
        points = 5
        text = "👍 Неплохо!"
    else:
        points = 1
        text = "🙂 Попробуй ещё!"

    user = get_user(callback.from_user.id)
    user["points"] += points
    save_users(users)

    await callback.message.edit_text(
        f"🎯 <b>Удача</b>\n\n"
        f"Число: <b>{number}</b>\n"
        f"{text}\n\n"
        f"🏆 +{points} очков\n"
        f"Всего: {user['points']}",
        reply_markup=games_menu(),
        parse_mode="HTML",
    )

    await callback.answer()


@dp.callback_query(F.data == "guess")
async def guess(callback: CallbackQuery):
    number_games[callback.from_user.id] = random.randint(1, 10)

    await callback.message.answer(
        "🔢 <b>Угадай число</b>\n\n"
        "Я загадал число от <b>1 до 10</b>.\n"
        "Напиши свой вариант.",
        parse_mode="HTML",
    )

    await callback.answer()


@dp.callback_query(F.data == "rps")
async def rps(callback: CallbackQuery):
    await callback.message.edit_text(
        "✊ <b>Камень — ножницы — бумага</b>\n\n"
        "Выбирай:",
        reply_markup=rps_menu(),
        parse_mode="HTML",
    )

    await callback.answer()


@dp.callback_query(F.data.startswith("rps_"))
async def rps_play(callback: CallbackQuery):
    user_choice = callback.data.replace("rps_", "")

    choices = ["rock", "paper", "scissors"]
    bot_choice = random.choice(choices)

    names = {
        "rock": "🪨 Камень",
        "paper": "📄 Бумага",
        "scissors": "✂️ Ножницы",
    }

    if user_choice == bot_choice:
        result = "🤝 Ничья!"
        points = 1
    elif (
        (user_choice == "rock" and bot_choice == "scissors")
        or
        (user_choice == "paper" and bot_choice == "rock")
        or
        (user_choice == "scissors" and bot_choice == "paper")
    ):
        result = "🎉 Ты победил!"
        points = 5
    else:
        result = "😄 Я победил!"
        points = 0

    user = get_user(callback.from_user.id)
    user["points"] += points
    save_users(users)

    await callback.message.edit_text(
        "✊ <b>Камень — ножницы — бумага</b>\n\n"
        f"Ты: {names[user_choice]}\n"
        f"Бот: {names[bot_choice]}\n\n"
        f"<b>{result}</b>\n\n"
        f"🏆 +{points} очков\n"
        f"Всего: {user['points']}",
        reply_markup=games_menu(),
        parse_mode="HTML",
    )

    await callback.answer()


# =========================
# ВИКТОРИНА
# =========================

QUIZ = [
    {
        "question": "Столица Франции?",
        "answers": ["Париж", "Лондон", "Берлин", "Рим"],
        "correct": "Париж",
    },
    {
        "question": "Сколько дней в неделе?",
        "answers": ["5", "6", "7", "8"],
        "correct": "7",
    },
    {
        "question": "Сколько будет 5 × 5?",
        "answers": ["20", "25", "30", "35"],
        "correct": "25",
    },
]


def quiz_keyboard(answers):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=answer,
                    callback_data=f"quiz_answer:{answer}"
                )
            ]
            for answer in answers
        ]
        + [
            [
                InlineKeyboardButton(
                    text="⬅️ Игры",
                    callback_data="games"
                )
            ]
        ]
    )


@dp.callback_query(F.data == "quiz")
async def quiz(callback: CallbackQuery):
    question = random.choice(QUIZ)

    quiz_games[callback.from_user.id] = question["correct"]

    await callback.message.edit_text(
        f"🧠 <b>Викторина</b>\n\n"
        f"{question['question']}",
        reply_markup=quiz_keyboard(question["answers"]),
        parse_mode="HTML",
    )

    await callback.answer()


@dp.callback_query(F.data.startswith("quiz_answer:"))
async def quiz_answer(callback: CallbackQuery):
    answer = callback.data.split(":", 1)[1]
    correct = quiz_games.get(callback.from_user.id)

    user = get_user(callback.from_user.id)

    if answer == correct:
        user["points"] += 5
        text = "🎉 Правильно!\n\n🏆 +5 очков"
    else:
        text = f"❌ Неправильно!\n\nПравильный ответ: <b>{correct}</b>"

    save_users(users)

    await callback.message.edit_text(
        f"🧠 <b>Викторина</b>\n\n"
        f"{text}\n\n"
        f"Твои очки: <b>{user['points']}</b>",
        reply_markup=games_menu(),
        parse_mode="HTML",
    )

    await callback.answer()


# =========================
# ЛИДЕРБОРД
# =========================

@dp.callback_query(F.data == "leaderboard")
async def leaderboard(callback: CallbackQuery):
    sorted_users = sorted(
        users.items(),
        key=lambda x: x[1].get("points", 0),
        reverse=True,
    )

    text = "🏆 <b>ТАБЛИЦА ЛИДЕРОВ</b>\n\n"

    if not sorted_users:
        text += "Пока никто не набрал очки."
    else:
        for index, (uid, data) in enumerate(sorted_users[:10], start=1):
            text += f"{index}. ID {uid}: <b>{data.get('points', 0)}</b> очков\n"

    await callback.message.edit_text(
        text,
        reply_markup=games_menu(),
        parse_mode="HTML",
    )

    await callback.answer()


# =========================
# НАСТРОЙКИ / ПОМОЩЬ
# =========================

@dp.callback_query(F.data == "settings")
async def settings(callback: CallbackQuery):
    await callback.message.edit_text(
        "⚙️ <b>Настройки</b>\n\n"
        "Автоматически определяем сайт по ссылке.\n"
        "Видео скачивается в максимально доступном качестве.\n"
        "MP3 доступен при наличии ffmpeg на сервере.",
        reply_markup=back_menu(),
        parse_mode="HTML",
    )

    await callback.answer()


@dp.callback_query(F.data == "help")
async def help_button(callback: CallbackQuery):
    await callback.message.edit_text(
        "❓ <b>Помощь</b>\n\n"
        "1️⃣ Выбери нужный раздел.\n"
        "2️⃣ Отправь публичную ссылку.\n"
        "3️⃣ Бот попробует скачать файл.\n\n"
        "Поддержка конкретного сайта зависит от его доступности "
        "для yt-dlp.\n\n"
        "⚠️ Используй загрузку только для контента, который тебе "
        "разрешено скачивать.",
        reply_markup=back_menu(),
        parse_mode="HTML",
    )

    await callback.answer()


# =========================
# СКАЧИВАНИЕ
# =========================

def clean_url(text):
    match = re.search(r"https?://\S+", text)

    if not match:
        return None

    return match.group(0).strip()


def download_media(url, mode, job_dir):
    job_dir.mkdir(parents=True, exist_ok=True)

    output_template = str(job_dir / "%(title).100s-%(id)s.%(ext)s")

    if mode == "audio":
        if shutil.which("ffmpeg") is None:
            raise RuntimeError(
                "Для создания MP3 на сервере нужен ffmpeg."
            )

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": output_template,
            "noplaylist": True,
            "quiet": False,
            "no_warnings": False,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
        }

    else:
        ydl_opts = {
            "format": "bestvideo+bestaudio/best",
            "outtmpl": output_template,
            "noplaylist": True,
            "merge_output_format": "mp4",
            "quiet": False,
            "no_warnings": False,
        }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

        prepared = Path(
            ydl.prepare_filename(info)
        )

        # После объединения yt-dlp может изменить расширение
        candidates = list(job_dir.iterdir())

        if mode == "audio":
            mp3_files = [
                p for p in candidates
                if p.suffix.lower() == ".mp3"
            ]

            if mp3_files:
                return max(
                    mp3_files,
                    key=lambda p: p.stat().st_mtime
                )

        video_files = [
            p for p in candidates
            if p.suffix.lower() in {
                ".mp4",
                ".mkv",
                ".webm",
                ".mov",
            }
        ]

        if video_files:
            return max(
                video_files,
                key=lambda p: p.stat().st_mtime
            )

        if prepared.exists():
            return prepared

        raise RuntimeError("Скачанный файл не найден.")


async def process_download(message, url, mode):
    job_id = uuid.uuid4().hex
    job_dir = DOWNLOAD_DIR / job_id

    status = await message.answer(
        "⏳ <b>Начинаю скачивание...</b>",
        parse_mode="HTML",
    )

    try:
        file_path = await asyncio.to_thread(
            download_media,
            url,
            mode,
            job_dir,
        )

        if not file_path.exists():
            raise RuntimeError("Файл после скачивания не найден.")

        file_size = file_path.stat().st_size

        # Примерная защита от слишком больших файлов
        if file_size > 49 * 1024 * 1024:
            raise RuntimeError(
                "Файл получился слишком большим для отправки ботом."
            )

        await status.edit_text(
            "📤 <b>Скачивание завершено!</b>\n"
            "Отправляю файл...",
            parse_mode="HTML",
        )

        input_file = FSInputFile(
            path=str(file_path)
        )

        if mode == "audio":
            await message.answer_audio(
                audio=input_file,
                caption="🎵 Готово!",
            )
        else:
            await message.answer_video(
                video=input_file,
                caption="🎬 Готово!",
                supports_streaming=True,
            )

        user = get_user(message.from_user.id)
        user["downloads"] += 1
        user["points"] += 1
        save_users(users)

        await status.delete()

    except Exception as e:
        print("DOWNLOAD ERROR:", repr(e))

        try:
            await status.edit_text(
                "❌ <b>Не удалось отправить файл.</b>\n\n"
                "Проверь ссылку или попробуй другой публичный "
                "материал.\n\n"
                f"<code>{str(e)[:500]}</code>",
                parse_mode="HTML",
            )
        except Exception:
            await message.answer(
                "❌ Не удалось скачать или отправить файл."
            )

    finally:
        try:
            shutil.rmtree(job_dir, ignore_errors=True)
        except Exception:
            pass


# =========================
# УГАДАЙ ЧИСЛО
# =========================

@dp.message(F.text.regexp(r"^\d+$"))
async def guess_number_handler(message: Message):
    user_id = message.from_user.id

    if user_id not in number_games:
        return

    try:
        guess_value = int(message.text)
    except ValueError:
        return

    secret = number_games[user_id]

    user = get_user(user_id)

    if guess_value == secret:
        user["points"] += 10
        save_users(users)

        del number_games[user_id]

        await message.answer(
            "🎉 <b>Ты угадал!</b>\n\n"
            "🏆 +10 очков\n"
            f"Твои очки: <b>{user['points']}</b>",
            reply_markup=games_menu(),
            parse_mode="HTML",
        )

    elif guess_value < secret:
        await message.answer("⬆️ Моё число больше!")

    else:
        await message.answer("⬇️ Моё число меньше!")


# =========================
# ССЫЛКИ
# =========================

@dp.message(F.text)
async def text_handler(message: Message):
    text = message.text.strip()

    url = clean_url(text)

    if not url:
        await message.answer(
            "🤖 Отправь мне ссылку на видео или выбери раздел "
            "в меню."
        )
        return

    user_id = message.from_user.id

    mode = pending_links.pop(user_id, "video")

    await process_download(
        message,
        url,
        mode,
    )


# =========================
# ЗАПУСК
# =========================

async def main():
    print("Universal Downloader запущен!")

    await dp.start_polling(
        bot,
        allowed_updates=dp.resolve_used_update_types(),
    )


if __name__ == "__main__":
    asyncio.run(main())
