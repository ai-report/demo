import threading
import time

# 全域快取與條件變數
_cache = {}
_cond = threading.Condition()


def add_data(key, data):
    """
    寫入資料並通知所有在等 key 的執行緒。
    """
    with _cond:
        _cache[key] = data
        _cond.notify_all()


def retrieve_data(key, timeout=None):
    """
    取出指定 key 的資料：
      - 如果已經在 _cache 裡，立即回傳。
      - 否則就阻塞等到 add_data 通知、或 timeout。
    """
    with _cond:
        # 等到 key 出現或 timeout
        if key not in _cache:
            _cond.wait_for(lambda: key in _cache, timeout=timeout)
        return _cache.get(key)


# def gen_data(id, content):
#     if id == 'a':
#         time.sleep(1)
#     elif id == 'b':
#         time.sleep(2)
#     elif id == 'c':
#         time.sleep(3)
#     elif id == 'd':
#         time.sleep(4)
#     add_data(id, content)
#     return


# treads = []

# data = {
#     'a': '這是 a 的結果',
#     'b': '這是 b 的結果',
#     'c': [1, 2, 'c'],
#     'd': {'a': 1, 'b': 'd'},
# }
# for key in data:
#     value = data[key]
#     t = threading.Thread(target=gen_data, args=(key, value))
#     treads.append(t)
    
# for t in treads:
#     t.start()

# # time.sleep(1)


# def output_data(id):
#     content = retrieve_data(id)
#     return content


# # 程式其他地方要用時，就只要這樣：
# print(output_data('a'))   # → "這是 func1 的結果"
# print(output_data('d'))
# print(output_data('c'))   # → [1, 2, 3]
