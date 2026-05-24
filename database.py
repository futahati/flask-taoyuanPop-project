import requests, io, pymysql, urllib3, os
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# 自動尋找專案根目錄下的 .env 檔案並載入環境變數
load_dotenv()


# 取得資料庫裡 gender性別 + date最新的日期
def get_data_by_gender(gender):
    conn, cursor = open_db()

    result = {"success": True, "message": None, "rows": None}

    if not conn:
        result["success"] = False
        result["message"] = "資料庫開啟失敗！"
        return result

    # sql = "SELECT * FROM data LIMIT 500;"
    sql = """
    SELECT * FROM dfmerge where gender=%s and date=(SELECT max(date) FROM dfmerge);
    """

    try:
        # %s佔位符，要給參數(gender,)
        cursor.execute(sql, (gender,))

        rows = cursor.fetchall()
        result["success"] = True
        result["rows"] = rows

        return result

    except Exception as e:
        result["success"] = False
        result["message"] = f"資料庫查詢失敗，原因：{e}"

        return result
    finally:
        conn.close()


# 取得資料庫裡 region區域 + date最新的日期
def get_data_by_region(region):
    conn, cursor = open_db()

    result = {"success": True, "message": None, "rows": None}

    if not conn:
        result["success"] = False
        result["message"] = "資料庫開啟失敗！"
        return result

    # sql = "SELECT * FROM data LIMIT 500;"
    sql = """
    SELECT * FROM dfmerge where region=%s and date=(SELECT max(date) FROM dfmerge);
    """

    try:
        # %s佔位符，要給參數(region,)
        cursor.execute(sql, (region,))

        rows = cursor.fetchall()
        result["success"] = True
        result["rows"] = rows

        return result

    except Exception as e:
        result["success"] = False
        result["message"] = f"資料庫查詢失敗，原因：{e}"

        return result
    finally:
        conn.close()


# （下拉選單用）取得 gender 不重複資料
def get_gender():
    conn, cursor = open_db()
    result = {"success": True, "message": None, "rows": None}

    if not conn:
        result["success"] = False
        result["message"] = "資料庫開啟失敗！"

        return result

    # 取得唯一值：請在 SQL 語句中加入 DISTINCT 關鍵字
    sql = "select DISTINCT gender from dfmerge order by gender desc;"
    try:
        cursor.execute(sql)

        rows = cursor.fetchall()
        result["success"] = True
        result["rows"] = rows

        return result

    except Exception as e:
        result["success"] = False
        result["message"] = f"資料庫查詢失敗，原因：{e}"

        return result
    finally:
        conn.close()


# （下拉選單用）取得 region 不重複資料
def get_region():
    conn, cursor = open_db()
    result = {"success": True, "message": None, "rows": None}

    if not conn:
        result["success"] = False
        result["message"] = "資料庫開啟失敗！"

        return result

    # 取得唯一值：請在 SQL 語句中加入 DISTINCT 關鍵字
    sql = "select DISTINCT region from dfmerge order by region desc;"
    try:
        cursor.execute(sql)

        rows = cursor.fetchall()
        result["success"] = True
        result["rows"] = rows

        return result

    except Exception as e:
        result["success"] = False
        result["message"] = f"資料庫查詢失敗，原因：{e}"

        return result
    finally:
        conn.close()


# （下拉選單用）取得 date 不重複資料
def get_region():
    conn, cursor = open_db()
    result = {"success": True, "message": None, "rows": None}

    if not conn:
        result["success"] = False
        result["message"] = "資料庫開啟失敗！"

        return result

    # 取得唯一值：請在 SQL 語句中加入 DISTINCT 關鍵字
    sql = "select DISTINCT date from dfmerge order by date desc;"
    try:
        cursor.execute(sql)

        rows = cursor.fetchall()
        result["success"] = True
        result["rows"] = rows

        return result

    except Exception as e:
        result["success"] = False
        result["message"] = f"資料庫查詢失敗，原因：{e}"

        return result
    finally:
        conn.close()


# 取得資料庫裡最新的日期
def get_latest_data():
    conn, cursor = open_db()

    result = {"success": True, "message": None, "columns": None, "rows": None}

    if not conn:
        result["success"] = False
        result["message"] = "資料庫開啟失敗！"
        return result

    sql = """
    SELECT * FROM dfmerge where date=
    (select max(date) from dfmerge);
    """

    try:
        cursor.execute(sql)

        # .description取得最後一次 SQL 查詢結果的「欄位元資料」（Metadata）==>自動獲取欄位名稱
        # print(cursor.description)
        columns = [col[0] for col in cursor.description]

        rows = cursor.fetchall()
        result["success"] = True
        result["columns"] = columns
        result["rows"] = rows

        return result

    except Exception as e:
        result["success"] = False
        result["message"] = f"資料庫查詢失敗，原因：{e}"

        return result
    finally:
        conn.close()


# 建立雲端連線，使用 MySQL(PyMySQL) 語法
def open_db():
    # host=os.getenv("HOST") ← os.getenv()本地端dotenv使用
    try:
        conn = pymysql.connect(
            host=os.environ.get("HOST"),
            port=int(os.environ.get("PORT")),
            user=os.environ.get("USER"),
            password=os.environ.get("PASSWORD"),
            database=os.environ.get("NAME"),
            ssl={"ca": None},
        )

        cursor = conn.cursor()

        return conn, cursor

    except Exception as e:
        print(e)

    return None, None


if __name__ == "__main__":
    pass
