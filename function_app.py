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


blob_storage_connection_string = os.getenv("BLOB_STORAGE_CONNECTION_STRING")
blob_storage_container = "container-rag-dev"
openai.api_key = os.getenv("OPENAI_KEY")
openai.azure_endpoint = os.getenv("OPENAI_ENDPOINT")
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
    if not file_name:
        return func.HttpResponse("file_name is missing in the request", status_code=400)

    extracted_text = extract_text(blob_storage_container, file_name)
    if extracted_text.startswith("Error"):
        return func.HttpResponse(f"Error extracting text: {extracted_text}", status_code=500)

    improved_text = improve_text(extracted_text)
    if improved_text.startswith("Error"):
        return func.HttpResponse(f"Error improving text: {improved_text}", status_code=500)

    logging.info(f"Improved text:\n {improved_text}")
    return func.HttpResponse(improved_text, status_code=200, mimetype="text/plain")


def improve_text(text):
    
    prompt = (f"以下の文章を修正し、返却してください。:\n{text}")

    try:
        response = openai.chat.completions.create(
            model="gpt-35-turbo",
            messages=[
                {"role": "system", "content": "あなたはとても親切なアシスタントです。"},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1000,
            temperature=0.4,
        )
        response_text = response.choices[0].message.content.strip()
        return response_text

    except openai.OpenAIError as e:
        return f"Error during OpenAI request: {e}"


def extract_text(blob_storage_container, blob_name):
    """
    Azure Blob Storageからファイルを取得し、ファイルタイプに応じてテキストを抽出する関数
    """
    blob_service_client = BlobServiceClient.from_connection_string(blob_storage_connection_string)
    blob_client = blob_service_client.get_blob_client(container=blob_storage_container, blob=blob_name)

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
