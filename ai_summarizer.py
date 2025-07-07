from google import genai
from google.genai import types
import config
from logger_config import logger

# APIキーの設定
if not config.GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file")
client = genai.Client(api_key=config.GEMINI_API_KEY)

def summarize_and_tag_and_explain(text: str, date_str: str) -> tuple[str, str, dict[str, str]]:
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
    3.  **タグ解説**: 抽出された各キーワードについて、元のメモの内容と私の知識をもとに、個別に解説を行います。それぞれのキーワードに対しては、500字程度の詳細解説を記述します。解説の冒頭には、必ず `[[{date_str}]]` という形式で、今日の日付へのリンクを挿入してください。必要に応じてインターネットによる調査も行い、内容の正確性と深みを高めます。詳細解説には、関連する外部リンクや参考文献も適宜含めます。関連性の高い周辺情報についてさらに補足が必要な場合は、私の判断で新たなトピックやキーワードを追加し、その分もあわせて解説します。メモの中で重要と思われる単語や固有名詞は解説文の最後に`#単語`として記述してください。各キーワードごとの解説の区切りには、明確に --- を挿入してください。

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
            model="gemini-1.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=0)
            )
        )

        # レスポンスをセクションに分割
        sections = response.text.strip().split('---')
        
        summary = sections[0].strip()
        tags_line = sections[1].strip()
        
        explanations = {}
        for i in range(2, len(sections)):
            part = sections[i].strip()
            if part.startswith('[TAG:'):
                # タグ名と解説文を抽出
                tag_name_end = part.find(']')
                tag_name = part[5:tag_name_end]
                explanation = part[tag_name_end+1:].strip()
                explanations[tag_name] = explanation

        logger.info(f"--- AI Summarizer (Gemini) ---")
        logger.info(f"Generated Summary: {summary}")
        logger.info(f"Generated Tags: {tags_line}")
        logger.info(f"Generated Explanations: {len(explanations)} tags")
        logger.info(f"---------------------------------")

        return summary, tags_line, explanations

    except Exception as e:
        logger.error(f"[Error] Failed to generate content with Gemini: {e}")
        return f"処理中にエラーが発生しました。", "#error", {}

def generate_flash_supplement(text: str) -> str:
    """
    与えられたテキストに対して、短い補足を生成します。

    Args:
        text: 対象のテキスト。

    Returns:
        補足の文字列。
    """
    prompt = f"""
    以下のメモの内容について、簡潔な補足や関連情報を100文字程度の日本語で記述してください。
    重要なキーワードを抽出し、それについて簡潔に説明するような形式が望ましいです。

    [入力テキスト]
    {text}
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=prompt
        )
        supplement = response.text.strip()
        logger.info(f"--- AI Flash Supplement (Gemini) ---")
        logger.info(f"Generated Supplement: {supplement}")
        logger.info(f"---------------------------------")
        return supplement

    except Exception as e:
        logger.error(f"[Error] Failed to generate flash supplement with Gemini: {e}")
        return "補足の生成中にエラーが発生しました。"
