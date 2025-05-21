# backend_app.py
from dotenv import load_dotenv
from flask import Flask, jsonify, request as flask_request
from flask_cors import CORS
import datetime
import os
import json
from collections import deque
import random
import google.generativeai as genai
import traceback
import requests  # <--- 新增導入 requests

# --- 導入自訂設定 ---
import config

# --- API 金鑰設定 ---
load_dotenv()
gemini_api_key = os.getenv("GOOGLE_API_KEY")
deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")  # <--- 載入 DeepSeek API 金鑰

# --- Gemini API 設定 ---
if not gemini_api_key:
    print("警告：未找到 GOOGLE_API_KEY 環境變數。Gemini 功能將受限。")
else:
    try:
        genai.configure(api_key=gemini_api_key)
        print("Gemini API 金鑰已成功設定。")
    except Exception as e:
        print(f"設定 Gemini API 時發生錯誤: {e}")
        gemini_api_key = None

# --- DeepSeek API 檢查 ---
if not deepseek_api_key:
    print("警告：未找到 DEEPSEEK_API_KEY 環境變數。詩歌生成功能將無法使用。")


# --- Agent 類別定義 (與之前相同) ---
class Agent:
    def __init__(self, agent_id, name, persona_summary, initial_location="河川"):
        self.agent_id = agent_id
        self.name = name
        self.persona_summary = persona_summary
        self.current_location = initial_location
        self.current_action = "準備開始一天的生活"
        self.current_thought = "（新的一天，充滿未知。）"
        self.current_dialogue = ""
        self.memory_stream = deque(maxlen=config.MAX_MEMORY_STREAM_LENGTH)
        self.daily_schedule = []
        self.current_schedule_index = 0
        self.original_action_at_meeting_time = ""

        self.safety_settings = config.LLM_SAFETY_SETTINGS
        self.generation_config = genai.types.GenerationConfig(
            **config.LLM_GENERATION_CONFIG)

    def add_memory(self, game_time_str, memory_type, description, importance,
                   related_agent_ids=None):
        if related_agent_ids is None:
            related_agent_ids = []
        new_memory = {
            "timestamp": game_time_str, "type": memory_type,
            "description": description,
            "importance": importance, "related_agents": related_agent_ids
        }
        self.memory_stream.append(new_memory)

    def observe_environment(self, game_time_str, all_agents_map):
        agents_in_same_location = []
        for other_agent_id, other_agent_obj in all_agents_map.items():
            if other_agent_id != self.agent_id and \
                    other_agent_obj.current_location == self.current_location:
                agents_in_same_location.append(other_agent_obj)
        if agents_in_same_location:
            observed_names = ", ".join(
                [a.name for a in agents_in_same_location])
            description = f"在 {self.current_location} 看到了 {observed_names}。"
            self.add_memory(game_time_str, "observation_เห็น_คนอื่น",
                            description,
                            3,
                            [a.agent_id for a in agents_in_same_location])

    def _parse_time_to_indices(self, time_str_input):
        if not isinstance(time_str_input, str):
            return None, None
        if '時' in time_str_input:
            try:
                s_str, u_str = time_str_input.split('時', 1)
                s_idx = config.SHICHEN.index(s_str)
                u_idx = config.TIME_UNITS.index(u_str)
                return s_idx, u_idx
            except (ValueError, IndexError):
                pass
        for s_len in range(len(config.SHICHEN[0]), 0, -1):
            if len(time_str_input) > 1:
                s_str_candidate = time_str_input[0]
                u_str_candidate = time_str_input[1:]
                try:
                    s_idx = config.SHICHEN.index(s_str_candidate)
                    u_idx = config.TIME_UNITS.index(u_str_candidate)
                    return s_idx, u_idx
                except (ValueError, IndexError):
                    pass
        return None, None

    def _compare_time_strings(self, time_str1, time_str2):
        s1_idx, u1_idx = self._parse_time_to_indices(time_str1)
        s2_idx, u2_idx = self._parse_time_to_indices(time_str2)
        if s1_idx is None or s2_idx is None or\
                u1_idx is None or u2_idx is None:
            return 0
        if s1_idx < s2_idx:
            return -1
        if s1_idx > s2_idx:
            return 1
        if u1_idx < u2_idx:
            return -1
        if u1_idx > u2_idx:
            return 1
        return 0

    def _get_llm_response(self, prompt_text, purpose="", model_to_use=None):
        actual_model_name = model_to_use if model_to_use\
            else config.GEMINI_MODEL_NAME
        if not gemini_api_key:
            error_message = "錯誤：Gemini API 金鑰未設定或設定失敗。無法呼叫 LLM。"
            # print(error_message) # 減少控制台輸出
            if purpose == "daily_plan":
                return [{
                    "time_str": "錯誤",
                    "location": "API金鑰",
                    "action": "API金鑰問題",
                    "thought": "請檢查後端API金鑰設定",
                    "dialogue": ""
                }]
            if purpose == "interaction_dialogue":
                return {
                    "error": error_message,
                    "agent1_dialogue": "（API金鑰問題）",
                    "agent2_dialogue": "（API金鑰問題）"
                }
            return f"（{error_message}）"
        try:
            model = genai.GenerativeModel(
                model_name=actual_model_name,
                safety_settings=self.safety_settings,
                generation_config=self.generation_config
            )
            response = model.generate_content(prompt_text)
            generated_text = ""
            if response.candidates and hasattr(
                response.candidates[0], 'content') and \
                hasattr(response.candidates[0].content, 'parts') \
                    and response.candidates[0].content.parts:
                generated_text = "".join(
                    part.text for part in response.candidates[0].content.parts
                    if hasattr(part, 'text'))
            elif hasattr(response, 'text'):
                generated_text = response.text
            else:
                # print(f"錯誤：Gemini API 回應中未找到有效的文本內容 for {self.name} ({purpose})。") # 減少控制台輸出
                if hasattr(response, 'prompt_feedback') and\
                        response.prompt_feedback:
                    # print(f"Gemini API Prompt Feedback for {self.name}: {response.prompt_feedback}") # 減少控制台輸出
                    if any(hasattr(rating, 'blocked') and rating.blocked
                           for rating in response.
                           prompt_feedback.safety_ratings):
                        blocked_reason = next(
                            (
                                str(rating.category).split(
                                    '.')[-1] for rating in
                                response.prompt_feedback.safety_ratings
                                if hasattr(rating, 'blocked')
                                and rating.blocked
                            ),
                            "未知原因"
                        )
                        # print(f"LLM 內容被安全設定阻擋 for {self.name} ({purpose}). 原因: {blocked_reason}") # 減少控制台輸出
                        error_msg_blocked = f"LLM內容被安全設定阻擋({blocked_reason})"
                        if purpose == "daily_plan":
                            return [{
                                "time_str": "錯誤",
                                "location": "安全阻擋",
                                "action": error_msg_blocked,
                                "thought": "請檢查Prompt或調整安全設定",
                                "dialogue": ""
                            }]
                        if purpose == "interaction_dialogue":
                            return {
                                "error": error_msg_blocked,
                                "agent1_dialogue": f"（{error_msg_blocked}）",
                                "agent2_dialogue": f"（{error_msg_blocked}）"
                            }

            if purpose == "daily_plan" or purpose == "interaction_dialogue":
                if not generated_text.strip():
                    error_msg_no_content = "LLM未返回有效內容"
                    # print(f"錯誤: {error_msg_no_content} for {self.name} ({purpose}).") # 減少控制台輸出
                    if purpose == "daily_plan":
                        return [{
                            "time_str": "錯誤", "location": "LLM空回應",
                            "action": error_msg_no_content,
                            "thought": "API呼叫可能成功但無文本輸出",
                            "dialogue": ""
                        }]
                    if purpose == "interaction_dialogue":
                        return {
                            "error": error_msg_no_content,
                            "agent1_dialogue": f"（{error_msg_no_content}）",
                            "agent2_dialogue": f"（{error_msg_no_content}）"
                        }

                text_to_parse = generated_text.strip()
                if text_to_parse.startswith("```json"):
                    text_to_parse = text_to_parse[len("```json"):]
                if text_to_parse.endswith("```"):
                    text_to_parse = text_to_parse[:-len("```")]
                text_to_parse = text_to_parse.strip()
                if text_to_parse.startswith('\uFEFF'):
                    text_to_parse = text_to_parse[1:]
                text_to_parse = text_to_parse.replace('\u00A0', ' ')
                text_to_parse = text_to_parse.strip()

                try:
                    parsed_json = json.loads(text_to_parse)
                    return parsed_json
                except json.JSONDecodeError as e_parse:
                    print(
                        f"錯誤：JSON 解析失敗 for {self.name} ({purpose}): {e_parse}")
                    # 縮短日誌
                    print(
                        f"原始 Gemini 回應 (generated_text strip): '{
                            generated_text.strip()[:200]}...'"
                    )
                    # 縮短日誌
                    print(
                        f"最終嘗試解析的文本 (text_to_parse): '{
                            text_to_parse[:200]}...'"
                        )
                    error_action_msg = "日程解析失敗(清理後)"
                    error_thought_msg = "LLM輸出格式問題"  # 簡化
                    if purpose == "daily_plan":
                        return [{
                            "time_str": "錯誤",
                            "location": "JSON解析",
                            "action": error_action_msg,
                            "thought": error_thought_msg,
                            "dialogue": ""
                        }]
                    if purpose == "interaction_dialogue":
                        return {
                            "error": f"JSON解析失敗(清理後): {e_parse}",
                            "agent1_dialogue": "（JSON解析問題）",
                            "agent2_dialogue": "（JSON解析問題）"
                        }
            return generated_text
        except Exception as e:
            print(
                f"呼叫 Gemini API 時發生嚴重錯誤 "
                f"({actual_model_name} for {self.name}, {purpose}): {e}"
            )
            # traceback.print_exc() # 偵錯時開啟
            error_action_msg_api = "API呼叫失敗"
            if purpose == "daily_plan":
                # 限制錯誤訊息長度
                return [{
                    "time_str": "錯誤",
                    "location": "API錯誤",
                    "action": error_action_msg_api,
                    "thought": str(e)[:100], "dialogue": ""
                }]
            if purpose == "interaction_dialogue":
                return {
                    "error": f"API呼叫失敗: {str(e)[:100]}",
                    "agent1_dialogue": "（API呼叫錯誤）",
                    "agent2_dialogue": "（API呼叫錯誤）"
                }
            return f"（Gemini API 呼叫錯誤 ({actual_model_name}): {str(e)[:100]}）"

    def generate_daily_plan(self, current_date_str):
        last_reflection = "昨日無特別反思。"
        if self.memory_stream:
            recent_memories = [
                m["description"]
                for m in list(
                    self.memory_stream
                )[-config.RECENT_MEMORIES_TO_RETURN:]
                if m["type"] != "action_taken"
                and "生成了新的日程計劃" not in m["description"]]
            if recent_memories:
                last_reflection = "最近的觀察和想法：" + "；".join(recent_memories)

        prompt = config.DAILY_PLAN_PROMPT_TEMPLATE.format(
            agent_name=self.name, persona_summary=self.persona_summary,
            current_date_str=current_date_str, last_reflection=last_reflection,
            locations_list_str=", ".join(config.AVAILABLE_LOCATIONS)
        )
        self.daily_schedule = self._get_llm_response(
            prompt, purpose="daily_plan")
        self.current_schedule_index = 0

        if (
            self.agent_id in config.AGENTS_TO_MEET_IDS
            and isinstance(self.daily_schedule, list)
            and not (
                len(self.daily_schedule) == 1
                and self.daily_schedule[0].get("action", "").startswith("錯誤")
            )
        ):
            meeting_event_found_and_updated = False
            for event_idx, event in enumerate(self.daily_schedule):
                if (
                    isinstance(event, dict)
                    and event.get("time_str") == config.MEETING_TIME
                ):
                    self.original_action_at_meeting_time = event.get(
                        "action", "未知原計劃")
                    event["location"] = config.MEETING_LOCATION
                    event["action"] = f"在 {config.MEETING_LOCATION} 準備與人會面"
                    event["thought"] = (
                        f"（約好在 {config.MEETING_LOCATION} "
                        "見面，不知道是誰。）"
                    )
                    event["dialogue"] = ""
                    meeting_event_found_and_updated = True
                    break
            if not meeting_event_found_and_updated:
                self.original_action_at_meeting_time = "未知原計劃（事件被插入）"
                new_meeting_event = {
                    "time_str": config.MEETING_TIME,
                    "location": config.MEETING_LOCATION,
                    "action": f"在 {config.MEETING_LOCATION} 準備與人會面",
                    "thought": f"（應該是約在這個時候在 {config.MEETING_LOCATION} 見面。）",
                    "dialogue": ""
                }
                inserted = False
                for i, existing_event in enumerate(self.daily_schedule):
                    if self._compare_time_strings(
                        config.MEETING_TIME,
                        existing_event.get("time_str", "")
                    ) < 0:
                        self.daily_schedule.insert(i, new_meeting_event)
                        inserted = True
                        break
                if not inserted:
                    self.daily_schedule.append(new_meeting_event)

        if (
            isinstance(self.daily_schedule, list)
            and self.daily_schedule
            and not (
                len(self.daily_schedule) == 1
                and self.daily_schedule[0].get("action", "").startswith("錯誤")
            )
        ):
            self.add_memory(current_date_str, "system_event",
                            f"系統為 {self.name} 生成了新的日程計劃。", 2)
        else:
            # print(f"未能為 {self.name} 正確生成日程。收到的內容: {self.daily_schedule}") # 減少控制台輸出
            if (
                not isinstance(self.daily_schedule, list)
                or not self.daily_schedule
            ):
                self.daily_schedule = [{
                    "time_str": "錯誤",
                    "location": "未知",
                    "action": "日程生成失敗",
                    "thought": "請檢查LLM回應或Prompt。",
                    "dialogue": ""
                }]

    def update_action_for_time(self, game_time_str):
        self.current_dialogue = ""
        if (
            not self.daily_schedule
            or not isinstance(self.daily_schedule, list)
            or (
                isinstance(self.daily_schedule[0], dict)
                and self.daily_schedule[0].get("action", "").startswith("錯誤")
            )
        ):
            self.current_action = "今日事已畢或日程生成失敗"
            self.current_thought = "（等待新的一天或檢查後端日誌...）"
            if self.daily_schedule and isinstance(self.daily_schedule[0], dict):
                self.current_location = self.daily_schedule[0].get(
                    "location", self.current_location)
            else:
                self.current_location = (
                    self.current_location
                    or config.AVAILABLE_LOCATIONS[0]
                )
            return

        latest_applicable_event = None
        next_event_index_to_set = 0
        for i, event in enumerate(self.daily_schedule):
            if (
                not isinstance(event, dict)
                or not all(k in event
                           for k in ["time_str", "location", "action"])
            ):
                continue
            event_time_from_llm = event["time_str"]
            comparison = self._compare_time_strings(
                event_time_from_llm, game_time_str)
            if comparison <= 0:
                latest_applicable_event = event
                next_event_index_to_set = i + 1
            else:
                break
        self.current_schedule_index = next_event_index_to_set

        if latest_applicable_event:
            self.current_location = latest_applicable_event["location"]
            self.current_action = latest_applicable_event["action"]
            self.current_thought = latest_applicable_event.get(
                "thought", "（執行中...）")
            scheduled_dialogue = latest_applicable_event.get("dialogue", "")
            is_meeting_time_and_place = (
                game_time_str == config.MEETING_TIME
                and self.agent_id in config.AGENTS_TO_MEET_IDS
                and self.current_location == config.MEETING_LOCATION
            )
            if scheduled_dialogue and not is_meeting_time_and_place:
                self.current_dialogue = scheduled_dialogue
            action_description = (
                f"在 {self.current_location} "
                f"執行了 '{self.current_action}'。"
            )
            if self.current_dialogue:
                action_description += f" 並說了：'{self.current_dialogue}'"
            is_meeting_interaction_action = (
                "與" in self.current_action
                and "交談" in self.current_action
                and is_meeting_time_and_place
            )
            if not is_meeting_interaction_action:
                self.add_memory(game_time_str, "action_taken",
                                action_description, 5)
            if (
                self._compare_time_strings(
                    latest_applicable_event["time_str"],
                    game_time_str
                ) < 0
                and self.current_schedule_index < len(self.daily_schedule)
            ):
                next_event_in_schedule = (
                    self.daily_schedule[self.current_schedule_index]
                )
                if isinstance(next_event_in_schedule, dict) and\
                        "location" in next_event_in_schedule:
                    loc = next_event_in_schedule["location"]
                    if self.current_location != loc:
                        self.current_action = f"前往 {loc}"
                        self.current_thought = (
                            f"（正從 {self.current_location} 趕往 {loc}。）"
                        )
                        self.current_dialogue = ""
                        self.add_memory(
                            game_time_str,
                            "movement_decision",
                            f"決定從 {self.current_location} 前往 "
                            f"{next_event_in_schedule['location']}。",
                            4
                        )
        elif (
            self.daily_schedule
            and isinstance(self.daily_schedule[0], dict)
            and "location" in self.daily_schedule[0]
        ):
            self.current_action = "等待日程開始"
            self.current_thought = "（一日之計在於晨。）"
            self.current_dialogue = ""
            self.current_location = self.daily_schedule[0]["location"]
            self.current_schedule_index = 0
        else:
            self.current_action = "無所事事"
            self.current_thought = "（不知今日該做些什麼。）"
            self.current_location = self.current_location or\
                config.AVAILABLE_LOCATIONS[0]

