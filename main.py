import os
import json
import requests
from io import BytesIO
from PIL import Image
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import http.client

# Load environment variables
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")  # Your RapidAPI key

# Hardcoded prompt for edits
PROMPT = "Edit this image according to the prompt: make it fancy and magical"

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me a photo, and I will edit it using RapidAPI!")

# Handle incoming photos
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Download photo from Telegram as byte array
        file = await update.message.photo[-1].get_file()
        file_bytes = BytesIO(await file.download_as_bytearray())
        file_bytes.seek(0)

        # Option 1: Upload image to image hosting and use URL (simplest)
        # Here, we'll use a free image hosting service (or you can use your own)
        # For simplicity, let's assume user sends a URL
        # If you want to upload to RapidAPI directly, the API must support base64 input

        # Convert image to base64
        image_base64 = base64.b64encode(file_bytes.read()).decode("utf-8")

        # Prepare RapidAPI payload
        payload = json.dumps({
            "prompt": PROMPT,
            "image": [image_base64],  # Some RapidAPI endpoints support base64 directly
            "stream": False,
            "return": "base64_image"  # so we get the actual image bytes
        })

        headers = {
            'x-rapidapi-key': RAPIDAPI_KEY,
            'x-rapidapi-host': "gemini-2-5-flash-image-nano-banana1.p.rapidapi.com",
            'Content-Type': "application/json"
        }

        # Connect and send request
        conn = http.client.HTTPSConnection("gemini-2-5-flash-image-nano-banana1.p.rapidapi.com")
        conn.request("POST", "/api/gemini", payload, headers)
        res = conn.getresponse()
        data = res.read()
        conn.close()

        # Parse response
        response_json = json.loads(data.decode("utf-8"))

        # Extract base64 image
        edited_base64 = response_json['output'][0]['image']  # check exact path depending on API
        edited_bytes = BytesIO(base64.b64decode(edited_base64))
        edited_image = Image.open(edited_bytes)

        # Send back to Telegram
        output_bytes = BytesIO()
        edited_image.save(output_bytes, format="PNG")
        output_bytes.seek(0)
        await update.message.reply_photo(photo=InputFile(output_bytes))

    except Exception as e:
        await update.message.reply_text(f"An error occurred: {e}")
        print("Error in handle_photo:", e)

# Run bot
if BOT_TOKEN is None or RAPIDAPI_KEY is None:
    raise ValueError("Please set TELEGRAM_BOT_TOKEN and RAPIDAPI_KEY environment variables.")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
app.run_polling()
