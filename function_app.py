import azure.functions as func
import logging
import os
import requests
import openai
import time

# Azure Functionsアプリケーションのエントリポイント
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# 環境変数からAPIキーとエンドポイントを取得
COMPUTER_VISION_KEY = os.getenv('COMPUTER_VISION_KEY')
COMPUTER_VISION_ENDPOINT = os.getenv('COMPUTER_VISION_ENDPOINT')
openai.api_key = os.getenv('OPENAI_KEY')
openai.azure_endpoint = os.getenv('OPENAI_ENDPOINT')  # Azure OpenAIのエンドポイント
openai.api_type = 'azure'
openai.api_version = '2023-08-01-preview'


# APIキーとエンドポイントが設定されているかチェック
if not COMPUTER_VISION_KEY or not COMPUTER_VISION_ENDPOINT:
    raise ValueError("Computer Vision APIのキーまたはエンドポイントが設定されていません。")
if not openai.api_key or not openai.azure_endpoint:
    raise ValueError("OpenAI APIのキーまたはエンドポイントが設定されていません。")


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
                
                else:
                # ステータスがまだ存在しない場合
                    print("ステータスが未設定。再試行中...")

            # 少し待機してから再試行 (3秒待つ)
                time.sleep(3)

            if ocr_result['status'] == 'succeeded':
                # 抽出されたテキストの組み立て
                extracted_text = ""
                for read_result in ocr_result["analyzeResult"]["readResults"]:
                    for line in read_result["lines"]:
                        extracted_text += line["text"] + "\n"

                logging.info(f"抽出されたテキスト: {extracted_text}")

                # OpenAI APIを使用してテキストを訂正
                response = openai.chat.completions.create(
                    model="gpt-35-turbo",
                    messages=[
                        {"role": "system", "content": "あなたは親切なアシスタントです。"},
                        {"role": "user", "content": f"以下の文章を修正してください。:\n{extracted_text}"}
                    ],
                    temperature=0.4,
                    max_tokens=1000
                )

                corrected_text = response.choices[0].message.content.strip()

                # 訂正後のテキストを返却
                return func.HttpResponse(
                f"修正されたテキスト: {corrected_text}",
                mimetype="text/plain",
                status_code=200)


            else:
                return func.HttpResponse("画像解析に失敗しました.", status_code=500)

        except requests.exceptions.RequestException as e:
            logging.error(f"Computer Vision APIの呼び出し中にエラーが発生しました。: {e}")
            return func.HttpResponse(f"画像処理中にエラーが発生しました。: {e}", status_code=500)

        except openai.OpenAIError as e:
            logging.error(f"OpenAI APIの呼び出し中にエラーが発生しました: {e}")
            return func.HttpResponse(f"OpenAI APIでエラーが発生しました: {e}", status_code=500)
