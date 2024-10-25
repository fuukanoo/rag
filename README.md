# Azure Computer Vision、Azure OpenAIによる画像解析とテキスト抽出プロジェクト

このプロジェクトは、Azure Functionsを使用してAzure Computer Vision APIで画像を解析し、抽出されたテキストをAzure OpenAI APIで処理・修正するワークフローを実現します。


## 目次

1. [プロジェクト概要](#プロジェクト概要)
2. [前提条件](#前提条件)
3. [環境設定](#環境設定)
4. [インストール手順](#インストール手順)
5. [使用方法](#使用方法)
6. [プロジェクトの構造](#プロジェクトの構造)
7. [エラーハンドリング](#エラーハンドリング)
8. [ライセンス](#ライセンス)


## プロジェクト概要

このプロジェクトは、Azure Computer Vision APIを使用して画像からテキストを抽出し、Azure OpenAI APIを使ってそのテキストを修正する、Azure Functionsを用いたサーバーレスアプリケーションです。


## 前提条件

このプロジェクトを動かすために必要なツールやリソース

- **Azure サブスクリプション**
- **Azure Functions Core Tools**
- **Azure Computer Vision API**
- **Azure OpenAI API**
- **Python 3.10
- **VSCode**
- **Azure CLI**


## 環境構築

### 仮想環境の構築と必要なライブラリにインストール
```
pyenv local 3.10.15
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### local_settings.jsonで環境変数の設定
```
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "COMPUTER_VISION_KEY": "your_computer_vision_key",
    "COMPUTER_VISION_ENDPOINT": "your_computer_vision_endpoint",
    "OPENAI_KEY": "your_openai_key,
    "OPENAI_ENDPOINT": "your_openai_endpoint"
  }
}
```
