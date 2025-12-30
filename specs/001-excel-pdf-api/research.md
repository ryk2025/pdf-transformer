# Phase 0 Research: Excel から PDF への変換 API

**作成日**: 2025-12-29  
**機能**: [spec.md](spec.md)  
**計画**: [plan.md](plan.md)

## 目的

Excel から PDF への変換サービスに最適な技術選択を調査し、実装の基盤を固める。

---

## 1. Excel ファイル解析ライブラリ

### 決定: openpyxl + xlrd の組み合わせ

**理由**:
- openpyxl は .xlsx（Excel 2007以降）の書式設定を完全にサポートし、罫線・配置・フォント・色などの詳細な読み取りが可能
- xlrd は .xls（旧形式）の読み取りに特化しており、安定性が高い
- openpyxl は読み取り専用モードで大きなファイルも効率的に処理可能
- 両ライブラリとも長期にわたってメンテナンスされており、信頼性が高い
- openpyxl: 週次 2,500万ダウンロード、GitHub 4,500スター
- xlrd: 週次 1,500万ダウンロード

**検討した代替案**:
- **pandas + openpyxl**: データ分析には最適だが、書式設定の読み取りが限定的。データのみの変換には有用だが、見た目の再現が必要な場合は不十分
- **pyexcel**: 統一的なインターフェースを提供するが、内部的には openpyxl などを使用するため、直接使用する方が制御性が高い
- **xlwings**: Excel アプリケーションが必要（Windows/Mac のみ）でサーバー環境に不適切

---

## 2. PDF 生成ライブラリ

### 決定: ReportLab

**理由**:
- 低レベル API により表構造・罫線・セル配置を細かく制御可能
- Platypus（高レベル API）で Table オブジェクトを使用し、Excel の表を忠実に再現できる
- パフォーマンスが優れており、大量のデータを含む PDF も高速生成
- 20年以上の実績があり、商用プロジェクトでも広く採用されている
- 豊富なドキュメントとコミュニティサポート
- 週次 150万ダウンロード、GitHub 4,000スター

**検討した代替案**:
- **WeasyPrint**: HTML/CSS からの PDF 生成に特化。Excel → HTML → PDF の変換パイプラインが必要で、書式の完全な再現が困難
- **pdfkit**: wkhtmltopdf のラッパー。外部バイナリ依存があり、デプロイが複雑化。また、wkhtmltopdf は非推奨化が進んでいる
- **pypdf/pypdf2**: PDF の操作・結合には優れるが、ゼロから表を作成する機能は限定的

---

## 3. ファイルアップロード処理

### 決定: UploadFile + 一時ファイル保存のハイブリッドアプローチ

**理由**:
- FastAPI の `UploadFile` は `SpooledTemporaryFile` を使用し、小さいファイルはメモリ、大きいファイルは自動的にディスクに保存される
- Excel ファイルの解析には実際のファイルパスが必要なライブラリが多い（openpyxl など）
- `tempfile.NamedTemporaryFile` を使用して安全な一時ファイル処理を実装
- 処理後は確実に削除する（try-finally または context manager 使用）

**実装アプローチ**:
```python
from fastapi import UploadFile
import tempfile
import os

async def process_excel(file: UploadFile):
    # 拡張子に応じて処理を分岐
    suffix = os.path.splitext(file.filename)[1]
    
    # 一時ファイルとして保存
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        # openpyxl で処理
        workbook = load_workbook(tmp_path, data_only=True)
        # ... PDF 生成処理
    finally:
        # 確実に削除
        os.unlink(tmp_path)
```

**サイズ制限の実装**:
```python
from fastapi import HTTPException

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

async def validate_file_size(file: UploadFile):
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large")
    await file.seek(0)  # ポインタをリセット
    return content
```

**検討した代替案**:
- **完全メモリ処理**: 小さいファイルには効率的だが、大きいファイルでメモリ不足のリスク。Excel ファイルは数十 MB になることもあり、リスクが高い
- **ストリーミング処理**: Excel のバイナリ形式では実用的でない。全体を読み込む必要がある

---

## 4. セキュリティベストプラクティス

### 決定: 多層防御アプローチ

**ファイル形式検証**:
```python
import magic
from fastapi import UploadFile, HTTPException

ALLOWED_MIME_TYPES = {
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
    'application/vnd.ms-excel',  # .xls
}

ALLOWED_EXTENSIONS = {'.xlsx', '.xls'}

async def validate_excel_file(file: UploadFile):
    # 1. 拡張子チェック
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid file extension")
    
    # 2. Content-Type チェック
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Invalid content type")
    
    # 3. Magic number チェック（推奨）
    content = await file.read()
    mime = magic.from_buffer(content, mime=True)
    if mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Invalid file format")
    
    await file.seek(0)
    return content
```