# --- 全域函式 ---


def generate_meeting_dialogue(
    agent1: Agent,
    agent2: Agent,
    location: str,
    time_str: str
):
    
    speakers = [agent1, agent2]
    random.shuffle(speakers)
    first_speaker, second_speaker = speakers[0], speakers[1]
    agent1_mem = "; ".join(
        [
            m['description'] for m in list(agent1.memory_stream)[-3:]
            if m['type'] in ["observation_เห็น_คนอื่น",
                             "action_taken", "dialogue_heard"]]
    )
    agent2_mem = "; ".join(
        [
            m['description'] for m in list(agent2.memory_stream)[-3:]
            if m['type'] in ["observation_เห็น_คนอื่น",
                             "action_taken", "dialogue_heard"]]
    )
    prompt = config.MEETING_DIALOGUE_PROMPT_TEMPLATE.format(
        location=location,
        time_str=time_str,
        first_speaker_name=first_speaker.name,
        first_speaker_persona=first_speaker.persona_summary,
        first_speaker_original_action=(
            first_speaker.original_action_at_meeting_time
            or "不詳"
        ),
        first_speaker_recent_memories=agent1_mem or "無特別記憶",
        first_speaker_agent_id=first_speaker.agent_id,
        second_speaker_name=second_speaker.name,
        second_speaker_persona=second_speaker.persona_summary,
        second_speaker_original_action=(
            second_speaker.original_action_at_meeting_time
            or "不詳"
        ),
        second_speaker_recent_memories=agent2_mem or "無特別記憶",
        second_speaker_agent_id=second_speaker.agent_id
    )
    response_data = agent1._get_llm_response(
        prompt, purpose="interaction_dialogue")
    if isinstance(response_data, dict) and "error" not in response_data:
        dialogue_fs = response_data.get(
            f"{first_speaker.agent_id}_dialogue", "")
        dialogue_ss = response_data.get(
            f"{second_speaker.agent_id}_dialogue", "")
        final_dialogues = {
            "agent1_dialogue": dialogue_fs
            if first_speaker.agent_id == agent1.agent_id else dialogue_ss,
            "agent2_dialogue": dialogue_ss
            if first_speaker.agent_id == agent1.agent_id else dialogue_fs
        }
        return final_dialogues
    else:
        error_msg = response_data.get("error", "未知的對話生成錯誤") if isinstance(
            response_data, dict) else "LLM回應格式錯誤或非字典"
        # print(f"DEBUG_INTERACTION ERROR: 為 {agent1.name} 和 {agent2.name} 生成會面對話失敗: {error_msg}") # 減少控制台輸出
        return {
            "error": error_msg,
            "agent1_dialogue": "（...）",
            "agent2_dialogue": "（...）"
        }

