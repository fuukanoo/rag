import azure.functions as func
import logging
import os
import requests
import openai

# Azure Functionsアプリケーションのエントリポイント
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# 環境変数からAPIキーとエンドポイントを取得
COMPUTER_VISION_KEY = os.getenv('COMPUTER_VISION_KEY')
COMPUTER_VISION_ENDPOINT = os.getenv('COMPUTER_VISION_ENDPOINT')
openai.api_key = os.getenv('OPENAI_KEY')
openai.azure_endpoint = os.getenv('OPENAI_ENDPOINT')  # Azure OpenAIのエンドポイント
openai.api_type = 'azure'
openai.api_version = '2023-08-01-preview'


# HTTPトリガー関数
@app.route(route="http_trigger")
def http_trigger(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    # リクエストから画像URLを取得
    image_url = req.params.get('image_url')
    if not image_url:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            image_url = req_body.get('image_url')

    if image_url:
        # OCR APIのURL
        ocr_url = f"{COMPUTER_VISION_ENDPOINT}/vision/v3.2/read/analyze"

        headers = {
            'Ocp-Apim-Subscription-Key': COMPUTER_VISION_KEY,
            'Content-Type': 'application/json'
        }
        data = {'url': image_url}

        try:
            # APIリクエストでOCRを実行
            response = requests.post(ocr_url, headers=headers, json=data)
            response.raise_for_status()

            # OCR結果の取得
            operation_url = response.headers["Operation-Location"]

            # OCRの結果を取得するためにポーリング
            ocr_result = {}
            while True:
                ocr_response = requests.get(operation_url, headers=headers)
                ocr_result = ocr_response.json()

                # 完了ステータスか確認
                if ocr_result['status'] in ['succeeded', 'failed']:
                    break

            if ocr_result['status'] == 'succeeded':
                # 抽出されたテキストの組み立て
                extracted_text = ""
                for read_result in ocr_result["analyzeResult"]["readResults"]:
                    for line in read_result["lines"]:
                        extracted_text += line["text"] + "\n"

                logging.info(f"Extracted text: {extracted_text}")

                # OpenAI APIを使用してテキストを訂正
                response = openai.chat.completions.create(
                    model="gpt-35-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": f"以下の文章をより詳細にし、その背景も述べてください。:\n{extracted_text}"}
                    ],
                    temperature=0.3,
                    max_tokens=1000
                )

                corrected_text = response.choices[0].message.content.strip()

                # 訂正後のテキストを返却
                return func.HttpResponse(f"Corrected Text:\n{corrected_text}", mimetype="text/plain")

            else:
                return func.HttpResponse("Failed to analyze image.", status_code=500)

        except requests.exceptions.RequestException as e:
            logging.error(f"Error calling the Computer Vision API: {e}")
            return func.HttpResponse(f"Error processing image: {e}", status_code=500)

    else:
        return func.HttpResponse(
            "Please pass an image_url in the query string or in the request body.",
            status_code=400
        )
