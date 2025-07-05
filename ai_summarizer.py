import google.generativeai as genai
import config
from logger_config import logger

# APIキーの設定
if not config.GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file")
genai.configure(api_key=config.GEMINI_API_KEY)

# モデルの設定
model = genai.GenerativeModel('gemini-1.5-flash')

def summarize_and_tag_and_explain(text: str) -> tuple[str, str, dict[str, str]]:
    """
    与えられたテキストを要約し、タグを生成し、各タグの解説を作成します。

    Args:
        text: 対象のテキスト。

    Returns:
        (要約文, タグの文字列, {タグ名: 解説文, ...})
    """
    prompt = f"""
    以下のテキストは、ある日のDiscordチャンネルで行われたメモの内容です。
    この内容について、以下の3つのタスクを実行してください。

    1.  **要約**: 全体を200字程度の日本語で簡潔に要約してください。
    2.  **タグ抽出**: 内容から重要なキーワードを5つ以内選び出し、`#キーワード` の形式で列挙してください。
    3.  **タグ解説**: 抽出された各キーワードについて、元のメモの内容と私の知識をもとに、個別に解説を行います。それぞれのキーワードに対しては、500字程度の詳細解説を記述します。必要に応じてインターネットによる調査も行い、内容の正確性と深みを高めます。詳細解説には、関連する外部リンクや参考文献も適宜含めます。関連性の高い周辺情報についてさらに補足が必要な場合は、私の判断で新たなトピックやキーワードを追加し、その分もあわせて解説します。各キーワードごとの解説の区切りには、明確に --- を挿入してください。


    ---
    [出力フォーマット]
    [ここに要約]
    ---
    #キーワード1 #キーワード2 #キーワード3
    ---
    [TAG:キーワード1]
    ここに解説文を記述
    ---
    [TAG:キーワード2]
    ここに解説文を記述
    ---
    ...
    ---
    [入力テキスト]
    {text}
    """

    try:
        response = model.generate_content(prompt)
        
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
