from docx import Document
from io import BytesIO

def word_processor(blob_data):
    try:
        doc = Document(BytesIO(blob_data))
        extracted_text = "\n".join([para.text for para in doc.paragraphs])
        
        return extracted_text.strip()

    except Exception as e:
        return f"Error processing the Word document: {e}"