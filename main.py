
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import config

# .envファイルから環境変数を読み込む
load_dotenv()

# Botのインテントを設定
intents = discord.Intents.default()
intents.message_content = True

# Botのインスタンスを作成
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    """Botがログインしたときに実行される"""
    # cogsディレクトリからCogを読み込む
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')
            print(f'Loaded cog: {filename[:-3]}')

    # 保存ディレクトリが存在しない場合は作成
    if not os.path.exists(config.SAVE_DIR):
        os.makedirs(config.SAVE_DIR)
        print(f"Created directory: {config.SAVE_DIR}")
        
    print(f'We have logged in as {bot.user}')

# Botを起動
bot.run(os.getenv('DISCORD_TOKEN'))
