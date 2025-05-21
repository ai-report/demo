from code import interact
import re
from storage import retrieve_data, add_data
from flask import Flask, jsonify
import threading
from schedule import agents
import time
import uvicorn


def background_job():
    """
    這個函式只被呼叫一次，然後自己在背景一直 loop。
    你可以在裡面放 60 秒一次、或任意間隔的工作邏輯。
    """
    # treads = []
    # data = {
    #     'a': '這是 a 的結果',
    #     'b': '這是 b 的結果',
    #     'c': [1, 2, 'c'],
    #     'd': {'a': 1, 'b': 'd'},
    # }
    
    # def gen_data(id, content):
    #     if id == 'a':
    #         print("正在等待a")
    #         time.sleep(1)
    #         print("正在寫入a")
    #     elif id == 'b':
    #         print("正在等待b")
    #         time.sleep(5)
    #         print("正在寫入b")
    #     elif id == 'c':
    #         print("正在等待c")
    #         time.sleep(10)
    #         print("正在寫入c")
    #     elif id == 'd':
    #         print("正在等待d")
    #         time.sleep(6)
    #         print("正在寫入d")
    #     add_data(id, content)
    #     return
    # for key in data:
    #     value = data[key]
    #     t = threading.Thread(target=gen_data, args=(key, value))
    #     treads.append(t)
    # for t in treads:
    #     t.start()
    peoples_name = {'li': '李白',
                    'teacher_li': '李老師',
                    'li_qing_zhao': '李清照',
                    'zhuang_zi': '莊子'}
    
    def gen_plan(name):
        print(f"{peoples_name[name]}計畫啟動")
        agents[name].plan_hour()
        agents[name].plan_15_minute(
            retrieve_data(f'sch_{peoples_name[name]}_hour')
        )
        agents[name].split_plan_to_each_15_minute()
        print(f"{peoples_name[name]}計畫結束")
        
    threads = []
    for name in peoples_name:
        t = threading.Thread(target=gen_plan, args=(name,))
        threads.append(t)
    for t in threads:
        t.start()

    
def start_background_thread():
    t = threading.Thread(target=background_job, daemon=True)
    t.start()
    print("[主程式] 背景工作已啟動")


def run_api():
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
    
    
def interactive():
    while True:
        a = input("請輸入id")
        print(retrieve_data(a, 2))


if __name__ == "__main__":
    # 1. 先啟動背景工作（只呼叫一次）
    start_background_thread()

    # 2. 再啟動 Flask（多執行緒模式）
    #    threaded=True 可讓每個 HTTP 請求都跑在自己的 thread 裡
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=False)
    # interactive()
    # app.run(host="0.0.0.0", port=5000, threaded=True)
