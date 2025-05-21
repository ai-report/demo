from llm import get_llm_response
import random

GEMINI_MODEL_NAME = "gemini-1.5-flash-latest"

# 全域定義 (與前端同步)
# time_units = ["", "一刻", "二刻", "三刻", "正"]
# shichen = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]


def get_normal_event():
    agent = ["李白","李清照","李昇暾","莊子"]
    place = ["河邊","酒館","李清照家","莊子家","衙門","診所","書院","城門"]
    random_hour = random.randint(0, 23) 
    random_min = random.randint(0,3) * 15
    agent1, agent2 = random.sample(agent, 2)
    random_place = random.choice(place)
    prompt_text = f"""
    在{random_hour}{random_min}時，{agent1}與{agent2}在{random_place}相遇。請為他們的相遇構想一個簡單的事件描述。
    并且你的回應格式如下：
    時間：{random_hour}{random_min}
    地點：{random_place}
    人物：{agent1},{agent2}
    事件：（你的回復，簡單的事件描述）"""
    random_normal_event = get_llm_response(prompt_text, provider='gemini',
                                        model_name=GEMINI_MODEL_NAME)
    
    return random_normal_event