# --- 新增：DeepSeek 詩歌生成函式 ---


def get_deepseek_poem():
    """使用 DeepSeek API 生成一首詩"""
    if not deepseek_api_key:
        return "DeepSeek API 金鑰未設定，無法生成詩詞。"
    if not config.DEEPSEEK_API_URL or not config.DEEPSEEK_MODEL_NAME:
        return "DeepSeek API URL 或模型名稱未在 config.py 中設定。"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {deepseek_api_key}"
    }
    # 使用 config 中的詩歌主題和 Prompt 模板
    prompt_content = config.POEM_GENERATION_PROMPT_TEMPLATE.format(
        theme=config.DEEPSEEK_POEM_PROMPT_THEME)

    payload = {
        "model": config.DEEPSEEK_MODEL_NAME,
        "messages": [{"role": "user", "content": prompt_content}],
        "stream": False,  # 我們需要一次性回應
        # 可以加入 config.DEEPSEEK_GENERATION_CONFIG 中的其他參數
        "temperature": config.DEEPSEEK_GENERATION_CONFIG.get("temperature", 0.7),
        "max_tokens": config.DEEPSEEK_GENERATION_CONFIG.get("max_tokens", 200)
    }
    # print(f"DEBUG: DeepSeek Payload: {json.dumps(payload, ensure_ascii=False)}") # 偵錯時開啟

    try:
        response = requests.post(
            # 設定超時
            config.DEEPSEEK_API_URL, headers=headers, json=payload, timeout=20
        )
        response.raise_for_status()  # 如果 HTTP 請求返回了不成功的狀態碼，則拋出 HTTPError 異常

        response_data = response.json()
        # print(f"DEBUG: DeepSeek Response Data: {json.dumps(response_data, ensure_ascii=False)}") # 偵錯時開啟

        if response_data and "choices" in response_data and len(
            response_data["choices"]
        ) > 0:
            poem_content = response_data["choices"][0].get(
                "message", {}).get("content", "")
            if poem_content:
                return poem_content.strip()
            else:
                return "未能從 DeepSeek API 獲取詩詞內容。"
        else:
            return f"DeepSeek API 回應格式不符預期: {str(response_data)[:200]}"

    except requests.exceptions.RequestException as e:
        print(f"呼叫 DeepSeek API 時發生網路錯誤: {e}")
        return f"呼叫詩歌 API 時發生網路錯誤: {e}"
    except json.JSONDecodeError as e:
        print(f"解析 DeepSeek API 回應 JSON 失敗: {e}")
        return f"解析詩歌 API 回應失敗: {e}"
    except Exception as e:
        print(f"呼叫 DeepSeek API 時發生未知錯誤: {e}")
        traceback.print_exc()
        return f"生成詩詞時發生未知錯誤: {e}"


