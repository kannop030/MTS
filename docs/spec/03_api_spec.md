# API仕様

## ベースURL
`http://localhost:8000`

---

## エンドポイント一覧

### POST /api/upload
ファイルをアップロードしてジョブを開始する。

**リクエスト**
```
Content-Type: multipart/form-data

file        : アップロードファイル（必須）
language    : 言語コード（任意, デフォルト: "ja"）
mode        : 処理モード（任意, デフォルト: "full"）
              "transcribe_only" | "extract_only" | "full"
```

**レスポンス**
```json
{
  "job_id": "abc123",
  "status": "queued",
  "filename": "meeting.mp4",
  "created_at": "2026-03-26T10:00:00"
}
```

---

### GET /api/status/{job_id}
処理状況を取得する。

**レスポンス**
```json
{
  "job_id": "abc123",
  "status": "processing",
  "progress": 45,
  "current_step": "transcribing",
  "steps": {
    "transcribing": "in_progress",
    "extracting":   "pending",
    "summarizing":  "pending"
  },
  "error": null
}
```

**ステータス値**
| 値 | 説明 |
|----|------|
| `queued` | 待機中 |
| `processing` | 処理中 |
| `completed` | 完了 |
| `failed` | エラー |

---

### GET /api/result/{job_id}
処理結果のファイル一覧を取得する。

**レスポンス**
```json
{
  "job_id": "abc123",
  "status": "completed",
  "files": {
    "transcript": "outputs/abc123/transcript.txt",
    "slides": ["outputs/abc123/slides/slide_001.png"],
    "slides_text": "outputs/abc123/slides_text.txt",
    "summary": "outputs/abc123/summary.md",
    "minutes": "outputs/abc123/minutes.md"
  }
}
```

---

### GET /api/download/{job_id}
処理結果をZIPでダウンロードする。

**レスポンス**
```
Content-Type: application/zip
Content-Disposition: attachment; filename="abc123_result.zip"
```

---

### DELETE /api/job/{job_id}
ジョブと関連ファイルを削除する。

**レスポンス**
```json
{
  "job_id": "abc123",
  "deleted": true
}
```

---

### GET /api/health
サーバーの稼働状況を確認する。

**レスポンス**
```json
{
  "status": "ok",
  "ollama": "connected",
  "whisper_model": "small"
}
```
