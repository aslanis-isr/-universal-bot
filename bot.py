import asyncio
import asyncio
import json
import os
import random
import re
import shutil
import uuid
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
import yt_dlp


# ============================================================
# НАСТРОЙКИ
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не найден")

DATA_DIR = Path("/data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

DOWNLOAD_DIR = DATA_DIR / "downloads"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

SCORES_FILE = DATA_DIR / "games.json"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Ссылки пользователей
pending_links = {}

# Игра "Угадай число"
number_games = {}

# Викторина
quiz_games = {}


# ============================================================
# ОЧКИ ИГР
# ============================================================

def load_scores():
    if not SCORES_FILE.exists():
        return {}

    try:
        with open(SCORES_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return {}


def save_scores(scores):
    with open(SCORES_FILE, "w", encoding="utf-8") as file:
        json.dump(scores, file, ensure_ascii=False, indent=2)


def add_score(user_id, name, points):
    scores = load_scores()
    key = str(user_id)

    if key not in scores:
        scores[key] = {
            "name": name,
            "score": 0
        }

    scores[key]["name"] = name
    scores[key]["score"] += points

    save_scores(scores)

    return scores[key]["score"]


# ============================================================
# ГЛАВНОЕ МЕНЮ
# ============================================================

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
                    text="🎥 Видео",
                    callback_data="video"
                ),
                InlineKeyboardButton(
                    text="🎵 Аудио MP3",
                    callback_data="audio"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📸 Instagram",
                    callback_data="instagram"
                ),
                InlineKeyboardButton(
                    text="▶️ YouTube",
                    callback_data="youtube"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎵 VK",
                    callback_data="vk"
                ),
                InlineKeyboardButton(
                    text="🎵 TikTok",
                    callback_data="tiktok"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🌐 Другие сайты",
                    callback_data="other"
                ),
                InlineKeyboardButton(
                    text="🎬 Фильмы",
                    callback_data="films"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎮 ИГРЫ",
                    callback_data="games"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⚙️ Настройки",
                    callback_data="settings"
                ),
                InlineKeyboardButton(
                    text="❓ Помощь",
                    callback_data="help"
                )
            ],
        ]
    )


def format_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎥 Видео",
                    callback_data="choose_video"
                ),
                InlineKeyboardButton(
                    text="🎵 MP3",
                    callback_data="choose_audio"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отмена",
                    callback_data="cancel"
                )
            ]
        ]
    )


def quality_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📱 360p",
                    callback_data="quality_360"
                ),
                InlineKeyboardButton(
                    text="📱 480p",
                    callback_data="quality_480"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎥 720p",
                    callback_data="quality_720"
                ),
                InlineKeyboardButton(
                    text="🔥 1080p",
                    callback_data="quality_1080"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🚀 Максимальное",
                    callback_data="quality_max"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отмена",
                    callback_data="cancel"
                )
            ]
        ]
    )


# ============================================================
# МЕНЮ ИГР
# ============================================================

def games_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🧠 Викторина",
                    callback_data="game_quiz"
                ),
                InlineKeyboardButton(
                    text="🔢 Угадай число",
                    callback_data="game_number"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✊ Камень-ножницы-бумага",
                    callback_data="game_rps"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🪙 Монетка",
                    callback_data="game_coin"
                ),
                InlineKeyboardButton(
                    text="🎲 Кубики",
                    callback_data="game_dice"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎯 Испытай удачу",
                    callback_data="game_lucky"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏆 Таблица лидеров",
                    callback_data="leaderboard"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏠 Главное меню",
                    callback_data="home"
                )
            ]
        ]
    )


def rps_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✊ Камень",
                    callback_data="rps_rock"
                ),
                InlineKeyboardButton(
                    text="✋ Бумага",
                    callback_data="rps_paper"
                ),
                InlineKeyboardButton(
                    text="✌️ Ножницы",
                    callback_data="rps_scissors"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎮 Игры",
                    callback_data="games"
                )
            ]
        ]
    )


