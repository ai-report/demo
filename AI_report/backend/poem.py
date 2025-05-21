import json
import os
import time
from dotenv import load_dotenv
import requests
from llm import get_llm_response


def poem_sound(TEXT_TO_SPEAK, file_name):

    load_dotenv()
    API_KEY = os.getenv('voice')

    headers = {
        "xi-api-key": API_KEY
    }

# 2. 使用克隆聲音合成語音


    def synthesize_speech(voice_id, text):
        print("🗣️ 開始合成語音...")
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        json_data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.8
            }
        }

        response = requests.post(url, headers=headers, json=json_data)

        if response.status_code == 200:
            with open(f"C:\\Users\\user\\OneDrive\\documents\\code\\Python\\Projects\\AI_report\\AI_report\\frontend\\assets\\audio\\{str(file_name).replace(":", "")}.mp3", "wb") as f:
                f.write(response.content)
            print("✅ 合成完成，已儲存為 output.mp3")
        else:
            print(f"❌ 合成語音失敗：{response.text}")

    voice_id = "crEjeSzlrwZRyvlQkB8c"
    synthesize_speech(voice_id, TEXT_TO_SPEAK)


def get_deepseek_poem(file_name):

    # 使用 config 中的詩歌主題和 Prompt 模板
    prompt_content = """
    請以「一座古代城市與其居民的日常生活」為主題，創作一首優美的五言古詩，共四句。風格典雅，意境悠遠，朗朗上口。
    並且請僅輸出詩詞部分。
    輸出簡體中文與繁體中文版本，格式如下:
    {"簡": "xxx", "繁": "xxx"}
    """

    # try:
    # 如果 HTTP 請求返回了不成功的狀態碼，則拋出 HTTPError 異常
    response = get_llm_response(prompt_content, provider='deepseek')
    print(response)
    response = json.loads(response)
    poem_sound(response['簡'], file_name)
    # response_data = response.json()
    return response['繁']

    # except:
    #     return "Deepseek沒有回應，詩詞產生失敗"
