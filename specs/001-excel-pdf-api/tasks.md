# タスク: Excel から PDF への変換 API サービス

**入力**: 設計ドキュメント `/specs/001-excel-pdf-api/`
**前提条件**: plan.md（必須）、spec.md（ユーザーストーリー用・必須）、research.md、data-model.md、contracts/

**テスト**: この仕様では統合テストのみを実装します（仕様書で明示的に要求されているため）。ユニットテストは任意です。

**構成**: タスクは各ユーザーストーリーごとにグループ化され、それぞれのストーリーを独立して実装・テスト可能にしています。

## 形式: `[ID] [P?] [Story] 説明`

- **[P]**: 並列実行可能（異なるファイル、依存関係なし）
- **[Story]**: このタスクが属するユーザーストーリー（例: US1, US2, US3）
- 説明に正確なファイルパスを含める

## パス規約

プロジェクト構成（plan.md より）:
- 単一プロジェクト: リポジトリルートの `src/`, `tests/`
- `src/models/` - データモデル
- `src/services/converter/` - 変換ロジック
- `src/services/storage/` - ファイルストレージ
- `src/api/` - FastAPI エンドポイント
- `src/lib/` - 共通ユーティリティ
- `tests/integration/` - 統合テスト

---

## Phase 1: セットアップ（共有インフラ）

**目的**: プロジェクト初期化と基本構造

- [ ] T001 plan.md に従ってプロジェクト構造を作成（src/, tests/, pyproject.toml, README.md, .gitignore）
- [ ] T002 Python プロジェクトを依存関係とともに初期化（FastAPI, openpyxl, xlrd, reportlab, python-magic, python-multipart, uvicorn, pytest）
- [ ] T003 [P] mypy 設定と型ヒント方針を pyproject.toml と README.md に追加

---

## Phase 2: 基盤（ブロッキング前提条件）

**目的**: すべてのユーザーストーリーが実装される前に完了しなければならないコアインフラ

**⚠️ 重要**: このフェーズが完了するまで、ユーザーストーリーの作業を開始できません

- [ ] T004 データモデルの基底クラスと共通型を src/models/__init__.py に作成（型ヒント付き）
- [ ] T005 [P] src/services/converter/ と src/services/storage/ ディレクトリ構造を作成
- [ ] T006 [P] src/api/ にルーターとミドルウェア構造をセットアップ
- [ ] T007 [P] src/lib/ にファイル検証ユーティリティの基盤を作成
- [ ] T008 環境設定管理を src/config.py に設定（ファイルサイズ制限、許可された拡張子）
- [ ] T009 エラーハンドリングとロギングインフラを src/lib/errors.py と src/lib/logging.py に設定

**チェックポイント**: 基盤準備完了 - ユーザーストーリーの実装を並列で開始可能

---

## Phase 3: ユーザーストーリー 1 - 基本的な Excel から PDF への変換 (優先度: P1) 🎯 MVP

**目標**: Excel ファイル（.xlsx、.xls）を PDF 形式に変換し、表構造とコンテンツを保持する

**独立したテスト**: シンプルな Excel ファイル（tests/fixtures/simple.xlsx）をアップロードし、コンテンツが保持された PDF が返されることを確認

### ユーザーストーリー 1 のテスト

> **注意: これらのテストを最初に作成し、実装前に失敗することを確認してください**

- [ ] T010 [P] [US1] /convert エンドポイントの統合テスト（正常系）を tests/integration/test_convert_success.py に作成
- [ ] T011 [P] [US1] 複数シートファイルの統合テストを tests/integration/test_multisheet.py に作成

### ユーザーストーリー 1 の実装

