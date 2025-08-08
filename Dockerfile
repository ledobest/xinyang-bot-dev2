# 1. 使用一個官方、穩定的 Python 映像檔作為基礎
FROM python:3.11-slim

# 2. 在容器內建立一個叫做 /app 的工作目錄
WORKDIR /app

# 3. 先複製我們的工具清單進去
COPY requirements.txt .

# 4. 執行指令，安裝所有需要的工具
RUN pip install --no-cache-dir -r requirements.txt

# 5. 把我們資料夾裡剩下的所有東西 (app.py) 都複製進去
COPY . .

# 6. 設定最終的啟動指令
# gunicorn 會自動監聽由 Railway 提供的 $PORT 變數
CMD ["gunicorn", "app:app"]