def coin_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🟡 Орёл",
                    callback_data="coin_heads"
                ),
                InlineKeyboardButton(
                    text="⚪ Решка",
                    callback_data="coin_tails"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎮 Игры",
                    callback_data="games"
                )
            ]
        ]
    )


# ============================================================
# START
# ============================================================

@dp.message(CommandStart())
async def start(message: Message):
    text = (
        "<b>🖤 UNIVERSAL DOWNLOADER 💛</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "Скачивай разрешённый контент\n"
        "в удобном формате.\n\n"
        "🎥 Видео\n"
        "🎵 MP3\n"
        "📸 Instagram\n"
        "▶️ YouTube\n"
        "🎵 VK\n"
        "🎵 TikTok\n"
        "🌐 Другие поддерживаемые сайты\n"
        "🎬 Фильмы\n\n"
        "🎮 Игры и очки\n\n"
        "<i>Просто отправь ссылку.</i>"
    )

    await message.answer(
        text,
        reply_markup=main_menu(),
        parse_mode="HTML"
    )


# ============================================================
# ГЛАВНОЕ МЕНЮ
# ============================================================

@dp.callback_query(F.data == "home")
async def home(callback: CallbackQuery):
    await callback.message.edit_text(
        "<b>🖤 UNIVERSAL DOWNLOADER 💛</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "Выбери нужное действие:",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data == "download")
async def download_button(callback: CallbackQuery):
    pending_links.pop(callback.from_user.id, None)

    await callback.message.answer(
        "🔗 <b>Отправь ссылку</b>\n\n"
        "Я определю поддерживаемый источник "
        "автоматически.",
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data == "video")
async def video_button(callback: CallbackQuery):
    pending_links[callback.from_user.id] = {
        "mode": "video"
    }

    await callback.message.answer(
        "🎥 Отправь ссылку на видео.\n\n"
        "После получения ссылки выберем качество."
    )
    await callback.answer()


@dp.callback_query(F.data == "audio")
async def audio_button(callback: CallbackQuery):
    pending_links[callback.from_user.id] = {
        "mode": "audio"
    }

    await callback.message.answer(
        "🎵 Отправь ссылку на видео.\n\n"
        "Я попробую извлечь из него MP3."
    )
    await callback.answer()


@dp.callback_query(F.data == "instagram")
async def instagram_button(callback: CallbackQuery):
    await callback.message.answer(
        "📸 <b>Instagram</b>\n\n"
        "Отправь ссылку на Reel или видео, "
        "которое разрешено скачивать.",
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data == "youtube")
async def youtube_button(callback: CallbackQuery):
    await callback.message.answer(
        "▶️ <b>YouTube</b>\n\n"
        "Отправь ссылку на видео, которое "
        "разрешено тебе скачивать.",
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data == "vk")
async def vk_button(callback: CallbackQuery):
    await callback.message.answer(
        "🎵 <b>VK</b>\n\n"
        "Отправь ссылку на разрешённое видео.",
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data == "tiktok")
async def tiktok_button(callback: CallbackQuery):
    await callback.message.answer(
        "🎵 <b>TikTok</b>\n\n"
        "Отправь ссылку на видео, которое "
        "разрешено сохранять.",
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data == "other")
async def other_button(callback: CallbackQuery):
    await callback.message.answer(
        "🌐 <b>Другие сайты</b>\n\n"
        "Отправь ссылку. Бот попробует "
        "определить поддерживаемый источник.",
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data == "films")
async def films_button(callback: CallbackQuery):
    await callback.message.answer(
        "🎬 <b>Фильмы</b>\n\n"
        "Можно скачивать только контент, "
        "который разрешено скачивать правообладателем "
        "или который находится в открытом доступе.\n\n"
        "Отправь разрешённую ссылку.",
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data == "settings")
async def settings_button(callback: CallbackQuery):
    await callback.message.answer(
        "⚙️ <b>Настройки</b>\n\n"
        "🎥 Видео — выбор качества\n"
        "🎵 MP3 — извлечение аудио\n"
        "🌐 Автоматическое определение источника\n\n"
        "Основной режим: максимальное доступное качество.",
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data == "help")
async def help_button(callback: CallbackQuery):
    await callback.message.answer(
        "❓ <b>Помощь</b>\n\n"
        "1️⃣ Отправь ссылку.\n"
        "2️⃣ Выбери видео или MP3.\n"
        "3️⃣ Для видео выбери качество.\n"
        "4️⃣ Подожди обработку.\n"
        "5️⃣ Получи файл.\n\n"
        "⚠️ Используй бот только для контента, "
        "который разрешено скачивать.",
        parse_mode="HTML"
    )
    await callback.answer()


# ============================================================
# ПОЛУЧЕНИЕ ССЫЛКИ
# ============================================================

URL_PATTERN = re.compile(
    r"https?://[^\s]+",
    re.IGNORECASE
)


@dp.message(F.text)
async def receive_url(message: Message):
    text = message.text.strip()

    match = URL_PATTERN.search(text)

    if not match:
        return

    url = match.group(0).rstrip(").,!?")

    user_id = message.from_user.id

    current = pending_links.get(user_id, {})

    if current.get("mode") in ("video", "audio"):
        mode = current["mode"]
        pending_links[user_id] = {
            "url": url,
            "mode": mode
        }

        if mode == "audio":
            await message.answer(
                "🎵 Ссылка получена!\n\n"
                "⏳ Подготавливаю MP3..."
            )
            await download_and_send(
                message,
                url,
                "audio"
            )
        else:
            await message.answer(
                "🎥 Ссылка получена!\n\n"
                "Выбери качество:",
                reply_markup=quality_menu()
            )

        return

    pending_links[user_id] = {
        "url": url
    }

    await message.answer(
        "🔗 <b>Ссылка получена!</b>\n\n"
        "Что хочешь получить?",
        reply_markup=format_menu(),
        parse_mode="HTML"
    )


# ============================================================
# ВЫБОР ФОРМАТА
# ============================================================

@dp.callback_query(F.data == "choose_video")
async def choose_video(callback: CallbackQuery):
    user_id = callback.from_user.id

    if user_id not in pending_links:
        await callback.answer(
            "Сначала отправь ссылку.",
            show_alert=True
        )
        return

    pending_links[user_id]["mode"] = "video"

    await callback.message.edit_text(
        "🎥 <b>Выбери качество видео:</b>",
        reply_markup=quality_menu(),
        parse_mode="HTML"
    )

    await callback.answer()


@dp.callback_query(F.data == "choose_audio")
async def choose_audio(callback: CallbackQuery):
    user_id = callback.from_user.id

    data = pending_links.get(user_id)

    if not data or "url" not in data:
        await callback.answer(
            "Сначала отправь ссылку.",
            show_alert=True
        )
        return

    url = data["url"]

    pending_links.pop(user_id, None)

    await callback.message.edit_text(
        "🎵 <b>Извлекаю аудио...</b>\n\n"
        "⏳ Подожди немного.",
        parse_mode="HTML"
    )

    await download_and_send(
        callback.message,
        url,
        "audio"
    )

    await callback.answer()


# ============================================================
# КАЧЕСТВО
# ============================================================

@dp.callback_query(F.data.startswith("quality_"))
async def choose_quality(callback: CallbackQuery):
    user_id = callback.from_user.id

    data = pending_links.get(user_id)

    if not data or "url" not in data:
        await callback.answer(
            "Ссылка не найдена.",
            show_alert=True
        )
        return

    quality = callback.data.replace(
        "quality_",
        ""
    )

    url = data["url"]

    pending_links.pop(user_id, None)

    names = {
        "360": "360p",
        "480": "480p",
        "720": "720p",
        "1080": "1080p",
        "max": "максимальное качество"
    }

    await callback.message.edit_text(
        f"🎥 <b>Скачиваю: {names.get(quality, quality)}</b>\n\n"
        "⏳ Это может занять некоторое время.",
        parse_mode="HTML"
    )

    await download_and_send(
        callback.message,
        url,
        "video",
        quality
    )

    await callback.answer()


# ============================================================
# ОТМЕНА
# ============================================================

@dp.callback_query(F.data == "cancel")
async def cancel(callback: CallbackQuery):
    pending_links.pop(callback.from_user.id, None)

    await callback.message.edit_text(
        "❌ Загрузка отменена.",
        reply_markup=main_menu()
    )

    await callback.answer()


# ============================================================
# СКАЧИВАНИЕ
# ============================================================

def get_video_format(quality):
    ffmpeg_exists = shutil.which("ffmpeg") is not None

    if quality == "360":
        height = 360
    elif quality == "480":
        height = 480
    elif quality == "720":
        height = 720
    elif quality == "1080":
        height = 1080
    else:
        height = None

    if ffmpeg_exists:
        if height:
            return (
                f"bestvideo[height<={height}]+bestaudio/"
                f"best[height<={height}]/best"
            )

        return "bestvideo+bestaudio/best"

    # Если ffmpeg отсутствует,
    # берём готовый одиночный MP4-файл.
    if height:
        return (
            f"best[ext=mp4][height<={height}]/"
            f"best[height<={height}]/best"
        )

    return "best[ext=mp4]/best"


def download_video(url, quality, output_dir):
    output_template = str(
        output_dir / "%(title).80s-%(id)s.%(ext)s"
    )

    options = {
        "format": get_video_format(quality),
        "outtmpl": output_template,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "restrictfilenames": True,
        "retries": 3,
    }

    if shutil.which("ffmpeg"):
        options["merge_output_format"] = "mp4"

    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(
            url,
            download=True
        )

        requested = info.get("requested_downloads") or []

        files = []

        for item in requested:
            filepath = item.get("filepath")
            if filepath:
                files.append(Path(filepath))

        if not files:
            prepared = ydl.prepare_filename(info)
            files.append(Path(prepared))

        # После объединения yt-dlp может создать mp4.
        possible = list(output_dir.glob("*"))

        if possible:
            possible.sort(
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )

            for file in possible:
                if file.is_file():
                    return file

        return files[0]


def download_audio(url, output_dir):
    if not shutil.which("ffmpeg"):
        raise RuntimeError(
            "Для создания MP3 на сервере нужен ffmpeg."
        )

    output_template = str(
        output_dir / "%(title).80s-%(id)s.%(ext)s"
    )

    options = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "restrictfilenames": True,
        "retries": 3,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        ydl.download([url])

    possible = list(output_dir.glob("*.mp3"))

    if not possible:
        raise RuntimeError(
            "MP3-файл не был создан."
        )

    possible.sort(
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )

    return possible[0]


async def download_and_send(
    message,
    url,
    mode,
    quality="max"
):
    job_dir = DOWNLOAD_DIR / str(uuid.uuid4())
    job_dir.mkdir(parents=True, exist_ok=True)

    try:
        if mode == "video":
            file_path = await asyncio.to_thread(
                download_video,
                url,
                quality,
                job_dir
            )

            if not file_path.exists():
                raise RuntimeError(
                    "Файл не найден после скачивания."
                )

            size_mb = file_path.stat().st_size / (
                1024 * 1024
            )

            if size_mb > 50:
                await message.answer(
                    "❌ Файл получился слишком большим "
                    "для отправки через стандартный Telegram Bot API.\n\n"
                    f"Размер: {size_mb:.1f} МБ\n\n"
                    "Попробуй выбрать качество ниже."
                )
                return

            await message.answer_document(
                document=file_path.open("rb"),
                caption=(
                    "🎥 <b>Готово!</b>\n\n"
                    "🖤 Universal Downloader"
                ),
                parse_mode="HTML"
            )

        else:
            file_path = await asyncio.to_thread(
                download_audio,
                url,
                job_dir
            )

            if not file_path.exists():
                raise RuntimeError(
                    "MP3-файл не найден."
                )

            size_mb = file_path.stat().st_size / (
                1024 * 1024
            )

            if size_mb > 50:
                await message.answer(
                    "❌ MP3 получился слишком большим "
                    "для отправки через стандартный Telegram Bot API."
                )
                return

            await message.answer_audio(
                audio=file_path.open("rb"),
                caption=(
                    "🎵 <b>MP3 готов!</b>\n\n"
                    "🖤 Universal Downloader"
                ),
                parse_mode="HTML"
            )

    except Exception as error:
        print("DOWNLOAD ERROR:", repr(error))

        await message.answer(
            "❌ <b>Не удалось скачать файл.</b>\n\n"
            "Возможные причины:\n"
            "• сайт не поддерживается;\n"
            "• ссылка недоступна;\n"
            "• контент требует авторизации;\n"
            "• сайт временно блокирует загрузку;\n"
            "• файл слишком большой;\n"
            "• для MP3 на сервере нет ffmpeg.\n\n"
            "Попробуй другую ссылку.",
            parse_mode="HTML"
        )

    finally:
        try:
            shutil.rmtree(
                job_dir,
                ignore_errors=True
            )
        except Exception:
            pass


# ============================================================
# ИГРЫ
# ============================================================

@dp.callback_query(F.data == "games")
async def games(callback: CallbackQuery):
    scores = load_scores()
    user = scores.get(str(callback.from_user.id), {})
    score = user.get("score", 0)

    await callback.message.edit_text(
        "<b>🎮 ИГРОВАЯ ЗОНА</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"⭐ Твои очки: <b>{score}</b>\n\n"
        "Выбирай игру:",
        reply_markup=games_menu(),
        parse_mode="HTML"
    )

    await callback.answer()


# ============================================================
# КУБИКИ
# ============================================================

@dp.callback_query(F.data == "game_dice")
async def game_dice(callback: CallbackQuery):
    value = random.randint(1, 6)

    points = value

    total = add_score(
        callback.from_user.id,
        callback.from_user.full_name,
        points
    )

    await callback.message.edit_text(
        "🎲 <b>Кубик</b>\n\n"
        f"Выпало: <b>{value}</b>\n"
        f"⭐ +{points} очков\n\n"
        f"Твой счёт: <b>{total}</b>",
        reply_markup=games_menu(),
        parse_mode="HTML"
    )

    await callback.answer()


# ============================================================
# ИСПЫТАЙ УДАЧУ
# ============================================================

@dp.callback_query(F.data == "game_lucky")
async def game_lucky(callback: CallbackQuery):
    points = random.choice(
        [1, 2, 3, 5, 10, 15, 20]
    )

    total = add_score(
        callback.from_user.id,
        callback.from_user.full_name,
        points
    )

    await callback.message.edit_text(
        "🎯 <b>Испытай удачу!</b>\n\n"
        f"🎉 Ты получил <b>+{points}</b> очков!\n\n"
        f"⭐ Всего: <b>{total}</b>",
        reply_markup=games_menu(),
        parse_mode="HTML"
    )

    await callback.answer()


# ============================================================
# МОНЕТКА
# ============================================================

@dp.callback_query(F.data == "game_coin")
async def game_coin(callback: CallbackQuery):
    await callback.message.edit_text(
        "🪙 <b>Монетка</b>\n\n"
        "Выбери сторону:",
        reply_markup=coin_menu(),
        parse_mode="HTML"
    )

    await callback.answer()


@dp.callback_query(F.data.startswith("coin_"))
async def coin_result(callback: CallbackQuery):
    user_choice = callback.data.replace(
        "coin_",
        ""
    )

    result = random.choice(
        ["heads", "tails"]
    )

    if result == "heads":
        result_text = "🟡 Орёл"
    else:
        result_text = "⚪ Решка"

    if user_choice == result:
        points = 5

        total = add_score(
            callback.from_user.id,
            callback.from_user.full_name,
            points
        )

        text = (
            "🪙 <b>Монетка</b>\n\n"
            f"Выпало: <b>{result_text}</b>\n"
            "🎉 Ты угадал!\n\n"
            f"⭐ +{points} очков\n"
            f"Всего: <b>{total}</b>"
        )
    else:
        text = (
            "🪙 <b>Монетка</b>\n\n"
            f"Выпало: <b>{result_text}</b>\n"
            "😅 Не угадал.\n\n"
            "Попробуй ещё раз."
        )

    await callback.message.edit_text(
        text,
        reply_markup=coin_menu(),
        parse_mode="HTML"
    )

    await callback.answer()


# ============================================================
# КАМЕНЬ НОЖНИЦЫ БУМАГА
# ============================================================

@dp.callback_query(F.data == "game_rps")
async def game_rps(callback: CallbackQuery):
    await callback.message.edit_text(
        "✊ <b>Камень • Ножницы • Бумага</b>\n\n"
        "Выбирай:",
        reply_markup=rps_menu(),
        parse_mode="HTML"
    )

    await callback.answer()


@dp.callback_query(F.data.startswith("rps_"))
async def rps_result(callback: CallbackQuery):
    user_choice = callback.data.replace(
        "rps_",
        ""
    )

    choices = [
        "rock",
        "paper",
        "scissors"
    ]

    bot_choice = random.choice(choices)

    names = {
        "rock": "✊ Камень",
        "paper": "✋ Бумага",
        "scissors": "✌️ Ножницы"
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
        result = "😅 Победил бот!"
        points = 0

    total = add_score(
        callback.from_user.id,
        callback.from_user.full_name,
        points
    )

    await callback.message.edit_text(
        "✊ <b>Камень • Ножницы • Бумага</b>\n\n"
        f"Ты: {names[user_choice]}\n"
        f"Бот: {names[bot_choice]}\n\n"
        f"<b>{result}</b>\n"
        f"⭐ +{points} очков\n"
        f"Всего: <b>{total}</b>",
        reply_markup=rps_menu(),
        parse_mode="HTML"
    )

    await callback.answer()


# ============================================================
# УГАДАЙ ЧИСЛО
# ============================================================

@dp.callback_query(F.data == "game_number")
async def game_number(callback: CallbackQuery):
    number_games[callback.from_user.id] = random.randint(
        1,
        10
    )

    await callback.message.edit_text(
        "🔢 <b>Угадай число</b>\n\n"
        "Я загадал число от <b>1 до 10</b>.\n\n"
        "Напиши свой вариант числом:",
        parse_mode="HTML"
    )

    await callback.answer()


# ============================================================
# ВИКТОРИНА
# ============================================================

QUIZ = [
    {
        "question": "Столица Франции?",
        "answers": ["Париж", "Лондон", "Рим", "Берлин"],
        "correct": 0
    },
    {
        "question": "Сколько дней в неделе?",
        "answers": ["5", "6", "7", "8"],
        "correct": 2
    },
    {
        "question": "Сколько сторон у квадрата?",
        "answers": ["3", "4", "5", "6"],
        "correct": 1
    },
    {
        "question": "Какая планета называется Красной?",
        "answers": ["Венера", "Марс", "Юпитер", "Сатурн"],
        "correct": 1
    },
    {
        "question": "Сколько минут в одном часе?",
        "answers": ["30", "45", "60", "90"],
        "correct": 2
    }
]


def quiz_keyboard(question_index):
    question = QUIZ[question_index]

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=answer,
                    callback_data=f"quiz_{question_index}_{i}"
                )
            ]
            for i, answer in enumerate(question["answers"])
        ] + [
            [
                InlineKeyboardButton(
                    text="🎮 Игры",
                    callback_data="games"
                )
            ]
        ]
    )


