# ai_report

## 環境

1. language
python==3.12.4
2. python
見 [requirements.txt](/requirements.txt)

## 專案結構

- `/AI_report`為主要程式
  - `/AI_report/backend`為後端程式
  - `/AI_report/frontend`為前端程式
    - `/AI_report/frontend/assets`放前端需要的所有圖片、影片、媒體
    - `/AI_report/frontend/css`為前端css
    - `/AI_report/frontend/js`為前端JavaScript
- `/docs`為技術文件
- `/requirmets.txt`為python相依套件
- `/image`放前端以外的所有圖片
- `/.env`設置環境變數，包含api key

## API KEY

範例：
```gemini=***************************************```

各LLM api key設定名稱定義：

1. gemini: `gemini`
2. deepseek: `deepseek`

## how to use

1. run `AI_report\backend\main.py`
2. open `AI_report\frontend\ancient_city_frontend.html`