- [ ] T012 [P] [US1] ConversionRequest と ConversionResponse モデルを src/models/conversion.py に作成（Pydantic、型ヒント付き）
- [ ] T013 [P] [US1] ExcelWorkbook、ExcelSheet、ExcelCell モデルを src/models/excel.py に作成（型ヒント付き）
- [ ] T014 [P] [US1] PDFDocument と PDFPage モデルを src/models/pdf.py に作成（型ヒント付き）
- [ ] T015 [US1] Excel ファイル検証ロジック（拡張子、MIME、magic number、サイズ）を src/lib/validation.py に実装（T012 に依存）
- [ ] T016 [US1] 一時ファイル処理（安全な作成、クリーンアップ）を src/services/storage/temp_storage.py に実装（型ヒント付き）
- [ ] T017 [US1] Excel 解析サービス（openpyxl for .xlsx, xlrd for .xls）を src/services/converter/excel_parser.py に実装（T013 に依存、型ヒント付き）
- [ ] T018 [US1] PDF 生成サービス（ReportLab、Table、Platypus）を src/services/converter/pdf_generator.py に実装（T014 に依存、型ヒント付き）
- [ ] T019 [US1] 変換サービスオーケストレーター（検証→解析→生成）を src/services/converter/conversion_service.py に実装（T015-T018 に依存、型ヒント付き）
- [ ] T020 [US1] /convert POST エンドポイントを src/api/routes/convert.py に実装（T019 に依存、型ヒント付き）
- [ ] T021 [US1] FastAPI アプリケーションエントリポイントを src/main.py に実装（すべてのルートを含む、型ヒント付き）
- [ ] T022 [US1] 複数シートサポート（各シートを PDF ページとして）を src/services/converter/excel_parser.py と pdf_generator.py に追加
- [ ] T023 [US1] 基本的な書式設定保持（罫線、配置、フォント）を src/services/converter/pdf_generator.py に実装
- [ ] T024 [US1] ユーザーストーリー 1 のすべてのコードに mypy 型チェックを実行し、型エラーを修正

**チェックポイント**: この時点で、ユーザーストーリー 1 は完全に機能し、独立してテスト可能であるべきです

---

## Phase 4: ユーザーストーリー 2 - エラー処理とステータスフィードバック (優先度: P2)

**目標**: 無効なファイル、破損ファイル、変換失敗時に明確なエラーメッセージを提供

**独立したテスト**: 無効な入力（.txt ファイル、破損 Excel、サイズ超過ファイル）を送信し、適切なエラーレスポンスが返されることを確認

### ユーザーストーリー 2 のテスト

- [ ] T025 [P] [US2] 無効なファイル形式のエラー処理テストを tests/integration/test_error_invalid_format.py に作成
- [ ] T026 [P] [US2] ファイルサイズ超過のエラー処理テストを tests/integration/test_error_file_too_large.py に作成
- [ ] T027 [P] [US2] 破損ファイルのエラー処理テストを tests/integration/test_error_corrupted_file.py に作成

### ユーザーストーリー 2 の実装

- [ ] T028 [P] [US2] ErrorResponse モデルと ErrorType 列挙型を src/models/errors.py に作成（Pydantic、型ヒント付き）
- [ ] T029 [US2] カスタム例外クラス（InvalidFileFormat、FileTooLarge、CorruptedFile、ConversionFailed）を src/lib/exceptions.py に実装（型ヒント付き）
- [ ] T030 [US2] グローバル例外ハンドラーを src/api/middleware/error_handler.py に実装（T028-T029 に依存、型ヒント付き）
- [ ] T031 [US2] ファイル検証でのエラー処理を src/lib/validation.py に追加（適切な例外を発生させる）
- [ ] T032 [US2] Excel 解析でのエラー処理を src/services/converter/excel_parser.py に追加（破損ファイルを検出）
- [ ] T033 [US2] PDF 生成でのエラー処理を src/services/converter/pdf_generator.py に追加（変換失敗を処理）
- [ ] T034 [US2] エラーハンドラーを src/main.py の FastAPI アプリに登録
- [ ] T035 [US2] ユーザーストーリー 2 のすべてのコードに mypy 型チェックを実行