# --- Flask App 設定 ---
app = Flask(__name__)
CORS(app)

agents_data = {}
if (
    hasattr(config, 'AGENTS_INITIAL_SETUP')
    and isinstance(config.AGENTS_INITIAL_SETUP, dict)
):
    for agent_id, setup in config.AGENTS_INITIAL_SETUP.items():
        agents_data[agent_id] = Agent(
            agent_id=setup["agent_id"], name=setup["name"],
            persona_summary=setup["persona_summary"],
            initial_location=setup.get(
                "initial_location", config.AVAILABLE_LOCATIONS[0])
        )
    # print(f"已從 config 初始化 {len(agents_data)} 位代理人。") # 減少控制台輸出
else:
    print("錯誤：config.py 中未找到 AGENTS_INITIAL_SETUP 或格式不正確。無法初始化代理人。")


@app.route('/')
def home():
    return "古代城市 AI 代理模擬 - 後端 API (V1.8 - DeepSeek 詩歌)"

# --- 新增：詩歌 API 端點 ---


@app.route('/api/poem', methods=['GET'])
def poem_api():
    poem = get_deepseek_poem()
    return jsonify({"poem": poem})


@app.route('/api/game_state', methods=['GET'])
def get_game_state():
    current_game_time_str = flask_request.args.get(
        'time', f"{config.SHICHEN[3]}{config.TIME_UNITS[0]}")
    response_agents = {}
    if not agents_data:
        return jsonify({
            "error": "代理人未初始化，請檢查後端 config.py 設定。",
            "current_game_time": current_game_time_str,
            "agents": {}
        }), 500

    for agent_id, agent_obj in agents_data.items():
        if not gemini_api_key:
            agent_obj.current_action = "API金鑰未設定"
            agent_obj.current_thought = "（無法連接至大型語言模型。）"
        else:
            is_new_day = (current_game_time_str ==
                          f"{config.SHICHEN[3]}{config.TIME_UNITS[0]}")
            is_schedule_invalid = (
                not agent_obj.daily_schedule
                or (
                    isinstance(agent_obj.daily_schedule, list)
                    and len(agent_obj.daily_schedule) > 0
                    and isinstance(agent_obj.daily_schedule[0], dict)
                    and agent_obj.daily_schedule[0].get("action", "")
                    .startswith("錯誤")
                )
            )
            if is_new_day or is_schedule_invalid:
                today_game_date = datetime.date.today().strftime("%Y年%m月%d日")
                agent_obj.generate_daily_plan(
                    f"{today_game_date} ({current_game_time_str})")
        agent_obj.update_action_for_time(current_game_time_str)

    if current_game_time_str == config.MEETING_TIME:
        agents_at_meeting_spot = [
            agent for agent_id, agent in agents_data.items()
            if (
                agent_id in config.AGENTS_TO_MEET_IDS
                and agent.current_location == config.MEETING_LOCATION
            )
        ]
        if len(agents_at_meeting_spot) == len(config.AGENTS_TO_MEET_IDS) and\
                len(config.AGENTS_TO_MEET_IDS) >= 2:
            agent1_obj = agents_data.get(config.AGENTS_TO_MEET_IDS[0])
            agent2_obj = agents_data.get(config.AGENTS_TO_MEET_IDS[1])
            if (
                agent1_obj
                and agent2_obj
                and agent1_obj in agents_at_meeting_spot
                and agent2_obj in agents_at_meeting_spot
            ):
                interaction_result = generate_meeting_dialogue(
                    agent1_obj,
                    agent2_obj,
                    config.MEETING_LOCATION,
                    current_game_time_str
                )
                dialogue1 = interaction_result.get("agent1_dialogue", "（...）")
                dialogue2 = interaction_result.get("agent2_dialogue", "（...）")
                agent1_obj.current_dialogue = dialogue1
                agent1_obj.current_action = (
                    f"與 {agent2_obj.name} 在{config.MEETING_LOCATION}交談"
                )
                agent2_obj.current_dialogue = dialogue2
                agent2_obj.current_action = (
                    f"與 {agent1_obj.name} 在{config.MEETING_LOCATION}交談"
                )
                if dialogue1 and dialogue1 != "（...）":
                    agent1_obj.add_memory(
                        current_game_time_str,
                        "dialogue_spoken",
                        f"對 {agent2_obj.name} 說：'{dialogue1}'",
                        7,
                        [agent2_obj.agent_id]
                    )
                    agent2_obj.add_memory(
                        current_game_time_str,
                        "dialogue_heard",
                        f"聽到 {agent1_obj.name} 說：'{dialogue1}'",
                        6,
                        [agent1_obj.agent_id]
                    )
                if dialogue2 and dialogue2 != "（...）":
                    agent2_obj.add_memory(
                        current_game_time_str,
                        "dialogue_spoken",
                        f"對 {agent1_obj.name} 說：'{dialogue2}'",
                        7,
                        [agent1_obj.agent_id]
                    )
                    agent1_obj.add_memory(
                        current_game_time_str,
                        "dialogue_heard",
                        f"聽到 {agent2_obj.name} 說：'{dialogue2}'",
                        6,
                        [agent2_obj.agent_id]
                    )
                if "error" in interaction_result:
                    print(
                        f"DEBUG_API ERROR: 為 {agent1_obj.name} 和 "
                        f"{agent2_obj.name} 生成互動對話時出現問題: "
                        f"{interaction_result['error']}"
                    )

    for agent_id, agent_obj in agents_data.items():
        if gemini_api_key:
            agent_obj.observe_environment(current_game_time_str, agents_data)

    for agent_id, agent_obj in agents_data.items():
        current_schedule = agent_obj.daily_schedule
        if not isinstance(current_schedule, list) or not current_schedule:
            current_schedule = [{
                "time_str": "錯誤",
                "location": "未知",
                "action": "日程無效或為空",
                "thought": "請檢查LLM日程生成",
                "dialogue": ""
            }]
        response_agents[agent_id] = {
            "name": agent_obj.name,
            "location": agent_obj.current_location,
            "action": agent_obj.current_action,
            "thought": agent_obj.current_thought,
            "dialogue": agent_obj.current_dialogue,
            "schedule_today": current_schedule,
            "recent_memories": list(agent_obj.memory_stream)[
                -config.RECENT_MEMORIES_TO_RETURN:
            ]
        }
    return jsonify({
        "current_game_time": current_game_time_str,
        "agents": response_agents
    })


if __name__ == '__main__':
    print(
        f"後端 API 正在啟動於 http://localhost:{config.FLASK_PORT} "
        f"(除錯模式: {config.FLASK_DEBUG_MODE})"
    )
    app.run(debug=config.FLASK_DEBUG_MODE, port=config.FLASK_PORT)
