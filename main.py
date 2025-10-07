import os
from io import BytesIO
from PIL import Image
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai
from dotenv import load_dotenv
load_dotenv()

# Load environment variables (you should have a .env file or set these in your system)
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GENAI_API_KEY = os.getenv("GENAI_API_KEY")

# Initialize Google GenAI client with API key
client = genai.Client(api_key=GENAI_API_KEY)

# Hardcoded prompt
PROMPT = "take image as reference , A woman with a fair skin tone and warm undertones, glowing with sweat. She has defined facial features, bold eyebrows, and lipstick. She is dressed in a short sports bra with thin straps and a small front cutout. her tummy midriff visible. She accessorizes with small gold hoop earrings and a delicate gold chain with a pendant. keep the body measurements and facial details same as the uploaded photo as possible. same reference inage background. same pose and expression as original photo."

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send me a photo, and I will edit it with the hardcoded prompt!"
    )

# Handle incoming photos
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Get the highest resolution photo from Telegram
        file = await update.message.photo[-1].get_file()

        # Download the photo as byte array (new method in v20+)
        file_bytes = BytesIO(await file.download_as_bytearray())
        file_bytes.seek(0)

        # Open the image with PIL
        image = Image.open(file_bytes)

        # Send to Google GenAI for editing
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[PROMPT, image]
        )

        # Get the edited image
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                edited_image = Image.open(BytesIO(part.inline_data.data))
                output_bytes = BytesIO()
                edited_image.save(output_bytes, format="PNG")
                output_bytes.seek(0)
                await update.message.reply_photo(photo=InputFile(output_bytes))
                return

        await update.message.reply_text("Sorry, I couldn't edit your image.")

    except Exception as e:
        await update.message.reply_text(f"An error occurred: {e}")
        print("Error in handle_photo:", e)

# Run the bot
if BOT_TOKEN is None:
    raise ValueError("Please set the TELEGRAM_BOT_TOKEN environment variable.")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
app.run_polling()