**チェックポイント**: この時点で、ユーザーストーリー 1 と 2 の両方が独立して機能するべきです

---

## Phase 5: ユーザーストーリー 3 - API 統合の準備 (優先度: P3)

**目標**: 一貫した API レスポンス、適切な HTTP ステータスコード、完全なドキュメントを保証

**独立したテスト**: API エンドポイントを呼び出し、レスポンス形式、ステータスコード、ヘッダーが REST 標準に準拠していることを確認

### ユーザーストーリー 3 のテスト

- [ ] T036 [P] [US3] API レスポンス形式と HTTP ステータスコードのテストを tests/integration/test_api_consistency.py に作成
- [ ] T037 [P] [US3] 並列リクエストとステートレス性のテストを tests/integration/test_concurrent_requests.py に作成

### ユーザーストーリー 3 の実装

- [ ] T038 [P] [US3] OpenAPI スキーマ（contracts/api.yaml）と FastAPI 自動ドキュメントの整合性を確認
- [ ] T039 [US3] すべてのエンドポイントに適切な HTTP ヘッダー（Content-Type、Content-Disposition、Content-Length）を src/api/routes/convert.py に追加
- [ ] T040 [US3] ヘルスチェックエンドポイント（/health）を src/api/routes/health.py に実装（型ヒント付き）
- [ ] T041 [US3] API レスポンス形式の一貫性を src/api/ 全体で保証（すべてのエンドポイントで統一されたフォーマット）
- [ ] T042 [US3] ステートレス性を検証（リクエスト間で状態が漏れないことを確認）
- [ ] T043 [US3] API 利用例を README.md に追加（curl コマンド、レスポンス例）
- [ ] T044 [US3] ユーザーストーリー 3 のすべてのコードに mypy 型チェックを実行

**チェックポイント**: すべてのユーザーストーリーが独立して機能するようになりました

---

## Phase 6: 仕上げと横断的な関心事

**目的**: 複数のユーザーストーリーに影響する改善

- [ ] T045 [P] ドキュメント更新（README.md にセットアップ手順、使用例、型ヒント方針を記載）
- [ ] T046 コードクリーンアップとリファクタリング（すべてのストーリー全体で）
- [ ] T047 [P] パフォーマンス最適化（大きなファイル処理、メモリ使用量）
- [ ] T048 セキュリティ強化（OWASP ベストプラクティス準拠）
  - 一時ファイルの安全な削除（確実なクリーンアップ、パストラバーサル対策）
  - ログサニタイズ（機密情報の除外、ファイル名のみ記録）
  - タイムアウト設定（30秒制限で DoS 攻撃防止）
  - ファイルパーミッション（一時ファイルを 0o600 に設定）
  - 入力検証の多層防御（拡張子、MIME、magic number、サイズ）
- [ ] T049 [P] エッジケーステスト（空ファイル、100列以上の表、特殊文字・絵文字、パスワード保護ファイル）を tests/integration/test_edge_cases.py に作成
- [ ] T050 [P] 将来拡張性のレビュー（モジュール設計が Word/画像変換に対応可能か確認、必要に応じてリファクタリング）
- [ ] T051 すべてのコードに対して最終 mypy 型チェックを実行（strictモード）
- [ ] T052 quickstart.md の検証（すべての手順を実際に実行）

---

## 依存関係と実行順序

### フェーズの依存関係

- **セットアップ（Phase 1）**: 依存関係なし - すぐに開始可能
- **基盤（Phase 2）**: セットアップの完了に依存 - すべてのユーザーストーリーをブロック
- **ユーザーストーリー（Phase 3+）**: すべて基盤フェーズの完了に依存
  - ユーザーストーリーは並列で進行可能（スタッフがいる場合）
  - または優先順位順に順次実行（P1 → P2 → P3）
