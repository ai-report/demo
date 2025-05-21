# config.py
# 這個檔案包含了 backend_app.py 中所有可供使用者自訂的設定。

# --- Google Gemini API 設定 ---
GEMINI_MODEL_NAME = "gemini-1.5-flash-latest"

# --- DeepSeek API 設定 ---
# 請將您的 DeepSeek API 金鑰設定在 .env 檔案的 DEEPSEEK_API_KEY
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions" # 請確認此 URL 是否正確
DEEPSEEK_MODEL_NAME = "deepseek-chat" # 或適合生成詩詞的模型，例如 deepseek-coder (需確認)
DEEPSEEK_POEM_PROMPT_THEME = "一座寧靜的古代城市與其居民的日常生活" # 詩的主題

# --- 全域時間定義 (與前端同步) ---
TIME_UNITS = ["初刻", "一刻", "二刻", "三刻", "正"]
SHICHEN = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# --- 代理記憶體設定 ---
MAX_MEMORY_STREAM_LENGTH = 100
RECENT_MEMORIES_TO_RETURN = 5

# --- 強制會面設定 ---
MEETING_TIME = "辰時三刻"
MEETING_LOCATION = "酒館"
AGENTS_TO_MEET_IDS = ["li_xiucai", "zhao_zhanggui"]

# --- 前端定義的地點列表 (用於驗證或提示 LLM) ---
AVAILABLE_LOCATIONS = ["河川", "書院", "酒館", "衙門", "城門", "診所"]

# --- 代理人 (Agent) 初始設定 ---
AGENTS_INITIAL_SETUP = {
    "li_xiucai": {
        "agent_id": "li_xiucai",
        "name": "李秀才",
        "persona_summary": "一位居住在古城「雲夢城」、勤奮苦讀、準備科舉的年輕書生。他性格溫和有禮，但有時略顯迂腐。他對詩詞歌賦有濃厚興趣，常去書院研讀或與同窗交流。他夢想有朝一日能金榜題名，光耀門楣。他與城中一些文人雅士略有交情，偶爾也會去酒館小酌，聽聽坊間傳聞。",
        "initial_location": "河川"
    },
    "zhao_zhanggui": {
        "agent_id": "zhao_zhanggui",
        "name": "趙掌櫃",
        "persona_summary": "「雲夢城」診所「仁心堂」的老闆，約四十歲，精明能幹，略懂醫術，為人現實但心地不壞。他每天忙於打理診所生意，接待病人，採購藥材。他消息靈通，對城中大小事務都有所耳聞。他希望診所生意興隆，也關心家人的健康。",
        "initial_location": "診所"
    },
}

# --- LLM 安全性與生成設定 (Gemini & DeepSeek 可能有不同設定方式) ---
# Gemini
LLM_SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]
LLM_GENERATION_CONFIG = { # 主要用於 Gemini
    "temperature": 0.8,
    "max_output_tokens": 2048,
}

# DeepSeek 的生成設定 (如果 API 支援，可以在呼叫時傳遞)
DEEPSEEK_GENERATION_CONFIG = {
    "temperature": 0.7, # 詩歌生成溫度可以稍低，使其更穩定
    "max_tokens": 200,  # 詩歌通常不需要太長
}


# --- LLM Prompt 模板 ---
DAILY_PLAN_PROMPT_TEMPLATE = """
角色名稱: {agent_name}
角色人設: {persona_summary}
今日日期: {current_date_str}
最近的記憶/反思: {last_reflection}
可選地點清單: {locations_list_str}
主要目標: 根據他的人設和最近記憶，他今天可能想做什麼？

請為 {agent_name} 規劃一份從卯時到戌時的詳細日程表。
日程表應包含以下時辰點：卯時初刻, 卯時二刻, 辰時初刻, 辰時三刻, 巳時二刻, 巳時三刻, 午時初刻, 未時初刻, 未時二刻, 申時初刻, 酉時初刻, 戌時初刻。
每個條目應包含：
1. "time_str": (字串) 時間描述 (例如："卯時初刻")
2. "location": (字串) 地點 (必須從提供的「可選地點清單」中選擇，例如："書院")
3. "action": (字串) 具體活動 (簡潔描述，例如："在書院讀書")
4. "thought": (字串) 內心想法 (例如："（今天一定要把這本書看完。）")
5. "dialogue": (字串, 可選) 如果此活動涉及與人交談或自言自語（非會面時的特定對話），則填寫，否則留空 ""。對話內容不要包含換行符。

請嚴格以JSON列表格式輸出，不要包含任何JSON格式以外的文字或解釋。
範例單個條目：{{"time_str": "卯時初刻", "location": "河川", "action": "起床、整理儀容", "thought": "（一日之計在於晨。）", "dialogue": ""}}
"""

MEETING_DIALOGUE_PROMPT_TEMPLATE = """
場景：在古代中國的「{location}」，時間是「{time_str}」。
人物A：{first_speaker_name} (ID: {first_speaker_agent_id})。人設：{first_speaker_persona}。他本來計劃做的事情是：『{first_speaker_original_action}』。他最近的記憶片段：『{first_speaker_recent_memories}』。
人物B：{second_speaker_name} (ID: {second_speaker_agent_id})。人設：{second_speaker_persona}。他本來計劃做的事情是：『{second_speaker_original_action}』。他最近的記憶片段：『{second_speaker_recent_memories}』。

他們偶然相遇了。請生成一段他們之間簡短、自然、符合人設的兩輪對話。
{first_speaker_name} 先開口說一句話。
然後 {second_speaker_name} 回應一句話。

請嚴格以 JSON 物件格式輸出，包含兩個鍵（鍵的名稱必須是代理的 agent_id 加上 "_dialogue"）：
"{first_speaker_agent_id}_dialogue": "{first_speaker_name}說的話"
"{second_speaker_agent_id}_dialogue": "{second_speaker_name}說的話"

例如，如果 {first_speaker_name} 的 agent_id 是 "li_xiucai"，{second_speaker_name} 的 agent_id 是 "zhao_zhanggui"：
{{
  "li_xiucai_dialogue": "哎呀，這不是趙掌櫃嗎？真巧啊！",
  "zhao_zhanggui_dialogue": "原來是李秀才！的確巧合，你也來{location}辦事？"
}}
確保對話內容簡短，每句話不超過30字。對話內容不要包含換行符。
"""

# DeepSeek 詩歌生成 Prompt
# 可用變數: {theme}
POEM_GENERATION_PROMPT_TEMPLATE = "請以「{theme}」為主題，創作一首優美的五言或七言古詩，至少四句。風格典雅，意境悠遠。"


# --- Flask App 設定 ---
FLASK_PORT = 5001
FLASK_DEBUG_MODE = True

# 放各LLM呼叫時要丟的設定參數
import google.generativeai as genai

config = {
    'gemini': {
        'safety_settings': [
            {"category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ],
        'generation_config': genai.types.GenerationConfig(
            temperature=0.75,
        )
    }
}
