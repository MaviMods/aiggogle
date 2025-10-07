from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai
from PIL import Image
from io import BytesIO

# Initialize Google GenAI client
client = genai.Client(api_key="AIzaSyDcCsCvsmtCBSv1EGLCJwPfQNZTSRLj79Q")

# Hardcoded prompt
PROMPT = "take image as reference , A woman with a fair skin tone and warm undertones, glowing with sweat. She has defined facial features, bold eyebrows, and lipstick. She is dressed in a short sports bra with thin straps and a small front cutout. her tummy midriff visible. She accessorizes with small gold hoop earrings and a delicate gold chain with a pendant. keep the body measurements and facial details same as the uploaded photo as possible. same reference inage background. same pose and expression as original photo."

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
