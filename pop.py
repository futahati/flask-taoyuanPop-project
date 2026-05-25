import os
import pymysql
import sqlite3
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# 自動尋找專案根目錄下的 .env 檔案並載入環境變數
load_dotenv()


# 建立雲端連線
def open_db():
    # host=os.getenv("HOST") ← os.getenv()本地端dotenv使用
    try:
        conn = pymysql.connect(
            host=os.environ.get("HOST"),
            port=int(os.environ.get("PORT")),
            user=os.environ.get("NAME"),
            password=os.environ.get("PASSWORD"),
            database=os.environ.get("DATABASE"),
            ssl={"ca": None},
        )

        cursor = conn.cursor()

        return conn, cursor

    except Exception as e:
        print(e)

    return None, None


# 動態建立資料表 (自動處理 100 多個年齡欄位)
def create_table(df, table_name):
    global conn, cursor
    try:
        # 動態組合欄位定義
        columns_def = []

        # 基礎欄位
        columns_def.append("date DATE")
        columns_def.append("region VARCHAR(20)")
        columns_def.append("gender VARCHAR(5)")

        # 動態加入 0aged ~ 100aged 的欄位
        for col in df.columns:
            if "aged" in col:
                columns_def.append(
                    f"`{col}` INT"
                )  # 使用反引號包住欄位名稱，避免特殊字元衝突

        # 組合完整的 CREATE TABLE 指令
        # 這裡加上了 (date, region, gender) 的複合主鍵，防止重複寫入
        sqlstr = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            {", ".join(columns_def)},
            PRIMARY KEY (date, region, gender)
        )
        """

        cursor.execute(sqlstr)
        conn.commit()
        print(f"🎉 資料表 {table_name} 檢查/建立成功。")
    except Exception as e:
        print(f"建立資料表失敗: {e}")


# 動態批量寫入 TiDB
def insert_data(df, table_name):
    global conn, cursor
    try:
        # 動態產生欄位名稱 (例如: date, region, gender, `0aged`, `1aged`...)
        cols = ", ".join([f"`{c}`" for c in df.columns])

        # 動態產生對應數量的 %s 佔位符
        placeholders = ", ".join(["%s"] * len(df.columns))

        # 使用 INSERT IGNORE 避免重複主鍵報錯
        sqlstr = f"INSERT IGNORE INTO {table_name} ({cols}) VALUES ({placeholders})"

        # 轉換 Pandas DataFrame 為 2D List (tuple) 丟給 executemany
        # tuple(x) 會把每一列換成 Python 的標準資料型態，TiDB 才能精準讀取
        data_tuples = [tuple(x) for x in df.to_numpy()]

        print(f"🚀 正在發送 {len(data_tuples)} 筆資料到 TiDB Cloud...")
        cursor.executemany(sqlstr, data_tuples)
        conn.commit()

        if cursor.rowcount == 0:
            print("目前無更新資料（或資料已存在）。")
        else:
            print(f"成功寫入/更新 {cursor.rowcount} 筆資料項目。")

    except Exception as e:
        print(f"寫入資料失敗: {e}")


# ==================== 主程式執行流程 Upload to the cloud（上傳到雲端） ====================
print("==" * 30)
start_time = datetime.now()
print(f"運行開始時間：{start_time}")

# 從 taoyuanage.db 資料庫取出資料後，上傳Tidb雲端資料庫儲存
# 建立 SQLite 連線（或連到現有資料庫）
conn = sqlite3.connect("taoyuanage.db")

# pd.read_sql() 的第一個參數必須是『SQL 查詢語句』，第二個參數必須是 conn ←開啟連接資料庫
datas = pd.read_sql("SELECT * FROM dfmerge", conn)

# 關閉連線
conn.close()

df = pd.DataFrame(datas)

# 目標表名為 "dfmerge"
target_table = "dfmerge"

# 【提醒】請確保 df["date"] 已經轉換成標準 date 物件：
# df["date"] = pd.to_datetime(df["date"]).dt.date

conn, cursor = open_db()

if conn is not None:
    # 傳入 df 與 表名，自動幫你蓋好 100 多個欄位的表格
    create_table(df, target_table)

    # 直接把整個 df 倒進去
    insert_data(df, target_table)

    conn.close()
else:
    print("❌ 雲端資料庫開啟失敗，請檢查環境變數 (HOST, PORT, PASSWORD 等) 是否正確。")

print("==" * 30)
end_time = datetime.now()
print(f"運行結束時間：{end_time}")
print(f"總執行時間：{end_time - start_time}")
print("==" * 30)
