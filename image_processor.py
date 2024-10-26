from io import BytesIO
from PIL import Image
import pytesseract

def image_processor(blob_data):
    try:
        img = Image.open(BytesIO(blob_data))
        extracted_text = pytesseract.image_to_string(img)
        
        return extracted_text.strip()

    except Exception as e:
        return f"Error processing the image: {e}"