**ファイルサイズ制限**:
- アプリケーションレベル: 上記の `validate_file_size` 関数
- FastAPI レベル: `app.add_middleware()` でリクエストボディサイズを制限
- Nginx/リバースプロキシレベル: `client_max_body_size` 設定（将来のデプロイ時）

**一時ファイルの安全な処理**:
```python
import tempfile
import secrets

def create_safe_temp_file(suffix: str):
    # ランダムな名前を生成してパストラバーサル対策
    random_name = secrets.token_hex(16)
    temp_dir = tempfile.gettempdir()
    
    # 安全なパス結合
    safe_path = os.path.join(temp_dir, f"{random_name}{suffix}")
    
    # 親ディレクトリが temp_dir であることを確認
    if not os.path.commonpath([safe_path, temp_dir]) == temp_dir:
        raise ValueError("Invalid path")
    
    return safe_path
```

**追加のセキュリティ対策**:
- Excel マクロの無効化: openpyxl は `keep_vba=False`（デフォルト）でマクロを読み込まない
- タイムアウト設定: 処理時間に上限を設け、DoS 攻撃を防ぐ
- レート制限: API エンドポイントにレート制限を実装（slowapi など）
- ログ記録: ファイル処理の監査ログを記録（機密情報は除外）
- 一時ファイルの権限: `os.chmod(path, 0o600)` で所有者のみアクセス可能に

---

## 5. 推奨技術スタック

### コア依存関係

```toml
[project]
name = "pdf-transformer"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.104.1",
    "uvicorn[standard]>=0.24.0",
    "openpyxl>=3.1.2",
    "xlrd>=2.0.1",
    "reportlab>=4.0.7",
    "python-magic>=0.4.27",
    "python-multipart>=0.0.6",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "httpx>=0.25.0",  # FastAPI テストクライアント用
]
```

### 依存関係の正当化

| 依存関係 | 目的 | 憲章原則への準拠 |
|---------|------|--------------|
| FastAPI | REST API フレームワーク | ✅ モダンで人気（週次 1,500万DL）、優れたドキュメント |
| uvicorn | ASGI サーバー | ✅ FastAPI の標準サーバー、高パフォーマンス |
| openpyxl | .xlsx ファイル解析 | ✅ 人気（週次 2,500万DL）、活発なメンテナンス |
| xlrd | .xls ファイル解析 | ✅ 安定した旧形式サポート、広く使用 |
| reportlab | PDF 生成 | ✅ 20年以上の実績、商用プロジェクトで信頼性実証 |
| python-magic | ファイル形式検証 | ✅ セキュリティベストプラクティス、OWASP 推奨 |
| python-multipart | ファイルアップロード | ✅ FastAPI の標準依存関係 |

---

## 6. アーキテクチャパターン

### 変換パイプライン

```
Excel ファイル → 検証 → 解析 → 変換 → PDF 生成 → 返却
     ↓            ↓       ↓       ↓        ↓        ↓
  UploadFile   Validator  Parser  Converter Generator Response
```

### モジュール分離

1. **Validation Layer** (`src/services/validation/`)
   - ファイル形式検証
   - サイズ制限チェック
   - セキュリティチェック

2. **Parsing Layer** (`src/services/converter/parser/`)
   - Excel ファイル解析
   - 書式情報抽出
   - データ構造化

3. **Conversion Layer** (`src/services/converter/transformer/`)
   - Excel データから PDF レイアウトへの変換
   - 表構造マッピング
   - 書式適用

4. **Generation Layer** (`src/services/converter/generator/`)
   - ReportLab による PDF 生成
   - 複数シート処理
   - ページネーション

5. **Storage Layer** (`src/services/storage/`)
   - 一時ファイル管理
   - クリーンアップ処理
   - エラー時の安全な削除

---

## 7. パフォーマンス考慮事項

### 最適化戦略

1. **読み取り専用モード**: openpyxl の `read_only=True`, `data_only=True` を使用
2. **メモリ効率**: 大きなファイルは一時ファイルに保存してストリーム処理
3. **並行処理**: 複数リクエストの同時処理（FastAPI の非同期サポート）
4. **タイムアウト**: 長時間処理の中断（30秒制限）

### 性能目標（SC-001 より）

- 標準的な Excel ファイル（5MB未満、10シート未満）を30秒以内に変換
- メモリ使用量: ファイルサイズの3倍以下を目標
- 同時リクエスト: 10リクエストまで劣化なし（ローカル環境）

---

## まとめ

すべての技術選択は以下を満たします：

✅ **憲章原則 III（Popular Dependencies）**: すべての依存関係が人気で活発にメンテナンスされている  
✅ **憲章原則 IV（Modern Implementation）**: Python 3.11+、FastAPI などモダンなツールを使用  
✅ **憲章原則 V（High Security）**: 多層防御、OWASP ベストプラクティスに準拠

この技術スタックにより、安全で高性能、かつ保守しやすい Excel to PDF 変換サービスを構築できます。
