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

## Getting Started

### Prerequisites
- Python 3.8 or higher
- `pip` (Python package installer)

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/Obsidian-discord.git
   cd Obsidian-discord
   ```
2. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Configuration
1. Create a `.env` file in the root directory of the project.
2. Add your Discord bot token to the `.env` file:
   ```
   DISCORD_TOKEN=YOUR_BOT_TOKEN_HERE
   ```
   Replace `YOUR_BOT_TOKEN_HERE` with your actual bot token.
3. Open `config.py` and set the `CHANNEL_ID` to the ID of the Discord channel where you want the bot to operate.

### Running the Bot
To run the bot in the background and log its output to `bot.log`:
```bash
nohup .venv/bin/python3 -u main.py > bot.log 2>&1 &
```

### Checking Logs
To view the bot's logs, you can use:
```bash
tail -f bot.log
```
This command will display the log output in real-time.

### Stopping the Bot
To stop the bot, you first need to find its process ID (PID):
```bash
ps aux | grep main.py
```
Look for the line containing `main.py` and note the PID (the second column).
Then, kill the process:
```bash
kill <PID>
```
Replace `<PID>` with the actual process ID.
