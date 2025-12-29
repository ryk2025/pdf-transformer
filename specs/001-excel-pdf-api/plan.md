# Implementation Plan: Excel から PDF への変換 API サービス

**Branch**: `001-excel-pdf-api` | **Date**: 2025-12-29 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-excel-pdf-api/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Excel ファイル（.xlsx、.xls）を PDF 形式に変換する REST API サービスを構築します。このサービスは、ファイルアップロードを受け付け、表構造とコンテンツを保持した PDF を生成し、クライアントに返します。将来的な拡張（Word、画像の変換）を考慮し、モジュール化された設計を採用します。

## Technical Context

**Language/Version**: Python 3.11 以上  
**Primary Dependencies**: FastAPI（REST API フレームワーク）、uv（依存関係管理）  
**Storage**: 一時ファイルストレージ（変換処理用）、永続ストレージは不要  
**Testing**: pytest（統合テスト）  
**Target Platform**: ローカル開発環境（将来的にクラウドデプロイ可能）
**Project Type**: single（バックエンド API サービス）  
**Performance Goals**: 標準的な Excel ファイル（5MB未満、10シート未満）を30秒以内に変換  
**Constraints**: 
- ファイルサイズ制限: 10MB
- ステートレス操作
- 同時リクエスト処理能力（妥当な制限まで劣化なし）
- Python コードは可能な限り型ヒント（type hints, type annotations）を使用すること
**Scale/Scope**: 
- フェーズ1では Excel → PDF 変換のみ
- 将来的に他のフォーマットに拡張可能な設計

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Phase 0 チェック（研究前）

#### I. コード品質基準（Clean and Short Code）
✅ **PASS** - 単一機能（Excel → PDF 変換）に集中、シンプルな設計を採用

#### II. テスト標準（Sprint Development）
✅ **PASS** - 統合テストのみを実装予定（ユニットテストは任意）

#### III. 依存関係の選択（Popular Dependencies）
✅ **PASS** - 計画中の依存関係:
- FastAPI: 人気の高いモダンな Python Web フレームワーク
- uv: モダンな Python 依存関係マネージャー
- Excel 解析ライブラリ: Phase 0 で調査が必要（openpyxl、pandas など人気ライブラリから選択）
- PDF 生成ライブラリ: Phase 0 で調査が必要（ReportLab、pypdf など人気ライブラリから選択）

#### IV. モダンな実装（Modern Implementation）
✅ **PASS** - Python 3.11+、FastAPI、uv を使用し、最新のベストプラクティスに従う

#### V. セキュリティの確保（High Security）
✅ **PASS** - 計画に含む:
- ファイルサイズ検証
- ファイル形式検証
- 一時ファイルの安全なクリーンアップ
- 機密情報のログ出力を避ける
- 依存関係のセキュリティアップデート

---

### Phase 1 再チェック（設計後）

#### I. コード品質基準（Clean and Short Code）
✅ **PASS** - 設計確認:
- モジュール化された責任分離（validation、parsing、conversion、generation、storage）
- 各レイヤーが単一の責任を持つ
- 不要な複雑さを排除

#### II. テスト標準（Sprint Development）
✅ **PASS** - テスト戦略確認:
- 統合テストを `tests/integration/` に配置
- API エンドポイントのエンドツーエンドテスト
- ユニットテストは任意（必須ではない）

#### III. 依存関係の選択（Popular Dependencies）
✅ **PASS** - 最終的な依存関係（research.md より）:
- FastAPI: 週次 1,500万ダウンロード、モダンで人気
- uvicorn: FastAPI の標準 ASGI サーバー
- openpyxl: 週次 2,500万ダウンロード、.xlsx サポート
- xlrd: 週次 1,500万ダウンロード、.xls サポート
- reportlab: 週次 150万ダウンロード、20年以上の実績
- python-magic: 週次 200万ダウンロード、セキュリティ検証
- python-multipart: FastAPI 標準依存関係

すべての依存関係が人気で活発にメンテナンスされている ✅

#### IV. モダンな実装（Modern Implementation）
✅ **PASS** - 最新技術の使用確認:
- Python 3.11+ の最新機能
- FastAPI の非同期サポート
- uv による高速な依存関係管理
- 型ヒントの活用（data-model.md）
- OpenAPI 3.0 仕様（contracts/api.yaml）

#### V. セキュリティの確保（High Security）
✅ **PASS** - セキュリティ実装確認（research.md より）:
- 多層防御アプローチ
  - 拡張子チェック
  - Content-Type チェック
  - Magic number チェック
- ファイルサイズ制限（10MB）
- 一時ファイルの安全な処理
  - ランダムな名前生成
  - パストラバーサル対策
  - 処理後の確実な削除
- マクロの無効化
- タイムアウト設定
- ログに機密情報を含めない
- OWASP ベストプラクティス準拠

すべてのセキュリティ要件を満たす ✅

---

**結論**: すべての憲章原則にパスしました。Phase 2（タスク分解）に進む準備が整いました。

## Project Structure

### Documentation (this feature)

```text
specs/001-excel-pdf-api/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── api.yaml        # OpenAPI 3.0 spec
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
pdf-transformer/
├── src/
│   ├── models/          # データモデル（リクエスト、レスポンス、エラー）
│   ├── services/        # ビジネスロジック（変換サービス、ファイル処理）
│   │   ├── converter/   # 変換ロジック（Excel → PDF）
│   │   └── storage/     # ファイルストレージ処理
│   ├── api/             # FastAPI エンドポイント
│   └── lib/             # 共通ユーティリティ
├── tests/
│   └── integration/     # 統合テスト
├── pyproject.toml       # uv 依存関係定義
├── uv.lock             # uv ロックファイル
└── README.md           # プロジェクトドキュメント
```

**Structure Decision**: シンプルな単一プロジェクト構造（Option 1）を選択しました。理由:
- バックエンド API のみで、フロントエンドやモバイルアプリは含まれない
- モジュール化された設計により、将来の拡張（Word、画像変換）を容易にする
- services/ ディレクトリを converter/ と storage/ に分割し、責任を明確化

## 型ヒント（Type Hints）に関する方針

Python コードは、関数・メソッドの引数・戻り値、クラス属性、変数など、可能な限り型ヒント（type hints, type annotations）を明示的に付与すること。

- 例: def func(a: int, b: str) -> bool:
- Pydantic モデルや FastAPI のエンドポイント定義も型ヒントを活用する
- 型安全性・可読性・保守性向上のため、mypy などの型チェッカーによる検証も推奨

この方針は設計・実装・レビューの全工程で徹底すること。

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

該当なし - すべての Constitution Check にパスしています。
