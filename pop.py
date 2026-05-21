import sqlite3
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.types import String, Integer, Date  # 🔥 完美的 Date 型態回歸！

# 1. 連線設定
sqlite_conn = sqlite3.connect("your_project.db")
tidb_uri = "mysql+pymysql://root:your_password@127.0.0.1:4000/taoyuan_pop"
tidb_engine = create_engine(tidb_uri)

# 處理兩張表
target_tables = ["m_df", "f_df"]

for table_name in target_tables:
    # 2. 讀取資料表
    df = pd.read_sql(f"SELECT * FROM {table_name}", sqlite_conn)

    # 🔥 【核心追加】因為你的 date 是 '2017-01-31'，將它轉換為標準 datetime 物件
    # 這樣才能跟 SQLAlchemy 的 Date() 型態完美對接不噴錯
    df["date"] = pd.to_datetime(df["date"]).dt.date

    # 3. 動態精準定義 104 個欄位的資料型態
    tidb_data_types = {
        "date": Date(),  # 儲存為資料庫標準 DATE 格式 (YYYY-MM-DD)
        "region": String(20),  # 區名 (如: 桃園區、中壢區)
        "gender": String(5),  # 性別 (男/女)
    }

    # 利用迴圈，把 0aged ~ 100aged 這 101 個年齡欄位，全部綁定為標準 Integer
    for col in df.columns:
        if "aged" in col:
            tidb_data_types[col] = Integer()

    # 4. 安全、高效能地寫入 TiDB
    print(f"🚀 正在精準轉移 {table_name} 到 TiDB (包含日期格式優化)...")
    df.to_sql(
        name=table_name,
        con=tidb_engine,
        if_exists="replace",
        index=False,
        dtype=tidb_data_types,
    )
    print(f"🎉 {table_name} 搬移成功！欄位結構與型態達到最高級別優化！\n")

# 關閉連線
sqlite_conn.close()
print("🏆 恭喜！桃園人口資料庫已完美在 TiDB 安家落戶！")
