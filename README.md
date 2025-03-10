# AGENT-TOOLS-PYTHON

## 概要

このプロジェクトは、LangChainとLangGraphを使用して、大規模言語モデル（LLM）によるワークフローを用いた各種ツールを提供しています。

## 主な機能

### 月報生成
- 指定されたディレクトリから作業日報ファイルを自動検索
- 作業日報から必要な情報を抽出（GPT-4oモデルを使用）
- 抽出された情報を基に月報（Excel形式）を自動生成
- 複数の作業日報を処理し、一つの月報にまとめる機能

## 必要条件

- Docker と Docker Compose
- OpenAI API キー（GPT-4oモデルを使用するため）
- LangChain API キー（オプション、トレーシング機能を使用する場合）

## セットアップ

1. リポジトリをクローン
2. `.env.example` ファイルを `.env` にコピーし、必要な API キーを設定
3. Docker Compose でコンテナを起動

```bash
cp .env.example .env
# .env ファイルを編集して API キーを設定
docker-compose up -d
```

## 使用方法

### 月報生成

```bash
docker-compose exec python python src/monthly_report_agent.py \
  -w "作業者名" \
  -c "参画企業名" \
  -m "対象年月（例: 202502）" \
  -i "入力ディレクトリ（inputsディレクトリからの相対パス）"
```

#### パラメータ

- `-w, --worker`: 作業者名（必須）
- `-c, --company`: 参画企業名（必須）
- `-m, --month`: 対象年月（例: 202502）（必須）
- `-i, --input`: 入力ディレクトリ（inputsディレクトリからの相対パス）（オプション）

## プロジェクト構造

```
.
├── data/
│   ├── inputs/      # 入力ディレクトリ
│   ├── outputs/     # 出力ディレクトリ
│   └── templates/   # 各種テンプレート
├── src/
│   ├── monthly_report_agent.py  # 月報生成の主要スクリプト
│   └── lib/         # ライブラリモジュール
├── .env.example     # 環境変数の設定例
├── docker-compose.yml  # Docker Compose 設定
└── Dockerfile       # Docker イメージ定義
```

## 技術スタック

- Python 3.10+
- LangChain: LLMとのインターフェース
- LangGraph: ワークフロー構築フレームワーク
- OpenAI GPT-4o: 情報抽出のためのLLM
- openpyxl: Excelファイル操作

## 注意事項

### 月報生成

- 作業日報ファイルは、ファイル名に「作業日報」を含む必要があります
- 月報自動生成スクリプト実行前に、月報テンプレートの対象年月を手動で更新する必要があります
    - 月報のテンプレートは `data/templates/monthly_work_report_template.xlsx` に保存されています
- 生成された月報は `data/outputs/` ディレクトリに保存されます
