from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO

client = genai.Client()

prompt = (
    "Create a high quality, ultra- realistic portrait of 8k, of same   woman, from the uploaded image, keep her face and features exactly the same (no face change), young women wearing colour bikini triangle cut out on front. seeing from front,showing full body pose, and background same as reference as posible ",
)

image = Image.open("/shiva.jpg")

response = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=[prompt, image],
)

for part in response.candidates[0].content.parts:
    if part.text is not None:
        print(part.text)
    elif part.inline_data is not None:
        image = Image.open(BytesIO(part.inline_data.data))
        image.save("generated_image.png")
