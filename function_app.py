import azure.functions as func

import os

import openai

from io import BytesIO

import tempfile

import uuid

import datetime

import json

from azure.functions import HttpResponse

from azure.storage.blob import BlobServiceClient

from langchain import hub

from langchain_openai import AzureChatOpenAI

from langchain_community.document_loaders import AzureAIDocumentIntelligenceLoader

from langchain_openai import AzureOpenAIEmbeddings

from langchain.schema import StrOutputParser

from langchain.schema.runnable import RunnablePassthrough

from langchain.text_splitter import MarkdownHeaderTextSplitter

from langchain.vectorstores.azuresearch import AzureSearch

from azure.cosmos import CosmosClient
 
# 環境変数や再利用可能な設定の読み込み

openai.api_key = os.getenv("OPENAI_KEY")

openai.azure_endpoint = os.getenv("OPENAI_ENDPOINT")

document_intelligence_key = os.getenv("DOCUMENT_INTELLIGENCE_KEY")

document_intelligence_endpoint = os.getenv("DOCUMENT_INTELLIGENCE_ENDPOINT")

blob_storage_connection_string = os.getenv("BLOB_STORAGE_CONNECTION_STRING")

blob_storage_container = "container-rag-dev"

vector_store_address = os.getenv("AI_SEARCH_ENDPOINT")

vector_store_password = os.getenv("AI_SEARCH_ADMIN_KEY")

index_name = "idx-rag-dev"

cosmos_db_key = os.getenv("COSMOS_DB_KEY")

cosmos_db_endpoint = os.getenv("COSMOS_DB_ENDPOINT")

cosmos_db_name = "rag-dev-db"

cosmos_container_name = "documents"
 
 
# Azureの各サービスクライアントを初期化

blob_service_client = BlobServiceClient.from_connection_string(

    blob_storage_connection_string

)
 
cosmos_service_client = CosmosClient(cosmos_db_endpoint, cosmos_db_key)

cosmos_db_client = cosmos_service_client.get_database_client(cosmos_db_name)

cosmos_container_client = cosmos_db_client.get_container_client(cosmos_container_name)
 
# EmbeddingsとVector Storeのセットアップ

aoai_embeddings = AzureOpenAIEmbeddings(

    azure_deployment="text-embedding-ada-002",

    openai_api_version="2023-05-15",

    api_key=openai.api_key,

    azure_endpoint=openai.azure_endpoint,

)
 
vector_store = AzureSearch(

    azure_search_endpoint=vector_store_address,

    azure_search_key=vector_store_password,

    index_name=index_name,

    embedding_function=aoai_embeddings.embed_query,

)
 
# Text splitterの設定

headers_to_split_on = [("#", "Header 1"), ("##", "Header 2"), ("###", "Header 3")]

text_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
 
# LLM promptの読み込み

prompt = hub.pull("rlm/rag-prompt")
 
# LLMインスタンスの作成

llm = AzureChatOpenAI(

    openai_api_version="2023-05-15",

    azure_deployment="gpt-35-turbo",

    temperature=0,

    api_key=openai.api_key,

    azure_endpoint=openai.azure_endpoint,

)
 
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)
 
 
@app.route(route="main")

def main(req: func.HttpRequest) -> func.HttpResponse:

    req_body = req.get_json()

    file_name = req_body.get("file_name")
 
    # Blobデータの取得と一時ファイルの作成

    blob_client = blob_service_client.get_blob_client(

        container=blob_storage_container, blob=file_name

    )

    blob_data = blob_client.download_blob().readall()
 
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:

        temp_file.write(blob_data)

        temp_file_path = temp_file.name
 
    try:

        # ドキュメントのロードとスプリット

        loader = AzureAIDocumentIntelligenceLoader(

            file_path=temp_file_path,

            api_key=document_intelligence_key,

            api_endpoint=document_intelligence_endpoint,

            api_model="prebuilt-layout",

        )

        docs = loader.load()

        docs_string = "\n\n".join(doc.page_content for doc in docs)

        splits = text_splitter.split_text(docs_string)
 
        # Vector Storeへの追加

        vector_store.add_documents(documents=splits)

        retriever = vector_store.as_retriever(search_type="similarity")

        retrieved_docs = retriever.get_relevant_documents(

            "ロードショーについて教えて。"

        )
 
        for doc in retrieved_docs:

            print(doc.page_content)
 
        # RAGチェーンのセットアップと実行

        rag_chain = (

            {"context": retriever | format_docs, "question": RunnablePassthrough()}

            | prompt

            | llm

            | StrOutputParser()

        )
 
        question = "ロードショーについてより詳細に教えて。"

        answer = rag_chain.invoke(question)
 
        response = save_cosmos(file_name, question, answer)
 
        return HttpResponse(

            body=json.dumps(response), status_code=200, mimetype="application/json"

        )
 
    finally:

        # 一時ファイルの削除

        os.remove(temp_file_path)
 
 
def format_docs(docs):

    return "\n\n".join(doc.page_content for doc in docs)
 
 
def save_cosmos(file_name, question, answer):

    item = {

        "id": str(uuid.uuid4()),

        "file_name": file_name,

        "question": question,

        "answer": answer,

        "timestamp": datetime.datetime.now().isoformat()

    }

    cosmos_container_client.upsert_item(item)

    return item
 