# Quickstart Guide: Excel から PDF への変換 API

**作成日**: 2025-12-29  
**機能**: [spec.md](spec.md)  
**計画**: [plan.md](plan.md)

## 概要

このガイドでは、Excel から PDF への変換 API サービスを最短でセットアップし、動作確認するための手順を説明します。

---

## 前提条件

以下がインストールされていることを確認してください：

- **Python 3.11 以上**
  ```bash
  python3 --version  # 3.11 以上であることを確認
  ```

- **uv**（Python 依存関係マネージャー）
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

- **Git**（ソースコード管理）
  ```bash
  git --version
  ```

---

## セットアップ手順

### 1. リポジトリのクローン

```bash
git clone https://github.com/ryk2025/pdf-transformer.git
cd pdf-transformer
```

### 2. ブランチの切り替え

```bash
git checkout 001-excel-pdf-api
```

### 3. 依存関係のインストール

```bash
# uv で仮想環境を作成し、依存関係をインストール
uv venv
source .venv/bin/activate  # Windows の場合: .venv\Scripts\activate

# 依存関係のインストール
uv pip install -e .
```

### 4. 開発サーバーの起動

```bash
# FastAPI サーバーを起動（ホットリロード有効）
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

サーバーが起動すると、以下のメッセージが表示されます：

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

---

## 動作確認

### ヘルスチェック

ブラウザまたは curl で以下にアクセス：

```bash
curl http://localhost:8000/health
```

**期待される応答**：
```json
{
  "status": "ok",
  "version": "0.1.0"
}
```

### API ドキュメントの確認

ブラウザで以下にアクセス：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

これらのページから、API エンドポイントの詳細を確認し、インタラクティブにテストできます。

---

## 基本的な使い方

### curl を使った変換

サンプル Excel ファイルを用意し、以下のコマンドで PDF に変換：

```bash
curl -X POST http://localhost:8000/convert \
  -F "file=@/path/to/your/sample.xlsx" \
  -o output.pdf
```

**成功例**：
```bash
# ファイルがダウンロードされ、output.pdf として保存される
# HTTP 200 OK が返される
```

**エラー例**：
```bash
# 無効なファイル形式の場合
curl -X POST http://localhost:8000/convert \
  -F "file=@/path/to/sample.txt"

# 応答:
{
  "error_type": "INVALID_FILE_FORMAT",
  "message": "サポートされていないファイル形式です。.xlsx または .xls ファイルをアップロードしてください。",
  "status_code": 400
}
```

---

### Python を使った変換

```python
import requests

# API エンドポイント
url = "http://localhost:8000/convert"

# Excel ファイルを読み込んで送信
with open("sample.xlsx", "rb") as f:
    files = {"file": ("sample.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    response = requests.post(url, files=files)

# 成功した場合、PDF を保存
if response.status_code == 200:
    with open("output.pdf", "wb") as pdf_file:
        pdf_file.write(response.content)
    print("変換成功！output.pdf が作成されました。")
else:
    print(f"エラー: {response.json()}")
```

---

### JavaScript (Node.js) を使った変換

```javascript
const fs = require('fs');
const FormData = require('form-data');
const axios = require('axios');

async function convertExcelToPdf() {
  const form = new FormData();
  form.append('file', fs.createReadStream('sample.xlsx'));

  try {
    const response = await axios.post('http://localhost:8000/convert', form, {
      headers: form.getHeaders(),
      responseType: 'arraybuffer'
    });

    fs.writeFileSync('output.pdf', response.data);
    console.log('変換成功！output.pdf が作成されました。');
  } catch (error) {
    console.error('エラー:', error.response.data);
  }
}

convertExcelToPdf();
```

---

## テスト実行

統合テストを実行：

```bash
# pytest でテストを実行
pytest tests/integration/ -v
```

**期待される出力**：
```
tests/integration/test_convert.py::test_convert_xlsx_success PASSED
tests/integration/test_convert.py::test_convert_xls_success PASSED
tests/integration/test_convert.py::test_invalid_format PASSED
tests/integration/test_convert.py::test_file_too_large PASSED
tests/integration/test_convert.py::test_corrupted_file PASSED
======================== 5 passed in 2.34s ========================
```

---

## トラブルシューティング

### 問題: `ModuleNotFoundError: No module named 'fastapi'`

**解決策**: 依存関係が正しくインストールされていません。

```bash
uv pip install -e .
```

### 問題: `ImportError: cannot import name 'app' from 'src.api.main'`

**解決策**: プロジェクトルートから実行していることを確認してください。

```bash
cd /path/to/pdf-transformer
uvicorn src.api.main:app --reload
```

### 問題: ファイルアップロードで 413 エラー

**解決策**: ファイルサイズが 10MB を超えています。より小さいファイルを使用するか、設定を変更してください。

### 問題: 変換が遅い（30秒以上）

**解決策**: 
- ファイルサイズを確認（5MB未満を推奨）
- シート数を確認（10シート未満を推奨）
- 大きなファイルの場合、処理時間が長くなる可能性があります

---

## 次のステップ

### 開発を進める

1. **コードの確認**: `src/` ディレクトリを探索し、実装を確認
2. **テストの追加**: `tests/integration/` にテストケースを追加
3. **機能の拡張**: 新しい変換機能（Word、画像）の追加を検討

### デプロイの準備

1. **環境変数の設定**: 本番環境用の設定を追加
2. **ロギングの設定**: 本番環境用のロギングを設定
3. **パフォーマンステスト**: 負荷テストを実行
4. **セキュリティ監査**: 依存関係の脆弱性スキャン

---

## サンプルファイル

テスト用のサンプル Excel ファイルは `tests/fixtures/` ディレクトリに含まれています：

- `simple.xlsx` - シンプルな表データ
- `multisheet.xlsx` - 複数シートを含むワークブック
- `formatted.xlsx` - 書式設定を含むファイル
- `large.xlsx` - 大きなデータセット（パフォーマンステスト用）

---

## リソース

- **API ドキュメント**: http://localhost:8000/docs
- **OpenAPI 仕様**: [contracts/api.yaml](contracts/api.yaml)
- **データモデル**: [data-model.md](data-model.md)
- **技術調査**: [research.md](research.md)
- **機能仕様**: [spec.md](spec.md)

---

## サポート

問題が発生した場合：

1. [Issues](https://github.com/ryk2025/pdf-transformer/issues) を確認
2. 新しい Issue を作成
3. コミュニティフォーラムで質問

---

**所要時間**: セットアップから動作確認まで約 10 分

これで、Excel から PDF への変換 API が動作する環境が整いました！🎉
