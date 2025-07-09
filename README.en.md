# Obsidian-Discord Integration Bot

## Overview

This is a high-performance bot designed to seamlessly connect your daily Discord interactions with your knowledge management workflow in Obsidian. It not only automatically records and formats conversations from a specified channel but also leverages AI to summarize and tag your daily notes. By automatically generating related topic notes, it provides powerful support for organizing and rediscovering information.

## Key Features

### 1. Note-Taking Features

- **Automatic Memoization**: Automatically appends all messages from a channel specified in `config.py` to a daily note in real-time.
- **Rich Information Enrichment**:
    - **URL Summaries**: Automatically fetches the title and description of any shared URL and includes it in the note.
    - **Image Handling**: Attached images are automatically saved and embedded into the note using Obsidian's `![[...]]` link format.
    - **AI-Powered Insights**: Utilizes the Gemini API to add relevant trivia or supplementary information as an "AI's Small Tip" to each entry.
- **Manual Addition**: You can manually add any message from any channel to the day's note by right-clicking it and selecting "Apps" > "Add to Memo".

### 2. Organization & Summarization Features

- **Automatic Daily Summary**: Every night (at 00:05 by default), the bot automatically processes the previous day's note with the following actions:
    1.  **Generate Summary**: Creates a concise summary of the day's conversations and appends it under a "## Summary" heading.
    2.  **Extract Tags & Auto-Generate Notes**: Identifies relevant keywords as tags and automatically creates a new, detailed explanation page for each tag in the `notes` directory.
    3.  **Automatic Linking**: Adds backlinks to these newly created tag notes in the daily note, automating the process of linking related information.

- **Manual Summary Execution**: The bot owner can manually trigger the above summary and organization process for the current day's note by using the `/today_summary` command.

## Setup Instructions

1.  **Clone the Repository**: `git clone <repository_url>`
2.  **Create and Activate Virtual Environment**: `python -m venv .venv && source .venv/bin/activate`
3.  **Install Libraries**: `pip install -r requirements.txt`
4.  **Edit Configuration File (`config.py`)**:
    Open the `config.py` file and edit the following variables to match your environment:
    *   `CHANNEL_ID`: The ID of the Discord channel you want to monitor for automatic note-taking.
    *   `SAVE_DIR`: The **absolute path** to the directory where memo files (.md) will be saved.
    *   `IMAGE_SAVE_DIR`: The **absolute path** to the directory where attached images will be saved.
    *   `NOTES_DIR`: The **absolute path** to the directory where tag-based explanation notes will be stored.

5.  **Create `.env` File**:
    Create a new file named `.env` in the project's root directory and add the following:
    ```env
    DISCORD_TOKEN="YOUR_DISCORD_BOT_TOKEN"
    GEMINI_API_KEY="YOUR_GOOGLE_API_KEY"
    ```
    *   `DISCORD_TOKEN`: Your Discord bot's token.
    *   `GEMINI_API_KEY`: Your API key from Google AI Studio.

6.  **Run the Bot**: `python main.py`

## Usage

- **To Take Notes**: Simply post in the channel configured in `config.py`, or right-click any message and use the "Add to Memo" context menu command.
- **To Organize the Day's Notes**: Either wait for the automatic nightly process or have the bot owner run the `/today_summary` command.
