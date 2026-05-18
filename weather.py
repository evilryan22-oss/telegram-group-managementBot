"""/weather <location> — uses wttr.in (no API key required)."""
from __future__ import annotations

import logging
import urllib.parse
from typing import Optional

import asyncio

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from utils.helpers import safe_html

log = logging.getLogger(__name__)


def _fetch_weather_sync(location: str) -> Optional[dict]:
    import json
    from urllib.request import Request, urlopen
    from urllib.error import URLError, HTTPError
    url = f"https://wttr.in/{urllib.parse.quote(location)}?format=j1"
    req = Request(url, headers={"User-Agent": "TelegramBot/1.0"})
    try:
        with urlopen(req, timeout=10) as resp:
            data = resp.read().decode("utf-8", errors="replace")
        return json.loads(data)
    except (URLError, HTTPError, ValueError, TimeoutError) as e:
        log.warning("Weather fetch failed for %r: %s", location, e)
        return None


async def cmd_weather(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.effective_message.reply_text(
            "Usage: /weather <city or place>\nExample: /weather Lagos"
        )
        return
    location = " ".join(context.args).strip()
    data = await asyncio.to_thread(_fetch_weather_sync, location)
    if not data:
        await update.effective_message.reply_text(
            f"⚠️ Could not fetch weather for <b>{safe_html(location)}</b>.",
            parse_mode=ParseMode.HTML,
        )
        return
    try:
        cur = data["current_condition"][0]
        area = data["nearest_area"][0]
        place = ", ".join(filter(None, [
            area["areaName"][0]["value"],
            area["region"][0]["value"],
            area["country"][0]["value"],
        ]))
        desc = cur["weatherDesc"][0]["value"]
        temp_c = cur["temp_C"]
        feels_c = cur["FeelsLikeC"]
        humidity = cur["humidity"]
        wind = cur["windspeedKmph"]
        cloud = cur["cloudcover"]
        text = (
            f"🌤️ <b>Weather — {safe_html(place)}</b>\n"
            f"{safe_html(desc)}\n\n"
            f"🌡 Temp: <b>{safe_html(temp_c)}°C</b> (feels {safe_html(feels_c)}°C)\n"
            f"💧 Humidity: {safe_html(humidity)}%\n"
            f"💨 Wind: {safe_html(wind)} km/h\n"
            f"☁️ Cloud: {safe_html(cloud)}%"
        )
    except (KeyError, IndexError, TypeError) as e:
        log.warning("Weather parse error: %s", e)
        text = f"⚠️ Got bad data for <b>{safe_html(location)}</b>."
    await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)
