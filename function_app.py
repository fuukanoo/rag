import azure.functions as func
import os
import openai
from azure.storage.blob import BlobServiceClient
import logging
import mimetypes


from image_processor import image_processor
from pdf_processor import pdf_processor
from word_processor import word_processor
from excel_processor import excel_processor
from ppt_processor import ppt_processor


#computer_vision_key = os.getenv("COMPUTER_VISION_API_KEY")
#computer_vision_endpoint = os.getenv("COMPUTER_VISION_ENDPOINT")
#document_intelligence_key = os.getenv("DOCUMENT_INTELLIGENCE_API_KEY")
#document_intelligence_endpoint = os.getenv("DOCUMENT_INTELLIGENCE_ENDPOINT")
blob_storage_connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
blob_storage_container = os.getenv("BLOB_CONTAINER")
openai.api_key = os.getenv("AZURE_OPENAI_API_KEY")
openai.azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")  
openai.api_type = "azure"
openai.api_version = "2023-05-15"

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="main")
def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing a request to extract and improve text from an image or document.')

    try:
        req_body = req.get_json()
    except ValueError:
        return func.HttpResponse("Invalid JSON format", status_code=400)

    file_name = req_body.get("file_name")

    extracted_text = extract_text(blob_storage_container, file_name)

    improved_text = improve_text(extracted_text)
    logging.info(f"Improved text:\n {improved_text}")

    return func.HttpResponse(improved_text, status_code=200)


@app.route(route="improve_text")
def improve_text(text):
    
    prompt = (f"以下の文章で誤りがあれば訂正してください、ない場合は元の文章を返却してください:\n{text}")

    try:
        response = openai.chat.completions.create(
            model="gpt-35-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant "},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1000,
            temperature=0.4,
        )
        message_content = response.choices[0].message.content.strip()
        return message_content

    except openai.OpenAIError as e:
        return f"Error during OpenAI request: {e}"


@app.route(route="extract_text")
def extract_text(blob_container, blob_name):
    blob_service_client = BlobServiceClient.from_connection_string(blob_storage_connection_string)
    blob_client = blob_service_client.get_blob_client(container=blob_container, blob=blob_name)

    try:
        blob_data = blob_client.download_blob().readall()
        mime_type, _ = mimetypes.guess_type(blob_name)

        if mime_type and mime_type.startswith("image"):
            return image_processor(blob_data)
        elif mime_type == "application/pdf":
            return pdf_processor(blob_data)
        elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return word_processor(blob_data)
        elif mime_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
            return excel_processor(blob_data)
        elif mime_type == "application/vnd.openxmlformats-officedocument.presentationml.presentation":
            return ppt_processor(blob_data)
        else:
            return "Error: Unsupported file type."

    except Exception as e:
        return f"Error processing the blob: {e}"