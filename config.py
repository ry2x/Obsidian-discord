import os
from dotenv import load_dotenv

load_dotenv()

CHANNEL_ID = 944090089376583711
SAVE_DIR = "/home/ry2x/Develop/Obsidian-discord/memos"
IMAGE_SAVE_DIR = "/home/ry2x/Develop/Obsidian-discord/images"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
