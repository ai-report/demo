from llm import get_llm_response


def check_special_events(event, name):

    # 使用與 backend_app.py 中相同的邏輯，但正確設置 event 變量
    prompt = f"""請爲我判斷以下事件是否符合特殊事件的條件
        判斷事件：{name}:{event}
        特殊事件條件：1）李白：晚上李白準備睡覺時
                    2）莊子：莊子到河邊時
                    3）李清照：李清照在自家庭院中思考時
                    4）李昇暾：李昇暾作詩時
        以上條件任只要滿足其中一條即判斷其為特殊事件
        若是特殊事件，回應"True"，否則則回應"False"，你的回復必須嚴格遵照規則
        """

    # 調用 LLM API 獲取結果
    GEMINI_MODEL_NAME = "gemini-1.5-flash-latest"
    result = get_llm_response(
        prompt, provider='gemini', model_name=GEMINI_MODEL_NAME)

    # 處理結果字符串，確保返回真正的布爾值
    is_special = result.strip().lower() == "true"
    return is_special
