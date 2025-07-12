import asyncio
import datetime
import os
from discord.ext import commands, tasks
from discord import app_commands
import discord

import config
from ai_summarizer import summarize_and_tag_and_explain
from logger_config import logger


class SummaryCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.daily_summary.start()

    def cog_unload(self):
        self.daily_summary.cancel()

    async def _run_summary(self, date_to_summarize: datetime.date):
        """指定された日付のメモを要約し、タグファイルを作成する共通ロジック"""
        file_path = os.path.join(
            config.SAVE_DIR, f"{date_to_summarize.strftime('%Y-%m-%d')}.md"
        )

        if not os.path.exists(file_path):
            logger.warning(
                f"Memo file for {date_to_summarize.strftime('%Y-%m-%d')} not found."
            )
            return "対象のメモファイルが見つかりませんでした。"

        try:
            with open(file_path, "r+", encoding="utf-8") as f:
                content = f.read()

                if "## まとめ" in content:
                    logger.info(f"Summary already exists for {file_path}")
                    return "既にまとめが存在します。"

                memo_section = content.split("## メモ")
                if len(memo_section) < 2:
                    logger.warning(f"'## メモ' section not found in {file_path}")
                    return "メモセクションが見つかりませんでした。"

                memo_content = memo_section[1]
                if not memo_content.strip():
                    logger.info(f"Memo content is empty for {file_path}")
                    return "メモの内容が空です。"

                date_str = date_to_summarize.strftime("%Y-%m-%d")
                summary, tags, explanations = summarize_and_tag_and_explain(
                    memo_content, date_str
                )

                # 1. 元のメモファイルにまとめとタグを追記
                f.seek(0, os.SEEK_END)
                if f.tell() > 0:
                    f.seek(f.tell() - 1, os.SEEK_SET)
                    if f.read(1) != "\n":
                        f.write("\n")
                f.write("\n## まとめ\n")
                f.write(summary + "\n")
                f.write(tags + "\n")
                logger.info(f"Added summary and tags to {file_path}")

                # 2. タグごとの解説ファイルを作成し、デイリーノートにバックリンクを追記
                if not os.path.exists(config.NOTES_DIR):
                    os.makedirs(config.NOTES_DIR)
                    logger.info(f"Created directory: {config.NOTES_DIR}")

                backlinks = []
                for tag, explanation in explanations.items():
                    tag_file_path = os.path.join(config.NOTES_DIR, f"{tag}.md")
                    with open(tag_file_path, "w", encoding="utf-8") as tag_f:
                        date_str = date_to_summarize.strftime("%Y-%m-%d")
                        file_content = (
                            f"# {tag}\n\n[[{date_str}]]\n\n{explanation}\n\n#{tag}"
                        )
                        tag_f.write(file_content)
                    logger.info(f"Created tag explanation file: {tag_file_path}")
                    backlinks.append(f"[[{tag}]]")

                # 3. デイリーノートにバックリンクを追記
                if backlinks:
                    f.write("\n## 詳細ノート\n")
                    f.write(" ".join(backlinks) + "\n")
                    logger.info(f"Added backlinks to {file_path}")

                return f"{date_to_summarize.strftime('%Y-%m-%d')}のメモの要約とタグ付けが完了しました。"

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

    @app_commands.command(
        name="today_summary",
        description="本日のメモファイルに対してサマリー作成を実行します。",
    )
    @commands.is_owner()
    async def today_summary(self, interaction: discord.Interaction):
        """本日のメモファイルに対してサマリー作成を実行します。"""
        await interaction.response.send_message(
            "本日のメモの要約とタグ解説の作成を開始します...", ephemeral=True
        )
        today = datetime.date.today()
        result = await self._run_summary(today)
        await interaction.followup.send(result, ephemeral=True)


async def setup(bot):
    await bot.add_cog(SummaryCog(bot))
    logger.info("Loaded cog: summary_cog")
