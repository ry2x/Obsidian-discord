import discord
from discord.ext import commands
import os
import re
from datetime import datetime, timedelta
import config
import aiohttp
from bs4 import BeautifulSoup

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

async def get_url_summary(url):
    """URLからタイトルとdescriptionを取得する"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    title = soup.title.string if soup.title else 'タイトルなし'
                    description_tag = soup.find('meta', attrs={'name': 'description'})
                    description = description_tag['content'] if description_tag else '説明文なし'
                    return f"タイトル: {title.strip()}\n説明: {description.strip()}"
                else:
                    return "ページの取得に失敗しました。"
    except Exception as e:
        print(f"Error fetching or parsing URL: {e}")
        return "URLの処理中にエラーが発生しました。"

class MemoHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        """メッセージが投稿されたときに実行される"""
        if message.author == self.bot.user:
            return

        if message.channel.id == config.CHANNEL_ID:
            today = datetime.now().date()
            file_name = f"{today.strftime('%Y-%m-%d')}.md"
            file_path = os.path.join(config.SAVE_DIR, file_name)

            if not os.path.exists(file_path):
                template = get_template(today)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(template)

            timestamp = message.created_at.strftime('%H:%M')
            content_to_append = f"\n{timestamp} -\n {message.content}\n"

            # URLを検出して要約を追加
            url_match = re.search(r'https?://\S+', message.content)
            if url_match:
                url = url_match.group(0)
                summary = await get_url_summary(url)
                content_to_append += f"\n> URLの概要:\n> {summary.replace('\n', '\n> ')}\n"
            
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(content_to_append)
            
            print(f"Appended message to {file_path}")

async def setup(bot):
    await bot.add_cog(MemoHandler(bot))