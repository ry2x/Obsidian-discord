import google.generativeai as genai
import config

# APIキーの設定
if not config.GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file")
genai.configure(api_key=config.GEMINI_API_KEY)

# モデルの設定
model = genai.GenerativeModel('gemini-1.5-flash')

def summarize_and_tag(text: str) -> tuple[str, str]:
    """
    与えられたテキストをGemini APIを使用して要約し、関連するタグを生成します。

    Args:
        text: 要約およびタグ付けする対象のテキスト。

    Returns:
        (要約文, タグの文字列)
    """
    prompt = f"""
    以下のテキストは、ある日のDiscordチャンネルで行ってるメモの内容です。
    この内容を最大10行程度の日本語で要約し、重要なキーワードを選び、`#タグ` の形式で抽出してください。

    フォーマット:
    [ここに要約]
    #キーワード1 #キーワード2 #キーワード3...

    テキスト:
    ---
    {text}
    ---
    """

    try:
        response = model.generate_content(prompt)
        
        # レスポンスから要約とタグを分離する
        parts = response.text.strip().split('\n')
        
        summary_lines = []
        tags_line = ""
        
        for part in parts:
            if part.startswith('#'):
                tags_line = part
            elif part.strip(): # 空行を無視する
                summary_lines.append(part)
        
        summary = "\n".join(summary_lines)
        tags = tags_line if tags_line else "#general"

        print(f"--- AI Summarizer (Gemini) ---")
        print(f"Generated Summary: {summary}")
        print(f"Generated Tags: {tags}")
        print(f"---------------------------------")

        return summary, tags

    except Exception as e:
        print(f"[Error] Failed to generate summary with Gemini: {e}")
        # エラーが発生した場合は、フォールバックとして簡単なサマリーを返す
        return f"要約の生成中にエラーが発生しました。", "#error"
