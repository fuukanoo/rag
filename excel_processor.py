import pandas as pd
from io import BytesIO

def excel_processor(blob_data):
    try:
        df = pd.read_excel(BytesIO(blob_data), sheet_name=None)
        extracted_text = df.to_string(index=False)
        
        return extracted_text.strip()

    except Exception as e:
        return f"Error processing the Excel document: {e}"
