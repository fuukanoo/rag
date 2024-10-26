import fitz  # PyMuPDF
from io import BytesIO

def pdf_processor(blob_data):
    try:
        pdf = fitz.open(stream=BytesIO(blob_data), filetype="pdf")
        extracted_text = ""
        
        for page_num in range(len(pdf)):
            page = pdf.load_page(page_num)
            extracted_text += page.get_text("text") + "\n"

        return extracted_text.strip()

    except Exception as e:
        return f"Error processing the PDF document: {e}"
