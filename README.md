# Obsidian Discord Bot Project Status

## Project Goal
特定のDiscordチャンネルに投稿された内容をキャッチし、Markdown形式のメモファイルとして保存するBot。将来的には拡張性、軽量性、信頼性を備えた多機能Botを目指す。

## Implemented Features
- **基本メモ機能:**
  - 特定のチャンネルに投稿されたメッセージを`yyyy-mm-dd.md`形式のファイルに保存。
  - ファイルが存在しない場合はテンプレート（日付、前後7日/1日リンク、`## メモ`セクション）で新規作成。
  - メッセージは`hh:mm - チャットの内容`形式で`## メモ`以下に追記。
- **URL概要取得機能:**
  - メッセージ内のURLを検出し、そのWebページのタイトルとdescriptionを抽出してメモに追記。
  - `aiohttp`と`BeautifulSoup4`を使用。
- **URLサムネイル保存機能:**
  - メッセージ内のURLからOpen Graph (og:image) サムネイルを抽出し、`config.IMAGE_SAVE_DIR`に保存。
  - メモファイルには`![[ファイル名]]`形式で画像へのリンクを追記。
  - `Content-Type`ヘッダーに基づいて適切な画像形式を判断し保存。
- **画像添付保存機能:**
  - メッセージに添付された画像を`config.IMAGE_SAVE_DIR`に保存。
  - メモファイルには`![[ファイル名]]`形式で画像へのリンクを追記。