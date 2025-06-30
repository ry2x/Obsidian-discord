import discord
from discord.ext import commands
import os
import re
from datetime import datetime, timedelta
import config
import aiohttp
from bs4 import BeautifulSoup
import hashlib
from urllib.parse import urlparse

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
    """URLからタイトル、description、og:imageを取得する"""
    print(f"[DEBUG] Attempting to fetch URL: {url}")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                print(f"[DEBUG] URL: {url}, Status: {response.status}")
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    title = soup.title.string if soup.title else 'タイトルなし'
                    description_tag = soup.find('meta', attrs={'name': 'description'})
                    description = description_tag['content'] if description_tag else '説明文なし'
                    
                    og_image_url = None
                    og_image_tag = soup.find('meta', property='og:image')
                    if og_image_tag and 'content' in og_image_tag.attrs:
                        og_image_url = og_image_tag['content']
                        print(f"[DEBUG] Extracted og:image: {og_image_url}")

                    print(f"[DEBUG] Extracted Title: {title.strip()}, Description: {description.strip()}")
                    return f"タイトル: {title.strip()}\n説明: {description.strip()}", og_image_url
                else:
                    return f"ページの取得に失敗しました。ステータスコード: {response.status}", None
    except aiohttp.ClientError as e:
        print(f"[ERROR] aiohttp ClientError fetching URL {url}: {e}")
        return "URLの取得中にネットワークエラーが発生しました。", None
    except Exception as e:
        print(f"[ERROR] Unexpected error fetching or parsing URL {url}: {e}")
        return "URLの処理中に予期せぬエラーが発生しました。", None

async def download_thumbnail(url, base_filename):
    """指定されたURLから画像をダウンロードし、適切な拡張子で保存する"""
    print(f"[DEBUG] Attempting to download thumbnail from: {url}")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    content_type = response.headers.get('Content-Type', '')
                    if 'image/' in content_type:
                        # Content-Typeから適切な拡張子を決定
                        if 'image/jpeg' in content_type:
                            ext = '.jpg'
                        elif 'image/png' in content_type:
                            ext = '.png'
                        elif 'image/gif' in content_type:
                            ext = '.gif'
                        elif 'image/webp' in content_type:
                            ext = '.webp'
                        else:
                            print(f"[DEBUG] Unsupported image content type: {content_type}")
                            return None

                        filename = f"{base_filename}{ext}"
                        save_path = os.path.join(config.IMAGE_SAVE_DIR, filename)
                        with open(save_path, 'wb') as f:
                            f.write(await response.read())
                        print(f"[DEBUG] Saved thumbnail: {save_path}")
                        return filename
                    else:
                        print(f"[DEBUG] URL content is not an image: {content_type}")
                        return None
                else:
                    print(f"[ERROR] Failed to download thumbnail from {url}. Status: {response.status}")
                    return None
    except aiohttp.ClientError as e:
        print(f"[ERROR] aiohttp ClientError downloading thumbnail {url}: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] Unexpected error downloading thumbnail {url}: {e}")
        return None

class MemoHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 保存ディレクトリが存在しない場合は作成
        for dir_path in [config.SAVE_DIR, config.IMAGE_SAVE_DIR]:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                print(f"Created directory: {dir_path}")

    @commands.Cog.listener()
    async def on_message(self, message):
        """メッセージが投稿されたときに実行される"""
        if message.author == self.bot.user:
            return

        print(f"[DEBUG] Message received from {message.author}: {message.content}")

        if message.channel.id == config.CHANNEL_ID:
            print(f"[DEBUG] Message is in target channel: {config.CHANNEL_ID}")
            today = datetime.now().date()
            file_name = f"{today.strftime('%Y-%m-%d')}.md"
            file_path = os.path.join(config.SAVE_DIR, file_name)

            if not os.path.exists(file_path):
                template = get_template(today)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(template)

            timestamp = message.created_at.strftime('%H:%M')
            content_to_append = f"\n{timestamp} -\n {message.content}\n"

            # 添付画像を保存してリンクを追記
            if message.attachments:
                print(f"[DEBUG] Message has attachments.")
                for attachment in message.attachments:
                    if attachment.content_type and attachment.content_type.startswith('image/'):
                        save_path = os.path.join(config.IMAGE_SAVE_DIR, attachment.filename)
                        await attachment.save(save_path)
                        content_to_append += f"\n![[{attachment.filename}]]\n"
                        print(f"[DEBUG] Saved image: {save_path}")

            # URLを検出して要約とサムネイルを追加
            url_match = re.search(r'https?://\S+', message.content)
            if url_match:
                url = url_match.group(0)
                print(f"[DEBUG] URL detected: {url}")
                summary, og_image_url = await get_url_summary(url)
                content_to_append += f"\n> URLの概要:\n> {summary.replace('\n', '\n> ')}\n"

                if og_image_url:
                    # サムネイルのファイル名を生成 (URLのハッシュ値と拡張子を使用)
                    import hashlib
                    from urllib.parse import urlparse
                    parsed_url = urlparse(og_image_url)
                    path_parts = parsed_url.path.split('/')
                    original_filename = path_parts[-1] if path_parts[-1] else 'image'
                    
                    # 拡張子を抽出
                    ext = os.path.splitext(original_filename)[1]
                    if not ext: # 拡張子がない場合、デフォルトで.png
                        ext = '.png'
                    
                    # URLのハッシュ値と元のファイル名からユニークなファイル名を生成
                    hash_object = hashlib.md5(og_image_url.encode())
                    base_thumbnail_filename = f"thumbnail_{hash_object.hexdigest()}"

                    downloaded_filename = await download_thumbnail(og_image_url, base_thumbnail_filename)
                    if downloaded_filename:
                        content_to_append += f"\n![[{downloaded_filename}]]\n"
            else:
                print(f"[DEBUG] No URL detected in message: {message.content}")
            
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(content_to_append)
            
            

async def setup(bot):
    await bot.add_cog(MemoHandler(bot))