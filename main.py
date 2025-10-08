import os
import json
import http.client
import requests
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- Keep-alive web server ---
app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "🤖 Telegram bot is running!"

def run_keepalive():
    app_flask.run(host="0.0.0.0", port=8080)

def keep_alive():
    t = Thread(target=run_keepalive)
    t.start()
# --- End keep-alive server ---

# In-memory store for user API keys
user_api_keys = {}

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # Set this in your .env or environment

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Send me an image and I’ll edit it using RapidAPI!\n\n"
        "Use /api <your_api_key> to set your own RapidAPI key."
    )

# /api command — store user key
async def set_api_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text("❗ Usage: /api <your_rapidapi_key>")
        return

    api_key = context.args[0]
    user_api_keys[update.effective_user.id] = api_key
    await update.message.reply_text("✅ Your RapidAPI key has been saved!")

# Handle photos
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    api_key = user_api_keys.get(user_id)

    if not api_key:
        await update.message.reply_text(
            "⚠️ You haven’t set your RapidAPI key yet.\nUse /api <your_key> first."
        )
        return

    try:
        # Get Telegram image URL
        file = await update.message.photo[-1].get_file()
        image_url = file.file_path

        # Prepare request
        payload = json.dumps({
            "prompt": "Mix the two items creatively",
            "image": [image_url],
            "stream": False,
            "return": "url_image"
        })

        headers = {
            'x-rapidapi-key': api_key,
            'x-rapidapi-host': "gemini-2-5-flash-image-nano-banana1.p.rapidapi.com",
            'Content-Type': "application/json"
        }

        # Send request
        conn = http.client.HTTPSConnection("gemini-2-5-flash-image-nano-banana1.p.rapidapi.com")
        conn.request("POST", "/api/gemini", payload, headers)
        res = conn.getresponse()
        data = res.read()
        conn.close()

        response_text = data.decode("utf-8")
        response_json = json.loads(response_text)

        # Detect quota error
        if "quota" in response_text.lower() or "limit" in response_text.lower():
            await update.message.reply_text("🚫 Your RapidAPI quota/limit is exhausted.")
            return

        # Get image URL from response
        edited_image_url = response_json.get("image_url")

        if not edited_image_url:
            await update.message.reply_text("❗ Could not get edited image from API.")
            return

        # Send final image
        await update.message.reply_photo(photo=edited_image_url)

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
        print("Error in handle_photo:", e)

# --- Run everything ---
def main():
    keep_alive()  # Start Flask keep-alive
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(C