@dp.callback_query(F.data == "game_quiz")
async def game_quiz(callback: CallbackQuery):
    question_index = random.randrange(
        len(QUIZ)
    )

    quiz_games[callback.from_user.id] = question_index

    question = QUIZ[question_index]

    await callback.message.edit_text(
        "🧠 <b>Викторина</b>\n\n"
        f"{question['question']}",
        reply_markup=quiz_keyboard(question_index),
        parse_mode="HTML"
    )

    await callback.answer()


@dp.callback_query(F.data.startswith("quiz_"))
async def quiz_answer(callback: CallbackQuery):
    parts = callback.data.split("_")

    question_index = int(parts[1])
    answer_index = int(parts[2])

    question = QUIZ[question_index]

    if answer_index == question["correct"]:
        points = 5

        total = add_score(
            callback.from_user.id,
            callback.from_user.full_name,
            points
        )

        text = (
            "🧠 <b>Викторина</b>\n\n"
            "✅ Правильно!\n\n"
            f"⭐ +{points} очков\n"
            f"Всего: <b>{total}</b>"
        )
    else:
        correct_answer = question["answers"][
            question["correct"]
        ]

        text = (
            "🧠 <b>Викторина</b>\n\n"
            "❌ Неправильно.\n\n"
            f"Правильный ответ: "
            f"<b>{correct_answer}</b>"
        )

    await callback.message.edit_text(
        text,
        reply_markup=games_menu(),
        parse_mode="HTML"
    )

    await callback.answer()


