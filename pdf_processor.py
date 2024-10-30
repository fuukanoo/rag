from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
import os

document_intelligence_key = os.getenv("DOCUMENT_INTELLIGENCE_KEY")
document_intelligence_endpoint = os.getenv("DOCUMENT_INTELLIGENCE_ENDPOINT")

document_analysis_client = DocumentAnalysisClient(
    credential=AzureKeyCredential(document_intelligence_key),
    endpoint=document_intelligence_endpoint
)

def pdf_processor(blob_data):
    try:
        poller = document_analysis_client.begin_analyze_document("prebuilt-document", blob_data)
        result = poller.result()

        extracted_text = ""
        
        for page_num, page in enumerate(result.pages):
            page_text = ""
            
            for line in page.lines:
                page_text += line.content + "\n"

            if page_text:
                extracted_text += f"--- Page {page_num + 1} ---\n" + page_text.strip() + "\n\n"
            else:
                extracted_text += f"Error extracting text on page {page_num + 1}.\n\n"

        return extracted_text.strip()

    except Exception as e:
        return f"Error processing the PDF document: {e}"
