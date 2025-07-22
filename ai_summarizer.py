from google import genai
from google.genai import types
import config
from logger_config import logger
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from google.api_core import exceptions

# APIキーの設定
if not config.GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file")
# The client uses the GEMINI_API_KEY environment variable automatically.
client = genai.Client()

# 検索ツールの設定 - google_search を使用
grounding_tool = types.Tool(google_search=types.GoogleSearch())
grounding_tool_retrieval = types.Tool(
    google_search_retrieval=types.GoogleSearchRetrieval()
)


@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(exceptions.ResourceExhausted),
)
def summarize_and_tag_and_explain(
    text: str, date_str: str
) -> tuple[str, str, dict[str, str]]:
    """
    与えられたテキストを要約し、タグを生成し、各タグの解説を作成します。

    Args:
        text: 対象のテキスト。
        date_str: yyyy-mm-dd形式の日付文字列。

    Returns:
        (要約文, タグの文字列, {タグ名: 解説文, ...})
    """
    prompt = f"""
    以下のテキストは、ある日のDiscordチャンネルで行われたメモの内容です。
    この内容について、以下の3つのタスクを実行してください。

    1.  **要約**: 全体を200字程度の日本語で簡潔に要約してください。
    2.  **タグ抽出**: 内容から重要なキーワードを5つ以内選び出し、`#キーワード` の形式で列挙してください。
    3.  **タグ解説**: 抽出された各キーワードについて、元のメモの内容と私の知識をもとに、個別に解説を行います。
    それぞれのキーワードに対しては、500字程度の詳細解説を記述します。
    解説の冒頭には、必ず `[[{date_str}]]` という形式で、今日の日付へのリンクを挿入してください。
    必要に応じてインターネットによる調査も行い、内容の正確性と深みを高めます。詳細解説には、関連する外部リンクや参考文献も適宜含めます。
    関連性の高い周辺情報についてさらに補足が必要な場合は、私の判断で新たなトピックやキーワードを追加し、その分もあわせて解説します。
    メモの中で重要と思われる単語や固有名詞は解説文の最後に`#単語`として記述してください。
    各キーワードごとの解説の区切りには、明確に --- を挿入してください。

    ---
    [出力フォーマット]
    [ここに要約]
    ---
    #キーワード1 #キーワード2 #キーワード3
    ---
    [TAG:キーワード1]
    [[{date_str}]]
    ここに解説文を記述
    ---
    [TAG:キーワード2]
    [[{date_str}]]
    ここに解説文を記述
    ---
    ...
    ---
    [入力テキスト]
    {text}
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=1.0,
                tools=[grounding_tool],
            ),
        )

        # レスポンスをセクションに分割
        sections = response.text.strip().split("---")

        summary = sections[0].strip()
        tags_line = sections[1].strip()

        explanations = {}
        for i in range(2, len(sections)):
            part = sections[i].strip()
            if part.startswith("[TAG:"):
                # タグ名と解説文を抽出
                tag_name_end = part.find("]")
                tag_name = part[5:tag_name_end]
                explanation = part[tag_name_end + 1 :].strip()
                explanations[tag_name] = explanation

        logger.info("--- AI Summarizer (Gemini) ---")
        logger.info(f"Generated Summary: {summary}")
        logger.info(f"Generated Tags: {tags_line}")
        logger.info(f"Generated Explanations: {len(explanations)} tags")
        logger.info("---------------------------------")

        return summary, tags_line, explanations

    except exceptions.ResourceExhausted as e:
        logger.error(f"[Error] Failed to generate content with Gemini: {e}")
        # Add more detailed error message for quota exceeded
        if "quota" in str(e).lower():
            logger.warning(
                "API usage quota exceeded. Consider upgrading your plan or waiting before retrying."
            )
            return (
                "APIの使用制限に達しました。しばらく時間をおいてから再試行してください。",
                "#api-limit-error",
                {},
            )
        raise e  # Reraise other ResourceExhausted errors to be caught by tenacity
    except Exception as e:
        logger.error(f"[Error] Failed to generate content with Gemini: {e}")
        return "処理中にエラーが発生しました。", "#error", {}


@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(exceptions.ResourceExhausted),
)
def generate_flash_supplement(text: str, url_summary: str = None) -> str:
    """
    与えられたテキストやURLの概要に対して、短い補足を生成します。

    Args:
        text: 対象のテキスト。
        url_summary: URLの概要（存在する場合）。

    Returns:
        補足の文字列。
    """
    prompt_parts = [
        "以下の情報について、簡潔な補足や関連情報を最大500文字程度の日本語で記述してください。",
        "重要なキーワードを抽出し、それについて簡潔に説明するような形式が望ましいです。",
        "URLからの外部情報を参照する場合は、信頼性の高い情報源を選んでください。",
        "**補足情報と関連情報を直接記述してください。冒頭の挨拶や確認の文言は不要です。**",
        "\n[入力テキスト]",
        text,
    ]

    if url_summary:
        prompt_parts.extend(
            [
                "\n[URLの概要]",
                url_summary,
            ]
        )

    prompt = "\n".join(prompt_parts)

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=1.0,
                tools=[grounding_tool],
            ),
        )
        supplement = response.text.strip()
        logger.info("--- AI Flash Supplement (Gemini) ---")
        logger.info(f"Generated Supplement: {supplement}")
        logger.info("---------------------------------")
        return supplement

    except exceptions.ResourceExhausted as e:
        logger.error(f"[Error] Failed to generate flash supplement with Gemini: {e}")
        # Add more detailed error message for quota exceeded
        if "quota" in str(e).lower():
            logger.warning(
                "API usage quota exceeded. Consider upgrading your plan or waiting before retrying."
            )
            return "APIの使用制限に達しました。しばらく時間をおいてから再試行するか、APIプランのアップグレードをご検討ください。"
        raise e  # Reraise other ResourceExhausted errors to be caught by tenacity
    except Exception as e:
        logger.error(f"[Error] Failed to generate flash supplement with Gemini: {e}")
        return "補足の生成中にエラーが発生しました。"


@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(exceptions.ResourceExhausted),
)
def extract_topics(text: str) -> list[str]:
    """
    与えられたテキストから重要なキーワードや話題を抽出します。

    Args:
        text: 対象のテキスト。

    Returns:
        キーワードや話題のリスト。
    """
    prompt = f"""
    以下のテキストから、重要なキーワードや話題を5つ以内で抽出してください。
    各項目は改行で区切って、単語や短いフレーズのリストとして出力してください。

    [入力テキスト]
    {text}
    """

    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
            ),
        )
        topics = response.text.strip().split("\n")
        logger.info("--- AI Topic Extractor (Gemini) ---")
        logger.info(f"Extracted Topics: {topics}")
        logger.info("------------------------------------")
        return topics

    except exceptions.ResourceExhausted as e:
        logger.error(f"[Error] Failed to extract topics with Gemini: {e}")
        # Add more detailed error message for quota exceeded
        if "quota" in str(e).lower():
            logger.warning(
                "API usage quota exceeded. Consider upgrading your plan or waiting before retrying."
            )
            return [
                "APIの使用制限に達しました。しばらく時間をおいてから再試行してください。"
            ]
        raise e  # Reraise other ResourceExhausted errors to be caught by tenacity
    except Exception as e:
        logger.error(f"[Error] Failed to extract topics with Gemini: {e}")
        return ["トピックの抽出中にエラーが発生しました。"]


@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(exceptions.ResourceExhausted),
)
def generate_topic_summary(topic: str) -> str:
    """
    与えられたトピックの概要や要約を生成します。

    Args:
        topic: 概要を生成するトピック。

    Returns:
        トピックの概要または要約。
    """
    prompt = f"""
    以下のトピックについて、簡潔な概要または要約を最大500文字程度の日本語で記述してください。
    必要に応じてインターネットによる調査も行い、内容の正確性と深みを高めてください。
    改行を文末に毎度入れてください。

    [トピック]
    {topic}
    """
    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
                tools=[grounding_tool_retrieval],
            ),
        )
        summary = response.text.strip()
        logger.info("--- AI Topic Summary (Gemini) ---")
        logger.info(f"Generated Summary for '{topic}': {summary}")
        logger.info("---------------------------------")
        return summary

    except exceptions.ResourceExhausted as e:
        logger.error(f"[Error] Failed to generate topic summary with Gemini: {e}")
        # Add more detailed error message for quota exceeded
        if "quota" in str(e).lower():
            logger.warning(
                "API usage quota exceeded. Consider upgrading your plan or waiting before retrying."
            )
            return "APIの使用制限に達しました。しばらく時間をおいてから再試行するか、APIプランのアップグレードをご検討ください。"
        raise e  # Reraise other ResourceExhausted errors to be caught by tenacity
    except Exception as e:
        logger.error(f"[Error] Failed to generate topic summary with Gemini: {e}")
        return "概要の生成中にエラーが発生しました。"
