import asyncio
import datetime
import os
from discord.ext import commands, tasks
from discord import app_commands
import discord

import config
from ai_summarizer import summarize_and_tag
from logger_config import logger

class SummaryCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.daily_summary.start()

    def cog_unload(self):
        self.daily_summary.cancel()

    async def _run_summary(self, date_to_summarize: datetime.date):
        """指定された日付のメモを要約する共通ロジック"""
        file_path = os.path.join(config.SAVE_DIR, f"{date_to_summarize.strftime('%Y-%m-%d')}.md")

        if not os.path.exists(file_path):
            logger.warning(f"Memo file for {date_to_summarize.strftime('%Y-%m-%d')} not found.")
            return "対象のメモファイルが見つかりませんでした。"

        try:
            with open(file_path, 'r+', encoding='utf-8') as f:
                content = f.read()

                if '## まとめ' in content:
                    logger.info(f"Summary already exists for {file_path}")
                    return "既にまとめが存在します。"

                memo_section = content.split('## メモ')
                if len(memo_section) < 2:
                    logger.warning(f"'## メモ' section not found in {file_path}")
                    return "メモセクションが見つかりませんでした。"

                memo_content = memo_section[1]
                if not memo_content.strip():
                    logger.info(f"Memo content is empty for {file_path}")
                    return "メモの内容が空です。"

                summary, tags = summarize_and_tag(memo_content)

                # ファイルの末尾に追記するために、ポインタを末尾に移動
                f.seek(0, os.SEEK_END)
                # ファイルの末尾が改行でない場合は、改行を追加
                if f.tell() > 0:
                    f.seek(f.tell() - 1, os.SEEK_SET)
                    if f.read(1) != '\n':
                        f.write('\n')

                f.write('\n## まとめ\n')
                f.write(summary + '\n')
                f.write(tags + '\n')
                logger.info(f"Added summary to {file_path}")
                return f"{date_to_summarize.strftime('%Y-%m-%d')}のメモにまとめを追記しました。"

        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            return f"処理中にエラーが発生しました: {e}"

    @tasks.loop(hours=24)
    async def daily_summary(self):
        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        await self._run_summary(yesterday)

    @daily_summary.before_loop
    async def before_daily_summary(self):
        now = datetime.datetime.now()
        next_run = now.replace(hour=0, minute=5, second=0, microsecond=0)
        if next_run < now:
            next_run += datetime.timedelta(days=1)
        await asyncio.sleep((next_run - now).total_seconds())

    @app_commands.command(name="today_summary", description="本日のメモファイルに対してサマリー作成を実行します。")
    @commands.is_owner()
    async def today_summary(self, interaction: discord.Interaction):
        """本日のメモファイルに対してサマリー作成を実行します。"""
        await interaction.response.send_message("本日のメモの要約を作成します...", ephemeral=True)
        today = datetime.date.today()
        result = await self._run_summary(today)
        await interaction.followup.send(result, ephemeral=True)

async def setup(bot):
    await bot.add_cog(SummaryCog(bot))
    logger.info("Loaded cog: summary_cog")
