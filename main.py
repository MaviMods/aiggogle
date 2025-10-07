from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai
from PIL import Image
from io import BytesIO

# Initialize Google GenAI client
client = genai.Client()

# Hardcoded prompt
PROMPT = "Create a picture of my cat eating a nano-banana in a fancy restaurant under the Gemini constellation"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me a photo, and I will edit it with the hardcoded prompt!")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Get the photo file from Telegram
    file = await update.message.photo[-1].get_file()
    file_bytes = BytesIO()
    await file.download(out=file_bytes)
    file_bytes.seek(0)
    
    # Open the image
    image = Image.open(file_bytes)

    # Send to GenAI for editing
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

# Run the bot
app = ApplicationBuilder().token("8462144861:AAGvDzBSvw9VcXdxgF3FgIxbFqtujfcdRK0").build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
app.run_polling()