# ============================================================
# ТЕКСТОВЫЕ ОТВЕТЫ ДЛЯ УГАДАЙ ЧИСЛО
# ============================================================

@dp.message(F.text.regexp(r"^\d+$"))
async def number_answer(message: Message):
    user_id = message.from_user.id

    if user_id not in number_games:
        return

    try:
        guess = int(message.text)
    except ValueError:
        return

    secret = number_games[user_id]

    if guess < 1 or guess > 10:
        await message.answer(
            "🔢 Введи число от 1 до 10."
        )
        return

    if guess == secret:
        points = 10

        total = add_score(
            user_id,
            message.from_user.full_name,
            points
        )

        number_games.pop(user_id, None)

        await message.answer(
            "🎉 <b>Ты угадал!</b>\n\n"
            f"Число было: <b>{secret}</b>\n"
            f"⭐ +{points} очков\n"
            f"Всего: <b>{total}</b>\n\n"
            "🎮 Можешь сыграть ещё.",
            reply_markup=games_menu(),
            parse_mode="HTML"
        )

    elif guess < secret:
        await message.answer(
            "⬆️ Моё число больше.\n"
            "Попробуй ещё раз!"
        )

    else:
        await message.answer(
            "⬇️ Моё число меньше.\n"
            "Попробуй ещё раз!"
        )


