from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from storage import retrieve_data
from storage import _cache

app = FastAPI()

origins = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    # "http://localhost:3000",
    # "https://你的正式網域.com"
]

# 2. 加入 CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,         # or ["*"] for all origins
    allow_credentials=True,
    allow_methods=["*"],           # GET, POST, PUT, DELETE…
    allow_headers=["*"],           # 所有 request headers
)

@app.get('/api/status')
def get_status(time: str = Query(None), name: str = Query(None)):
    if not time or not name:
        raise HTTPException(status_code=400, detail="缺少必要的參數 (time 或 name)")

    status = {
        "time": time,
        "name": name,
        "status": f"{name} 在 {time} 時的狀態"
    }
    print("接收到請求", "正在查詢", f"{name} 在 {time} 時的狀態")
    response = retrieve_data(
        f"sch_{name}_15_minute_{time}",
        2
    )
    print(_cache.keys())
    print(f"sch_{name}_15_minute_{time}")
    # print(_cache[f"sch_{name}_15_minute_{time}"])

    return response


@app.get('/api/check_poem')
def check_poem(time: str = Query(None), name: str = Query(None)):
    if not time or not name:
        raise HTTPException(status_code=400, detail="缺少必要的參數 (time 或 name)")
    key = f"trigger_{name}_{time}"
    response = retrieve_data(key, 2)
    
    return response
