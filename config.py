import os
from dotenv import load_dotenv

load_dotenv()

CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
SAVE_DIR = os.getenv("SAVE_DIR")
IMAGE_SAVE_DIR = os.getenv("IMAGE_SAVE_DIR")
NOTES_DIR = os.getenv("NOTES_DIR")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
