import os
import json
import base64
import requests
from io import BytesIO
from PIL import Image
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import http.client
from dotenv import load_dotenv
load_dotenv()

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
        # Download photo from Telegram
        file = await update.message.photo[-1].get_file()
        file_bytes = BytesIO(await file.download_as_bytearray())
        file_bytes.seek(0)

        # Convert to base64
        import base64
        image_base64 = base64.b64encode(file_bytes.read()).decode("utf-8")

        # Prepare RapidAPI payload
        payload = json.dumps({
            "prompt": "take image as reference , A woman with a fair skin tone and warm undertones, glowing with sweat. She has defined facial features, bold eyebrows, and lipstick. She is dressed in a short sports bra with thin straps and a small front cutout. her tummy midriff visible. She accessorizes with small gold hoop earrings and a delicate gold chain with a pendant. keep the body measurements and facial details same as the uploaded photo as possible. same reference inage background. same pose and expression as original photo.",
            "image": [image_base64],
            "stream": False,
            "return": "url_image"  # we get a URL
        })

        headers = {
            'x-rapidapi-key': os.getenv("RAPIDAPI_KEY"),
            'x-rapidapi-host': "gemini-2-5-flash-image-nano-banana1.p.rapidapi.com",
            'Content-Type': "application/json"
        }

        # Send request
        conn = http.client.HTTPSConnection("gemini-2-5-flash-image-nano-banana1.p.rapidapi.com")
        conn.request("POST", "/api/gemini", payload, headers)
        res = conn.getresponse()
        data = res.read()
        conn.close()

        # Parse JSON response
        response_json = json.loads(data.decode("utf-8"))
        print("API response:", response_json)  # for debugging

        # Get the image URL
        image_url = response_json.get("image_url")
        if not image_url:
            await update.message.reply_text("Could not get edited image from API.")
            return

        # Download image from URL
        img_data = requests.get(image_url).content
        edited_bytes = BytesIO(img_data)
        edited_image = Image.open(edited_bytes)

        # Send edited image back to Telegram
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