- **仕上げ（最終フェーズ）**: すべての必要なユーザーストーリーの完了に依存

### ユーザーストーリーの依存関係

- **ユーザーストーリー 1（P1）**: 基盤（Phase 2）の後に開始可能 - 他のストーリーへの依存なし
- **ユーザーストーリー 2（P2）**: 基盤（Phase 2）の後に開始可能 - US1 と統合するが独立してテスト可能
- **ユーザーストーリー 3（P3）**: 基盤（Phase 2）の後に開始可能 - US1/US2 と統合するが独立してテスト可能

### 各ユーザーストーリー内

- テスト（含まれる場合）は実装前に作成し、失敗することを確認する必要があります
- サービスの前にモデル
- エンドポイントの前にサービス
- 統合の前にコア実装
- 次の優先度に移る前にストーリーを完了

### 並列実行の機会

- [P] マークのあるすべてのセットアップタスクを並列実行可能
- Phase 2 内の [P] マークのあるすべての基盤タスクを並列実行可能
- 基盤フェーズ完了後、すべてのユーザーストーリーを並列で開始可能（チーム容量が許せば）
- ユーザーストーリー内の [P] マークのあるすべてのテストを並列実行可能
- ストーリー内の [P] マークのあるモデルを並列実行可能
- 異なるチームメンバーが異なるユーザーストーリーを並列作業可能

---

## 並列実行例: ユーザーストーリー 1

```bash
# ユーザーストーリー 1 のすべてのテストを一緒に起動:
タスク: "tests/integration/test_convert_success.py に /convert エンドポイントの統合テスト（正常系）を作成"
タスク: "tests/integration/test_multisheet.py に複数シートファイルの統合テストを作成"

# ユーザーストーリー 1 のすべてのモデルを一緒に起動:
タスク: "src/models/conversion.py に ConversionRequest と ConversionResponse モデルを作成"
タスク: "src/models/excel.py に ExcelWorkbook、ExcelSheet、ExcelCell モデルを作成"
タスク: "src/models/pdf.py に PDFDocument と PDFPage モデルを作成"
```

---

## 実装戦略

### MVP 優先（ユーザーストーリー 1 のみ）

1. Phase 1: セットアップを完了
2. Phase 2: 基盤を完了（重要 - すべてのストーリーをブロック）
3. Phase 3: ユーザーストーリー 1 を完了
4. **停止して検証**: ユーザーストーリー 1 を独立してテスト
5. 準備ができたらデプロイ/デモ

### 段階的デリバリー

1. セットアップ + 基盤を完了 → 基盤準備完了
2. ユーザーストーリー 1 を追加 → 独立してテスト → デプロイ/デモ（MVP！）
3. ユーザーストーリー 2 を追加 → 独立してテスト → デプロイ/デモ
4. ユーザーストーリー 3 を追加 → 独立してテスト → デプロイ/デモ
5. 各ストーリーが以前のストーリーを壊すことなく価値を追加

### 並列チーム戦略

複数の開発者がいる場合:

1. チームでセットアップ + 基盤を一緒に完了
2. 基盤が完了したら:
   - 開発者 A: ユーザーストーリー 1
   - 開発者 B: ユーザーストーリー 2
   - 開発者 C: ユーザーストーリー 3
3. ストーリーが独立して完了・統合

---

## 注意事項

- [P] タスク = 異なるファイル、依存関係なし
- [Story] ラベルはタスクを特定のユーザーストーリーにマッピングしてトレーサビリティを確保
- 各ユーザーストーリーは独立して完了・テスト可能であるべき
- 実装前にテストが失敗することを確認
- 各タスクまたは論理グループの後にコミット
- 任意のチェックポイントで停止してストーリーを独立して検証
- 避けるべき: 曖昧なタスク、同じファイルの競合、独立性を壊すストーリー間の依存関係
- すべてのコードは型ヒント（type hints）を使用し、mypy で検証すること
