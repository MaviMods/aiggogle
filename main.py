import os
import json
import http.client
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
load_dotenv()

# Load environment variables
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")  # Your RapidAPI key

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me an image and I will edit it via RapidAPI!")

# Handle photos
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Get the highest resolution image file URL from Telegram
        file = await update.message.photo[-1].get_file()
        image_url = file.file_path  # Telegram file URL

        # Prepare RapidAPI payload
        payload = json.dumps({
            "prompt": "take image as reference , A woman with a fair skin tone and warm undertones, glowing with sweat. She has defined facial features, bold eyebrows, and lipstick. She is dressed in a short sports bra with thin straps and a small front cutout. her tummy midriff visible. She accessorizes with small gold hoop earrings and a delicate gold chain with a pendant. keep the body measurements and facial details same as the uploaded photo as possible. same reference inage background.",
            "image": [image_url],  # send Telegram image URL directly
            "stream": False,
            "return": "url_image"
        })

        headers = {
            'x-rapidapi-key': RAPIDAPI_KEY,
            'x-rapidapi-host': "gemini-2-5-flash-image-nano-banana1.p.rapidapi.com",
            'Content-Type': "application/json"
        }

        # Send request to RapidAPI
        conn = http.client.HTTPSConnection("gemini-2-5-flash-image-nano-banana1.p.rapidapi.com")
        conn.request("POST", "/api/gemini", payload, headers)
        res = conn.getresponse()
        data = res.read()
        conn.close()

        # Parse response
        response_json = json.loads(data.decode("utf-8"))
        edited_image_url = response_json.get("image_url")

        if not edited_image_url:
            await update.message.reply_text("Could not get edited image from API.")
            return

        # Send edited image URL to Telegram
        await update.message.reply_photo(photo=edited_image_url)

    except Exception as e:
        await update.message.reply_text(f"An error occurred: {e}")
        print("Error in handle_photo:", e)

# Run bot
if not BOT_TOKEN or not RAPIDAPI_KEY:
    raise ValueError("Set TELEGRAM_BOT_TOKEN and RAPIDAPI_KEY environment variables.")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
app.run_polling()
