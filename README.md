# Excel to PDF Conversion API Service

Excel ファイル（.xlsx、.xls）を PDF 形式に変換する REST API サービス。

## 機能

- Excel ファイルを PDF に変換
- 複数シートのサポート
- 表構造と基本的な書式の保持
- ファイルサイズ制限: 10MB
- 堅牢なエラー処理

## 技術スタック

- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Excel Parsing**: openpyxl (.xlsx), xlrd (.xls)
- **PDF Generation**: ReportLab
- **Dependency Management**: uv
- **Testing**: pytest

## 型ヒント方針

このプロジェクトでは、Python の型ヒント（type hints, type annotations）を積極的に使用します。

- すべての関数とメソッドに型ヒントを追加
- mypy strict モードで検証
- 型の安全性を確保し、IDE のサポートを最大化

## セットアップ

### 前提条件

- Python 3.11 以上
- uv（推奨）または pip

### インストール

```bash
# uv を使用する場合
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"

# pip を使用する場合
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## 使用方法

### サーバー起動

```bash
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### API リクエスト例

```bash
# Excel ファイルを PDF に変換
curl -X POST "http://localhost:8000/convert" \
  -F "file=@example.xlsx" \
  --output result.pdf

# ヘルスチェック
curl "http://localhost:8000/health"
```

## 開発

### テスト実行

```bash
pytest tests/
```

### 型チェック

```bash
mypy src/
```

## プロジェクト構造

```
pdf-transformer/
├── src/
│   ├── models/          # データモデル (Pydantic)
│   ├── services/        # ビジネスロジック
│   │   ├── converter/   # Excel→PDF変換
│   │   └── storage/     # ファイルストレージ
│   ├── api/             # FastAPI エンドポイント
│   │   ├── routes/      # ルート定義
│   │   └── middleware/  # ミドルウェア
│   ├── lib/             # 共通ユーティリティ
│   ├── config.py        # 環境設定
│   └── main.py          # アプリケーションエントリポイント
├── tests/
│   ├── integration/     # 統合テスト
│   └── fixtures/        # テスト用データ
├── pyproject.toml       # プロジェクト設定
└── README.md
```

## API ドキュメント

サーバー起動後、以下の URL で API ドキュメントを確認できます:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## セキュリティ

- ファイルサイズ制限（10MB）
- 多層ファイル検証（拡張子、MIME タイプ、magic number）
- 一時ファイルの安全なクリーンアップ
- ログの機密情報サニタイズ

## ライセンス

このプロジェクトは MIT ライセンスの下でライセンスされています。
