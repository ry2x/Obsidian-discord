import discord
from discord.ext import commands
import os
import re
from datetime import datetime, timedelta
import config
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from logger_config import logger
from discord import app_commands, Interaction, Message, SelectOption
from discord.ui import Select, View
from ai_summarizer import (
    generate_flash_supplement,
    extract_topics,
    generate_topic_summary,
)


def get_template(date_obj):
    """指定された日付のテンプレート文字列を生成する"""
    today_str = date_obj.strftime("%Y-%m-%d")
    prev_day_str = (date_obj - timedelta(days=1)).strftime("%Y-%m-%d")
    next_day_str = (date_obj + timedelta(days=1)).strftime("%Y-%m-%d")
    prev_week_str = (date_obj - timedelta(days=7)).strftime("%Y-%m-%d")
    next_week_str = (date_obj + timedelta(days=7)).strftime("%Y-%m-%d")

    return f"""{today_str}
[[{prev_week_str}]]||[[{prev_day_str}]]||[[{next_day_str}]]||[[{next_week_str}]]
---

## メモ
"""


async def get_url_summary(url):
    """URLからタイトル、description、og:imageを取得する"""
    logger.debug(f"Attempting to fetch URL: {url}")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                logger.debug(f"URL: {url}, Status: {response.status}")
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, "html.parser")
                    title = soup.title.string if soup.title else "タイトルなし"
                    description_tag = soup.find("meta", attrs={"name": "description"})
                    description = (
                        description_tag["content"] if description_tag else "説明文なし"
                    )

                    og_image_url = None
                    og_image_tag = soup.find("meta", property="og:image")
                    if og_image_tag and "content" in og_image_tag.attrs:
                        og_image_url = og_image_tag["content"]
                        logger.debug(f"Extracted og:image: {og_image_url}")

                    logger.debug(
                        f"Extracted Title: {title.strip()}, Description: {description.strip()}"
                    )
                    return (
                        f"タイトル: {title.strip()}\n説明: {description.strip()}",
                        og_image_url,
                    )
                else:
                    return (
                        f"ページの取得に失敗しました。ステータスコード: {response.status}",
                        None,
                    )
    except aiohttp.ClientError as e:
        logger.error(f"aiohttp ClientError fetching URL {url}: {e}")
        return "URLの取得中にネットワークエラーが発生しました。", None
    except Exception as e:
        logger.error(f"Unexpected error fetching or parsing URL {url}: {e}")
        return "URLの処理中に予期せぬエラーが発生しました。", None


async def download_thumbnail(url, base_filename):
    """指定されたURLから画像をダウンロードし、適切な拡張子で保存する"""
    logger.debug(f"Attempting to download thumbnail from: {url}")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    content_type = response.headers.get("Content-Type", "")
                    if "image/" in content_type:
                        # Content-Typeから適切な拡張子を決定
                        if "image/jpeg" in content_type:
                            ext = ".jpg"
                        elif "image/png" in content_type:
                            ext = ".png"
                        elif "image/gif" in content_type:
                            ext = ".gif"
                        elif "image/webp" in content_type:
                            ext = ".webp"
                        else:
                            logger.debug(
                                f"Unsupported image content type: {content_type}"
                            )
                            return None

                        filename = f"{base_filename}{ext}"
                        save_path = os.path.join(config.IMAGE_SAVE_DIR, filename)
                        with open(save_path, "wb") as f:
                            f.write(await response.read())
                        logger.debug(f"Saved thumbnail: {save_path}")
                        return filename
                    else:
                        logger.debug(f"URL content is not an image: {content_type}")
                        return None
                else:
                    logger.error(
                        f"Failed to download thumbnail from {url}. Status: {response.status}"
                    )
                    return None
    except aiohttp.ClientError as e:
        logger.error(f"aiohttp ClientError downloading thumbnail {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error downloading thumbnail {url}: {e}")
        return None


class MemoHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.add_to_memo_context_menu = app_commands.ContextMenu(
            name="メモに追加",
            callback=self.add_to_memo_callback,
        )
        self.bot.tree.add_command(self.add_to_memo_context_menu)

        self.extract_topic_context_menu = app_commands.ContextMenu(
            name="単語/話題を抽出してメモ",
            callback=self.extract_topic_callback,
        )
        self.bot.tree.add_command(self.extract_topic_context_menu)

        self.lookup_topic_context_menu = app_commands.ContextMenu(
            name="単語/話題を調べる",
            callback=self.lookup_topic_callback,
        )
        self.bot.tree.add_command(self.lookup_topic_context_menu)

        # 保存ディレクトリが存在しない場合は作成
        for dir_path in [config.SAVE_DIR, config.IMAGE_SAVE_DIR]:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                logger.info(f"Created directory: {dir_path}")

    async def process_message_for_memo(self, message: Message, force_add: bool = False):
        """メッセージを処理してメモファイルに追記する共通ロジック"""
        if not force_add and message.channel.id != config.CHANNEL_ID:
            logger.debug(f"Message is not in target channel: {message.channel.id}")
            return

        today = datetime.now().date()
        file_name = f"{today.strftime('%Y-%m-%d')}.md"
        file_path = os.path.join(config.SAVE_DIR, file_name)

        if not os.path.exists(file_path):
            template = get_template(today)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(template)

        timestamp = datetime.now().strftime("%H:%M")
        content_to_append = f"\n{timestamp}\n{message.content}\n"

        # 添付画像を保存してリンクを追記
        if message.attachments:
            logger.debug("Message has attachments.")
            for attachment in message.attachments:
                if attachment.content_type and attachment.content_type.startswith(
                    "image/"
                ):
                    save_path = os.path.join(config.IMAGE_SAVE_DIR, attachment.filename)
                    await attachment.save(save_path)
                    content_to_append += f"\n![[{attachment.filename}]]\n"
                    logger.debug(f"Saved image: {save_path}")

        # URLを検出して要約とサムネイルを追加
        url_match = re.search(r"https?://\S+", message.content)
        url_summary = None
        if url_match:
            url = url_match.group(0)
            logger.debug(f"URL detected: {url}")
            summary, og_image_url = await get_url_summary(url)
            url_summary = summary  # 概要を保存
            content_to_append += f"\n> URLの概要:\n> {summary.replace('\n', '\n> ')}\n"

            if og_image_url:
                import hashlib

                parsed_url = urlparse(og_image_url)
                path_parts = parsed_url.path.split("/")
                original_filename = path_parts[-1] if path_parts[-1] else "image"
                os.path.splitext(original_filename)[1] or ".png"
                hash_object = hashlib.md5(og_image_url.encode())
                base_thumbnail_filename = f"thumbnail_{hash_object.hexdigest()}"
                downloaded_filename = await download_thumbnail(
                    og_image_url, base_thumbnail_filename
                )
                if downloaded_filename:
                    content_to_append += f"\n![[{downloaded_filename}]]\n"
        else:
            logger.debug(f"No URL detected in message: {message.content}")

        # AIによる補足を生成
        supplement = generate_flash_supplement(message.content, url_summary=url_summary)
        content_to_append += (
            f"\n> [!info] AI's Small Tip\n> {supplement.replace('\n', '\n> ')}\n"
        )

        with open(file_path, "a", encoding="utf-8") as f:
            f.write(content_to_append)
        logger.info(
            f"Appended message from {message.author.display_name} to {file_name}"
        )

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        """メッセージが投稿されたときに実行される"""
        if message.author == self.bot.user:
            return

        logger.debug(f"Message received from {message.author}: {message.content}")
        await self.process_message_for_memo(message)

    async def add_to_memo_callback(self, interaction: Interaction, message: Message):
        """コンテキストメニューから呼び出されたときの処理"""
        await interaction.response.defer(ephemeral=True)
        try:
            await self.process_message_for_memo(message, force_add=True)
            await interaction.followup.send(
                "メッセージを本日のメモに追加しました。", ephemeral=True
            )
        except Exception as e:
            logger.error(f"Failed to add message to memo from context menu: {e}")
            await interaction.followup.send(
                "メモへの追加中にエラーが発生しました。", ephemeral=True
            )

    async def extract_topic_callback(self, interaction: Interaction, message: Message):
        await interaction.response.defer(ephemeral=True)
        try:
            topics = []
            # メッセージ内のURLを抽出
            url_matches = re.findall(r"https?://\S+", message.content)
            if url_matches:
                topics.extend(url_matches)

            # AIでトピックを抽出
            ai_topics = extract_topics(message.content)
            topics.extend(ai_topics)

            if not topics:
                await interaction.followup.send(
                    "抽出できる単語や話題が見つかりませんでした。", ephemeral=True
                )
                return

            # 重複を削除し、リストをユニークにする
            topics = list(dict.fromkeys(topics))

            view = TopicSelectView(topics, message, self, "add_to_memo")
            await interaction.followup.send(
                "メモに追加するトピックを選択してください。", view=view, ephemeral=True
            )

        except Exception as e:
            logger.error(f"Failed to extract topics from context menu: {e}")
            await interaction.followup.send(
                "トピックの抽出中にエラーが発生しました。", ephemeral=True
            )

    async def _handle_add_topic_to_memo(
        self, interaction: Interaction, selected_topic: str, original_message: Message
    ):
        today = datetime.now().date()
        file_name = f"{today.strftime('%Y-%m-%d')}.md"
        file_path = os.path.join(config.SAVE_DIR, file_name)

        if not os.path.exists(file_path):
            template = get_template(today)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(template)

        timestamp = datetime.now().strftime("%H:%M")

        # AIによる補足を生成
        supplement = generate_flash_supplement(selected_topic)
        content_to_append = f"\n{timestamp}\n{selected_topic}\n"
        content_to_append += (
            f"\n> [!info] AI's Small Tip\n> {supplement.replace('\n', '\n> ')}\n"
        )

        with open(file_path, "a", encoding="utf-8") as f:
            f.write(content_to_append)

        logger.info(
            f"Appended topic '{selected_topic}' from {original_message.author.display_name} to {file_name}"
        )
        await interaction.followup.send(
            f"トピック「{selected_topic}」を本日のメモに追加しました。", ephemeral=True
        )

    async def _handle_lookup_topic_selection(
        self, interaction: Interaction, selected_topic: str, original_message: Message
    ):
        summary = generate_topic_summary(selected_topic)
        view = SummaryDisplayView(selected_topic, summary)
        await interaction.followup.send(
            f"**{selected_topic}** の概要:\n{summary}", view=view, ephemeral=True
        )

    async def lookup_topic_callback(self, interaction: Interaction, message: Message):
        await interaction.response.defer(ephemeral=True)
        try:
            topics = []
            # メッセージ内のURLを抽出
            url_matches = re.findall(r"https?://\S+", message.content)
            if url_matches:
                topics.extend(url_matches)

            # AIでトピックを抽出
            ai_topics = extract_topics(message.content)
            topics.extend(ai_topics)

            if not topics:
                await interaction.followup.send(
                    "抽出できる単語や話題が見つかりませんでした。", ephemeral=True
                )
                return

            # 重複を削除し、リストをユニークにする
            topics = list(dict.fromkeys(topics))

            view = TopicSelectView(topics, message, self, "lookup_topic")
            await interaction.followup.send(
                "概要を調べるトピックを選択してください。", view=view, ephemeral=True
            )

        except Exception as e:
            logger.error(f"Failed to lookup topics from context menu: {e}")
            await interaction.followup.send(
                "トピックの検索中にエラーが発生しました。", ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(MemoHandler(bot))


class TopicSelectView(View):
    def __init__(
        self,
        topics: list[str],
        original_message: Message,
        handler_instance,
        callback_type: str,
    ):
        super().__init__(timeout=180)
        self.original_message = original_message
        self.handler_instance = handler_instance  # Reference to MemoHandler instance
        self.callback_type = callback_type
        options = [SelectOption(label=topic, value=topic) for topic in topics]
        self.select = Select(
            placeholder="トピックを選択してください...",
            options=options,
            min_values=1,
            max_values=1,
        )
        self.select.callback = self.select_callback
        self.add_item(self.select)

    async def select_callback(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        selected_topic = self.select.values[0]

        if self.callback_type == "add_to_memo":
            await self.handler_instance._handle_add_topic_to_memo(
                interaction, selected_topic, self.original_message
            )
        elif self.callback_type == "lookup_topic":
            await self.handler_instance._handle_lookup_topic_selection(
                interaction, selected_topic, self.original_message
            )
        else:
            await interaction.followup.send(
                "不明なコールバックタイプです。", ephemeral=True
            )


class SummaryDisplayView(View):
    def __init__(self, topic: str, summary: str):
        super().__init__(timeout=180)
        self.topic = topic
        self.summary = summary

    @discord.ui.button(
        label="メモに追加",
        custom_id="add_summary_to_memo",
        style=discord.ButtonStyle.primary,
    )
    async def add_summary_to_memo_button(
        self, interaction: Interaction, button: discord.ui.Button
    ):
        await interaction.response.defer(ephemeral=True)
        today = datetime.now().date()
        file_name = f"{today.strftime('%Y-%m-%d')}.md"
        file_path = os.path.join(config.SAVE_DIR, file_name)

        if not os.path.exists(file_path):
            template = get_template(today)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(template)

        timestamp = datetime.now().strftime("%H:%M")
        content_to_append = f"""
            {timestamp}
            ## {self.topic} の概要
            {self.summary}
        """
        content_to_append = f"\n{timestamp}\n{self.topic}\n> [info] {self.topic} の検索結果 by AI\n> {self.summary.replace('\n', '\n> ')}\n"

        with open(file_path, "a", encoding="utf-8") as f:
            f.write(content_to_append)

        logger.info(f"Appended summary for '{self.topic}' to {file_name}")
        await interaction.followup.send(
            f"トピック「{self.topic}」の概要を本日のメモに追加しました。",
            ephemeral=True,
        )
