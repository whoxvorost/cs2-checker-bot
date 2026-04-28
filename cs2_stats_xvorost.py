import json
from pathlib import Path
from dotenv import load_dotenv
import os
import re
import requests

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)


BASE_DIR = Path(__file__).resolve().parent

dotenv_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=dotenv_path)

TOKEN = os.getenv("TELEGRAM_TOKEN")
STEAM_API_KEY = os.getenv("STEAM_API_KEY")

CACHE_FILE = BASE_DIR / "steam_cache.json"



# =========================
# КЕШ
# =========================

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    return {}


def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as file:
        json.dump(cache, file, indent=4)


steam_cache = load_cache()


# =========================
# STEAM
# =========================

def resolve_vanity(vanity: str):
    """
    Переробляє id з текстом на сток id steam[7437432894]
    """

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
            save_cache(steam_cache)

            return steamid

    except Exception as error:
        print(f"Steam API error: {error}")

    return None


def extract_steamid(text: str):
    """
    дістає id steam з посилання
    """

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
    keyboard = [["📊 Give Stats + Faceit"]]

    await update.message.reply_text(
        "Wassup! 👋\nНатисніть кнопку або відразу відправте Steam посилання.",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📊 Give Stats + Faceit":
        await update.message.reply_text("📎 Send Steam profile")
        return

    steamid = extract_steamid(text)

    if not steamid:
        await update.message.reply_text(
            "❌ Couldn't recognize the profile (Не зміг розпізнати профіль).\n\n"
            "Send a link like(Надішли посилання типу):\n"
            "https://steamcommunity.com/id/xvorost9/\n"
            "или\n"
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
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()


if __name__ == "__main__":
    main()

