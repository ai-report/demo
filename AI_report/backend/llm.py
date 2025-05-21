from typing import Optional
from openai import OpenAI
import google.generativeai as genai
from google.api_core.exceptions import RetryError
from google.api_core import retry
import os
from config import config
from dotenv import load_dotenv

load_dotenv()

# API_KEYS = dict(lioliolio=os.getenv('gemini'))
# print(API_KEYS)


API_KEYS = {
    'gemini': os.getenv('gemini'),
    'deepseek': os.getenv('deepseek')
}


def _check_api_keys():
    """檢查 `API_KEYS` 字典中所有 API 金鑰是否均已正確設定。
        這些金鑰應該是字串類型，且不能為空字串或前後端包含空白字元。
        此函數會遍歷 `API_KEYS` 中的每個金鑰。

        Returns:
            bool:   若所有 API 金鑰均通過檢查，則返回 `True`;
                    若至少有一個 API 金鑰未正確設定，則返回 `False`。
        """
    all_keys_valid = True
    for key in API_KEYS.keys():
        if not _check_api_key(key):
            all_keys_valid = False
    return all_keys_valid


def _check_api_key(key_name):
    """檢查單個 API 金鑰是否已正確設定。
        金鑰應該是字串類型，且不能為空字串或前後端包含空白字元。

    Args:
        key_name (str): 要檢查的 API 金鑰名稱。

    Returns:
        bool: 若金鑰已正確設定，則返回 `True`；否則返回 `False`。
    """
    if key_name not in API_KEYS:
        print(f"API KEY '{key_name}' 不存在，請檢查key name。")
        return False
    
    value = API_KEYS[key_name]
    # 非字串、空字串、全空格、前後端有空白為錯誤
    if (not isinstance(value, str)) or (
            not value.strip()) or (value != value.strip()):
        print(f"API KEY '{key_name}' 未設定。其value為'{value}'")
        return False
    
    return True


# _check_api_keys()


def get_llm_response(prompt_text: str, provider: str,
                     model_name: Optional[str | None] = None) -> str:
    '''
    發送prompt到LLM並取得回應
    
    :param prompt_text: 提示詞
    :param provider: 哪家的LLM
    :param model_name: 模型名稱
    :return(str): LLM實際回應文字
    '''
    if provider == "gemini":
        return _gemini(prompt_text, model_name)
    elif provider == "deepseek":
        return _deepseek(prompt_text, model_name)
    else:
        raise ValueError(f"不支援的LLM provider: {provider}")
    

def _deepseek(prompt_text: str, model_name: Optional[str | None] = None
              ) -> str:
    # 如果沒有指定模型名稱(None)，則使用預設的模型名稱
    if model_name is None:
        model_name = 'deepseek-chat'
    
    _check_api_key('deepseek')  # 檢查API金鑰是否正確設定
    
    client = OpenAI(api_key=API_KEYS['deepseek'],
                    base_url="https://api.deepseek.com")

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            # {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": prompt_text},
        ],
        stream=False
    )
    # print(response)

    # print(response.choices[0].message.content)
    
    return str(response.choices[0].message.content)
    
    
def _gemini(prompt_text: str, model_name: Optional[str | None] = None) -> str:
    '''
    發送prompt到gemini並取得回應
    
    :param prompt_text: 提示詞
    :param provider: 哪家的LLM
    :param model_name: 模型名稱 (default: 'gemini-1.5-flash-latest')
    :return(str): LLM實際回應文字
    :param retry: 最大重試次數 (default: 0)
    '''
    # 如果沒有指定模型名稱(None)，則使用預設的模型名稱
    if model_name is None:
        model_name = 'gemini-1.5-flash-latest'
        
    _check_api_key('gemini')  # 檢查API金鑰是否正確設定

    # try:
    genai.configure(api_key=API_KEYS['gemini'])  # 設定API金鑰
    # 這個api已經被官方棄用，但沒事就先照用吧
    model = genai.GenerativeModel(
        model_name=model_name,
        safety_settings=config['gemini']['safety_settings'],
        generation_config=config['gemini']['generation_config'],
    )
    try:
        response = model.generate_content(
            # 請求超過10秒未回應開始重試並輸出訊息，加上重試最多約30秒
            prompt_text, request_options={
                "timeout": 90,
                "retry": retry.Retry(
                    initial=1,
                    maximum=10,
                    multiplier=2,
                    timeout=180,
                    on_error=lambda e: print(f"Retrying due to error: {e}"),
                )
            })
    except RetryError:  # response 回應超過timeout且retry後仍無效的錯誤類別
        print("請求超時，請稍後再試。")
        return ""
    except Exception as e:
        print(f"發生錯誤: {e}")
        return ""
    
    # 從回應中取得實際生成的文本
    generated_text = ""
    if response.candidates and hasattr(response.candidates[0], 'content') \
        and hasattr(response.candidates[0].content, 'parts') \
            and response.candidates[0].content.parts:
        generated_text = "".join(
            part.text for part in response.candidates[0].content.parts if hasattr(part, 'text'))
    elif hasattr(response, 'text'):
        generated_text = response.text
    
    return generated_text


# print(_gemini('請幫我寫一篇關於AI的報告'))
# import time


# time_trace_list = []
# for i in range(500):
#     print(i)
#     start = time.time()
#     response_text = _gemini('請幫我寫一篇關於AI的報告')
#     print(str(response_text)[:10], "len: ", len(response_text))
#     end = time.time() - start
#     time_trace_list.append(end)
#     print(f"花費時間: {end:.2f}秒")
