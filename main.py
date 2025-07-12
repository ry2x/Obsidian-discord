import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import config
from logger_config import logger
import asyncio


async def main():
    # .envファイルから環境変数を読み込む
    load_dotenv()

    # Botのインテントを設定
    intents = discord.Intents.default()
    intents.message_content = True

    # Botのインスタンスを作成
    bot = commands.Bot(command_prefix="!", intents=intents)

    @bot.event
    async def on_ready():
        """Botがログインしたときに実行される"""
        # cogsディレクトリからCogを読み込む
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py") and not filename.startswith("__"):
                try:
                    await bot.load_extension(f"cogs.{filename[:-3]}")
                    logger.info(f"Loaded cog: {filename[:-3]}")
                except Exception as e:
                    logger.error(f"Failed to load cog {filename[:-3]}: {e}")

        # 保存ディレクトリが存在しない場合は作成
        if not os.path.exists(config.SAVE_DIR):
            os.makedirs(config.SAVE_DIR)
            logger.info(f"Created directory: {config.SAVE_DIR}")

        # スラッシュコマンドを同期
        try:
            synced = await bot.tree.sync()
            logger.info(f"Synced {len(synced)} command(s)")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")

        logger.info(f"We have logged in as {bot.user}")

    # Botを起動
    await bot.start(os.getenv("DISCORD_TOKEN"))


if __name__ == "__main__":
    asyncio.run(main())
