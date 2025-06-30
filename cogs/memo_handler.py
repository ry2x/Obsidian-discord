import discord
from discord.ext import commands
import os
from datetime import datetime, timedelta
import config

def get_template(date_obj):
    """指定された日付のテンプレート文字列を生成する"""
    today_str = date_obj.strftime('%Y-%m-%d')
    prev_day_str = (date_obj - timedelta(days=1)).strftime('%Y-%m-%d')
    next_day_str = (date_obj + timedelta(days=1)).strftime('%Y-%m-%d')
    prev_week_str = (date_obj - timedelta(days=7)).strftime('%Y-%m-%d')
    next_week_str = (date_obj + timedelta(days=7)).strftime('%Y-%m-%d')

    return f"""{today_str}
[[{prev_week_str}]]||[[{prev_day_str}]]||[[{next_day_str}]]||[[{next_week_str}]]
---

## メモ
"""

class MemoHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        """メッセージが投稿されたときに実行される"""
        # 自分のメッセージは無視
        if message.author == self.bot.user:
            return

        # 特定のチャンネルのメッセージのみを処理
        if message.channel.id == config.CHANNEL_ID:
            today = datetime.now().date()
            file_name = f"{today.strftime('%Y-%m-%d')}.md"
            file_path = os.path.join(config.SAVE_DIR, file_name)

            # ファイルが存在しない場合はテンプレートで作成
            if not os.path.exists(file_path):
                template = get_template(today)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(template)

            # メッセージを追記
            timestamp = message.created_at.strftime('%H:%M')
            content_to_append = f"\n{timestamp} -\n {message.content}\n"
            
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(content_to_append)
            
            print(f"Appended message to {file_path}")

async def setup(bot):
    await bot.add_cog(MemoHandler(bot))
