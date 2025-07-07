# Obsidian Discord Bot Project 

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
