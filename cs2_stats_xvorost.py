import json
import os
import re
from pathlib import Path

import requests
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)


# =========================
# НАЛАШТУВАННЯ
# =========================

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

TOKEN = os.getenv("TELEGRAM_TOKEN")
STEAM_API_KEY = os.getenv("STEAM_API_KEY")

CACHE_FILE = BASE_DIR / "steam_cache.json"
USERS_FILE = BASE_DIR / "users.json"


# =========================
# JSON HELPERS
# =========================


def load_json(file_path, default):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    return default


def save_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


steam_cache = load_json(CACHE_FILE, {})


# =========================
# USERS
# =========================


def register_user(user_id: int):
    users = load_json(USERS_FILE, [])

    if user_id not in users:
        users.append(user_id)
        save_json(USERS_FILE, users)

    return len(users)


# =========================
# STEAM
# =========================


def resolve_vanity(vanity: str):
    if vanity in steam_cache:
        return steam_cache[vanity]

    url = "https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/"

    params = {
        "key": STEAM_API_KEY,
        "vanityurl": vanity,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data["response"]["success"] == 1:
            steamid = data["response"]["steamid"]

            steam_cache[vanity] = steamid
            save_json(CACHE_FILE, steam_cache)

            return steamid

    except Exception as error:
        print(f"Steam API error: {error}")

    return None


def extract_steamid(text: str):
    steamid_match = re.search(r"(7656119\d{10})", text)

    if steamid_match:
        return steamid_match.group(1)

    vanity_match = re.search(r"steamcommunity\.com/id/([^/]+)", text)

    if vanity_match:
        vanity = vanity_match.group(1)
        return resolve_vanity(vanity)

    return None


# =========================
# КАРТОЧКА
# =========================


def build_card(steamid: str):
    steam_url = f"https://steamcommunity.com/profiles/{steamid}"
    csstats_url = f"https://csstats.gg/player/{steamid}"
    skinflow_url = f"https://skinflow.gg/cs2-tracker/{steamid}"
    csrep_url = f"https://csrep.gg/player/{steamid}"
    faceitfinder_url = f"https://faceitfinder.com/profile/{steamid}"

    return (
        "🎮 ── Player's Info ──\n\n"
        f"🔗 Steam:\n{steam_url}\n\n"
        f"🧮 CSStats:\n{csstats_url}\n"
        f"💠 SkinFlow:\n{skinflow_url}\n"
        f"📈 CSRep:\n{csrep_url}\n\n"
        f"🔥 Faceit Finder:\n{faceitfinder_url}\n\n"
        "──────────────────\n"
        "💎 CS2 Bot by xvorost"
    )


# =========================
# TELEGRAM BOT
# =========================


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    register_user(user_id)

    keyboard = [["📊 Give Stats + Faceit"]]

    await update.message.reply_text(
        "Wassup! 👋\nНатисніть кнопку або відразу відправте Steam посилання.",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
    )


async def users_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    register_user(user_id)

    users = load_json(USERS_FILE, [])

    await update.message.reply_text(f"👥 Bot users: {len(users)}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    register_user(user_id)

    text = update.message.text

    if text == "📊 Give Stats + Faceit":
        await update.message.reply_text("📎 Send Steam profile")
        return

    steamid = extract_steamid(text)

    if not steamid:
        await update.message.reply_text(
            "❌ Couldn't recognize the profile (Не зміг розпізнати профіль).\n\n"
            "Send a link like (Надішли посилання типу):\n"
            "https://steamcommunity.com/id/xvorost9/\n"
            "або\n"
            "https://steamcommunity.com/profiles/7656119..."
        )
        return

    card = build_card(steamid)

    await update.message.reply_text(
        card,
        disable_web_page_preview=True,
    )


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("users", users_count))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()


if __name__ == "__main__":
    main()