# ============================================================
# ТАБЛИЦА ЛИДЕРОВ
# ============================================================

@dp.callback_query(F.data == "leaderboard")
async def leaderboard(callback: CallbackQuery):
    scores = load_scores()

    if not scores:
        text = (
            "🏆 <b>Таблица лидеров</b>\n\n"
            "Пока никто не набрал очки.\n"
            "Будь первым! 🎮"
        )
    else:
        players = sorted(
            scores.values(),
            key=lambda item: item.get("score", 0),
            reverse=True
        )

        lines = [
            "🏆 <b>ТАБЛИЦА ЛИДЕРОВ</b>",
            "━━━━━━━━━━━━━━━━━━"
        ]

        medals = ["🥇", "🥈", "🥉"]

        for index, player in enumerate(
            players[:10],
            start=1
        ):
            medal = (
                medals[index - 1]
                if index <= 3
                else f"{index}."
            )

            name = player.get(
                "name",
                "Игрок"
            )

            score = player.get(
                "score",
                0
            )

            lines.append(
                f"{medal} {name} — ⭐ {score}"
            )

        text = "\n".join(lines)

    await callback.message.edit_text(
        text,
        reply_markup=games_menu(),
        parse_mode="HTML"
    )

    await callback.answer()


# ============================================================
# ЗАПУСК
# ============================================================

async def main():
    print("Universal Downloader запущен!")

    await dp.start_polling(
        bot,
        allowed_updates=dp.resolve_used_update_types()
    )


if __name__ == "__main__":
    asyncio.run(main())
