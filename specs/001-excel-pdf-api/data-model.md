# Data Model: Excel から PDF への変換 API

**作成日**: 2025-12-29  
**機能**: [spec.md](spec.md)  
**計画**: [plan.md](plan.md)

## 概要

Excel から PDF への変換 API のデータモデルを定義します。このモデルは、API リクエスト、レスポンス、内部データ構造、およびエラー処理を網羅します。

---

## 1. API リクエストモデル

### ConversionRequest（変換リクエスト）

ファイルアップロードによる変換リクエスト。

**属性**:
- `file`: UploadFile - アップロードされた Excel ファイル（.xlsx または .xls）
- `filename`: string - オリジナルのファイル名
- `content_type`: string - ファイルの MIME タイプ
- `size`: integer - ファイルサイズ（バイト）

**制約**:
- `size` <= 10MB (10,485,760 バイト)
- `content_type` ∈ {`application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`, `application/vnd.ms-excel`}
- ファイル拡張子 ∈ {`.xlsx`, `.xls`}

**検証ルール**:
1. ファイル拡張子が許可されたリストに含まれる
2. Content-Type が許可されたリストに含まれる
3. Magic number（ファイルシグネチャ）が Excel 形式と一致する
4. ファイルサイズが制限以下

---

## 2. API レスポンスモデル

### ConversionResponse（成功レスポンス）

変換が成功した場合の PDF ファイル返却。

**形式**: `application/pdf`（バイナリストリーム）

**HTTP ヘッダー**:
- `Content-Type`: application/pdf
- `Content-Disposition`: attachment; filename="[original_name].pdf"
- `Content-Length`: [PDF サイズ（バイト）]

**ステータスコード**: 200 OK

---

### ErrorResponse（エラーレスポンス）

変換が失敗した場合のエラー情報。

**属性**:
- `error_type`: string - エラーの種類（列挙型）
- `message`: string - ユーザー向けエラーメッセージ
- `detail`: string (optional) - 詳細情報（デバッグ用、本番では省略可）
- `status_code`: integer - HTTP ステータスコード

**error_type の値**:
- `INVALID_FILE_FORMAT`: サポートされていないファイル形式
- `FILE_TOO_LARGE`: ファイルサイズ超過
- `CORRUPTED_FILE`: ファイルが破損している、または読み取り不可
- `CONVERSION_FAILED`: 変換処理中のエラー
- `INTERNAL_ERROR`: サーバー内部エラー

**JSON 形式**:
```json
{
  "error_type": "INVALID_FILE_FORMAT",
  "message": "サポートされていないファイル形式です。.xlsx または .xls ファイルをアップロードしてください。",
  "status_code": 400
}
```

**HTTP ステータスコードマッピング**:
- `400 Bad Request`: INVALID_FILE_FORMAT, CORRUPTED_FILE
- `413 Payload Too Large`: FILE_TOO_LARGE
- `422 Unprocessable Entity`: CONVERSION_FAILED
- `500 Internal Server Error`: INTERNAL_ERROR

---

## 3. 内部データモデル

### ExcelWorkbook（Excel ワークブック）

解析された Excel ファイルの内部表現。

**属性**:
- `sheets`: List[ExcelSheet] - ワークブック内のすべてのシート
- `filename`: string - 元のファイル名
- `format`: string - ファイル形式（"xlsx" または "xls"）

**関係性**: 1 Workbook → N Sheets

---

### ExcelSheet（Excel シート）

単一のワークシート。

**属性**:
- `name`: string - シート名
- `rows`: List[ExcelRow] - シート内のすべての行
- `max_column`: integer - 最大列数
- `max_row`: integer - 最大行数

**関係性**: 1 Sheet → N Rows

---

### ExcelRow（Excel 行）

単一の行。

**属性**:
- `row_index`: integer - 行番号（1-based）
- `cells`: List[ExcelCell] - 行内のすべてのセル

**関係性**: 1 Row → N Cells

---

### ExcelCell（Excel セル）

単一のセル。

**属性**:
- `value`: Any - セルの値（文字列、数値、日付、None）
- `row`: integer - 行番号（1-based）
- `column`: integer - 列番号（1-based）
- `format`: CellFormat - セルの書式設定

**データ型**:
- `string`: テキスト
- `number`: 数値（整数または浮動小数点）
- `datetime`: 日付・時刻
- `boolean`: 真偽値
- `null`: 空セル

---

### CellFormat（セル書式）

セルの視覚的な書式設定。

**属性**:
- `font`: FontStyle - フォント設定
- `alignment`: Alignment - 配置
- `border`: Border - 罫線
- `fill`: Fill - 背景色

---

### FontStyle（フォントスタイル）

**属性**:
- `name`: string - フォント名（例: "Arial", "MS ゴシック"）
- `size`: float - フォントサイズ（ポイント）
- `bold`: boolean - 太字
- `italic`: boolean - 斜体
- `color`: string - 色（16進数: "#RRGGBB"）

---

### Alignment（配置）

**属性**:
- `horizontal`: string - 水平配置（"left", "center", "right"）
- `vertical`: string - 垂直配置（"top", "middle", "bottom"）

---

### Border（罫線）

**属性**:
- `left`: BorderSide - 左罫線
- `right`: BorderSide - 右罫線
- `top`: BorderSide - 上罫線
- `bottom`: BorderSide - 下罫線

---

### BorderSide（罫線の辺）

**属性**:
- `style`: string - 線のスタイル（"thin", "medium", "thick", "none"）
- `color`: string - 色（16進数: "#RRGGBB"）

---

### Fill（塗りつぶし）

