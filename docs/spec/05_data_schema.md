# 入出力データ仕様

## ディレクトリ構造（実行時）

```
data/
├── uploads/
│   └── {job_id}/
│       └── {original_filename}                        # アップロードファイル（処理完了後に自動削除）
│
├── outputs/
│   └── {job_id}/
│       ├── {filename_stem}_transcript.txt             # 文字起こし（タイムスタンプ付き）
│       ├── slides/
│       │   ├── slide_001.png                          # 抽出スライド画像
│       │   ├── slide_002.png
│       │   └── ...
│       ├── {filename_stem}_slides_text.txt            # スライドOCRテキスト
│       ├── {filename_stem}_summary.md                 # 要約
│       ├── {filename_stem}_minutes.md                 # 議事録
│       └── metadata.json                              # ジョブメタデータ
│
└── temp/
    └── {job_id}/
        ├── audio.wav                                  # 抽出音声（処理後削除）
        └── frames/                                    # 一時フレーム（処理後削除）
```

> `{filename_stem}` はアップロードファイルのファイル名（拡張子なし）をサニタイズしたもの。  
> 日本語ファイル名はそのまま保持されます（例: `会議録_2024年4月` → `会議録_2024年4月_transcript.txt`）。  
> パスに使用できない文字（`<>:"/\|?*` 等）は `_` に置換されます。

---

## ファイルライフサイクル

| ファイル | 作成タイミング | 削除タイミング |
|----------|---------------|---------------|
| `uploads/{job_id}/` | アップロード時 | **処理正常終了後に自動削除** |
| `temp/{job_id}/` | 処理開始時 | 処理終了後（成功・失敗問わず）自動削除 |
| `outputs/{job_id}/` | 処理完了時 | ユーザーが明示的に削除するまで保持 |

> アップロードファイルは処理が正常完了（status: completed）した時点で即座に削除されます。
> エラー終了時はデバッグのため保持し、ユーザー操作で削除します。

---

## ファイル仕様

### {filename_stem}_transcript.txt
```
[HH:MM:SS --> HH:MM:SS] テキスト内容
[00:00:05 --> 00:00:12] こんにちは、本日の会議を始めます。
[00:00:13 --> 00:00:20] 最初のアジェンダは先週の振り返りです。
```

### {filename_stem}_slides_text.txt
```
--- slide_001.png ---
スライドタイトル
箇条書き1
箇条書き2

--- slide_002.png ---
次のスライドの内容
```

### {filename_stem}_summary.md
```markdown
# 要約

## 概要
（全体の要点）

## 主なトピック
- トピック1
- トピック2

## 重要なポイント
- ポイント1
```

### {filename_stem}_minutes.md
```markdown
# 議事録

## 基本情報
- タイトル:
- 日時:
- 概要:

## 主要トピック
1. トピック名
   - 内容

## 決定事項
- [ ] 決定内容

## TODO・アクションアイテム
- [ ] タスク内容（担当者）
```

### metadata.json
```json
{
  "job_id": "abc123",
  "filename": "meeting.mp4",
  "file_type": "video",
  "language": "ja",
  "enable_ocr": true,
  "enable_minutes": true,
  "status": "completed",
  "created_at": "2026-03-26T10:00:00",
  "completed_at": "2026-03-26T10:15:00",
  "duration_seconds": 3600,
  "steps_completed": ["transcribe", "extract", "summarize", "minutes"],
  "upload_deleted": true
}
```

> `enable_ocr` / `enable_minutes` が `false` の場合、対応するステップは `skipped` になり出力ファイルは生成されません。

---

## ジョブID
- 形式: UUID v4（例: `550e8400-e29b-41d4-a716-446655440000`）
- 生成タイミング: ファイルアップロード時