**属性**:
- `type`: string - 塗りつぶしタイプ（"solid", "pattern", "none"）
- `color`: string - 色（16進数: "#RRGGBB"）

---

## 4. PDF 生成モデル

### PDFDocument（PDF ドキュメント）

生成される PDF の内部表現。

**属性**:
- `pages`: List[PDFPage] - PDF 内のすべてのページ
- `metadata`: PDFMetadata - PDF メタデータ

**関係性**: 1 Document → N Pages

---

### PDFPage（PDF ページ）

単一の PDF ページ。

**属性**:
- `page_number`: integer - ページ番号（1-based）
- `elements`: List[PDFElement] - ページ内のすべての要素
- `width`: float - ページ幅（ポイント）
- `height`: float - ページ高さ（ポイント）

**デフォルトサイズ**: A4 (595 x 842 ポイント)

---

### PDFElement（PDF 要素）

PDF ページ内の要素（基底クラス）。

**サブクラス**:
- `PDFTable`: 表
- `PDFText`: テキスト
- `PDFLine`: 線

---

### PDFTable（PDF 表）

**属性**:
- `rows`: List[PDFTableRow] - 表の行
- `x`: float - X 座標
- `y`: float - Y 座標
- `width`: float - 表の幅
- `height`: float - 表の高さ

---

### PDFTableRow（PDF 表の行）

**属性**:
- `cells`: List[PDFTableCell] - 行内のセル

---

### PDFTableCell（PDF 表のセル）

**属性**:
- `content`: string - セルの内容
- `width`: float - セル幅
- `height`: float - セル高さ
- `style`: PDFCellStyle - セルスタイル

---

### PDFCellStyle（PDF セルスタイル）

**属性**:
- `font_name`: string - フォント名
- `font_size`: float - フォントサイズ
- `text_color`: tuple - テキスト色 (R, G, B)
- `background_color`: tuple - 背景色 (R, G, B)
- `alignment`: string - 配置
- `borders`: dict - 罫線設定

---

### PDFMetadata（PDF メタデータ）

**属性**:
- `title`: string - PDF タイトル（元の Excel ファイル名）
- `author`: string - 作成者（"PDF Transformer"）
- `creator`: string - 作成アプリケーション（"PDF Transformer v0.1.0"）
- `creation_date`: datetime - 作成日時

---

## 5. エンティティ関係図

```
ConversionRequest
    │
    ├──→ ExcelWorkbook
    │       │
    │       └──→ ExcelSheet (1:N)
    │               │
    │               └──→ ExcelRow (1:N)
    │                       │
    │                       └──→ ExcelCell (1:N)
    │                               │
    │                               └──→ CellFormat
    │                                       ├──→ FontStyle
    │                                       ├──→ Alignment
    │                                       ├──→ Border
    │                                       └──→ Fill
    │
    ├──→ PDFDocument
    │       │
    │       ├──→ PDFMetadata
    │       └──→ PDFPage (1:N)
    │               │
    │               └──→ PDFElement (1:N)
    │                       ├──→ PDFTable
    │                       │       └──→ PDFTableRow (1:N)
    │                       │               └──→ PDFTableCell (1:N)
    │                       │                       └──→ PDFCellStyle
    │                       ├──→ PDFText
    │                       └──→ PDFLine
    │
    └──→ ConversionResponse or ErrorResponse
```

---

## 6. 状態遷移

### 変換リクエストの状態

```
[アップロード] → [検証中] → [解析中] → [変換中] → [生成中] → [完了]
                    ↓           ↓          ↓          ↓
                 [エラー]    [エラー]   [エラー]   [エラー]
```

**状態の説明**:
1. **アップロード**: ファイルがサーバーに送信される
2. **検証中**: ファイル形式、サイズ、内容を検証
3. **解析中**: Excel ファイルを ExcelWorkbook モデルに解析
4. **変換中**: ExcelWorkbook を PDFDocument モデルに変換
5. **生成中**: PDFDocument から実際の PDF バイナリを生成
6. **完了**: PDF をクライアントに返却
7. **エラー**: いずれかの段階で失敗した場合の状態

**状態は一時的**: システムはステートレスなので、状態はリクエスト処理中のみ存在

---

## 7. データ検証ルール

### 入力検証

| フィールド | 検証ルール | エラータイプ |
|----------|----------|------------|
| ファイル拡張子 | `.xlsx` または `.xls` | INVALID_FILE_FORMAT |
| Content-Type | 許可された MIME タイプ | INVALID_FILE_FORMAT |
| Magic number | Excel ファイルシグネチャ | INVALID_FILE_FORMAT |
| ファイルサイズ | <= 10MB | FILE_TOO_LARGE |
| ファイル読み取り | 破損していない | CORRUPTED_FILE |

### 変換検証

| 検証項目 | 検証内容 | エラータイプ |
|---------|---------|------------|
| シート数 | > 0 | CORRUPTED_FILE |
| セルデータ | 読み取り可能 | CONVERSION_FAILED |
| PDF 生成 | エラーなし | CONVERSION_FAILED |

---

## まとめ

このデータモデルは、以下を保証します：

- **明確な境界**: 各レイヤー（API、解析、変換、生成）が明確に分離
- **型安全性**: すべてのデータ構造が明確に定義
- **エラー処理**: 包括的なエラータイプとメッセージ
- **拡張性**: 将来的な機能追加（Word、画像変換）に対応可能な設計
- **ステートレス**: 状態はリクエスト処理中のみ、永続化なし

このモデルは、仕様書の要件（FR-001 ～ FR-014）をすべて満たし、成功基準（SC-001 ～ SC-007）の達成を支援します。
