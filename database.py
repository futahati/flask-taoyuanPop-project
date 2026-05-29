import requests, io, pymysql, urllib3, os
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# 自動尋找專案根目錄下的 .env 檔案並載入環境變數
load_dotenv()


# 人口結構：幼年、青壯、老年，各區在人口結構的佔比
def get_latest_age_structure_pie_data():
    conn, cursor = open_db()

    result = {"success": True, "message": None, "columns": None, "rows": None}

    if not conn:
        result["success"] = False
        result["message"] = "資料庫開啟失敗！"
        return result

    # 1. 根據你的定義，用 Python 動態生成三個年齡層的加總 SQL 片段
    # 幼年期: 0~14 歲
    child_cols = " + ".join([f"COALESCE({i}aged, 0)" for i in range(0, 15)])
    # 青壯年期: 15~64 歲
    adult_cols = " + ".join([f"COALESCE({i}aged, 0)" for i in range(15, 65)])
    # 老年期: 65~100 歲
    elder_cols = " + ".join([f"COALESCE({i}aged, 0)" for i in range(65, 101)])
    # 「權重百分比」：各區結構佔比的『再分配』圓餅圖
    all_cols = " + ".join([f"COALESCE({i}aged, 0)" for i in range(0, 101)])

    sql = f"""
        WITH LatestMonth AS (
            -- 步驟 1：鎖定最新的一個月份
            SELECT date 
            FROM dfmerge 
            ORDER BY date DESC 
            LIMIT 1
        ),
        RegionFirstPercentage AS (
            -- 步驟 2：第一次計算 -> 算出各區內部的幼年、青壯、老年「各自佔該區總人口的百分比」
            SELECT 
                t.region,
                SUM({child_cols}) * 100.0 / NULLIF(SUM({all_cols}), 0) AS child_rate,
                SUM({adult_cols}) * 100.0 / NULLIF(SUM({all_cols}), 0) AS adult_rate,
                SUM({elder_cols}) * 100.0 / NULLIF(SUM({all_cols}), 0) AS elder_rate
            FROM dfmerge t
            JOIN LatestMonth lm ON t.date = lm.date
            GROUP BY t.region
        ),
        RegionSecondPercentage AS (
            -- 步驟 3：第二次計算 -> 把各區的「結構比例」拿來做全桃園的圓餅圖再分配（SUM() OVER()）
            -- 這樣就能無視區域總人口大小，純粹比較「誰的結構比較年輕/年老」
            SELECT 
                region,
                ROUND(child_rate * 100.0 / NULLIF(SUM(child_rate) OVER(), 0), 2) AS `幼年期`,
                ROUND(adult_rate * 100.0 / NULLIF(SUM(adult_rate) OVER(), 0), 2) AS `青壯年期`,
                ROUND(elder_rate * 100.0 / NULLIF(SUM(elder_rate) OVER(), 0), 2) AS `老年期`
            FROM RegionFirstPercentage
        )
        -- 步驟 4：轉置結構，讓你直接用 age_group 來過濾出 3 張美麗的圓餅圖數據
        SELECT '幼年期' AS age_group, region, `幼年期` AS percentage FROM RegionSecondPercentage
        UNION ALL
        SELECT '青壯年期' AS age_group, region, `青壯年期` AS percentage FROM RegionSecondPercentage
        UNION ALL
        SELECT '老年期' AS age_group, region, `老年期` AS percentage FROM RegionSecondPercentage
        ORDER BY FIELD(age_group, '幼年期', '青壯年期', '老年期'), percentage DESC;
        """

    try:
        cursor.execute(sql)

        columns = [col[0] for col in cursor.description]

        rows = cursor.fetchall()
        result["success"] = True
        result["columns"] = columns
        result["rows"] = (
            rows  # 回傳的資料結構非常適合直接餵給 Matplotlib 或 Seaborn 畫圖
        )
        return result

    except Exception as e:
        result["success"] = False
        result["message"] = f"資料庫查詢失敗，原因：{e}"
        return result
    finally:
        conn.close()


# 取得近12個月的總人口數（依區域分組）
def get_12m_by_region():
    conn, cursor = open_db()

    result = {"success": True, "message": None, "columns": None, "rows": None}

    if not conn:
        result["success"] = False
        result["message"] = "資料庫開啟失敗！"
        return result

    # 1. 自動生成加總字串
    sql_sum_columns = " + ".join([f"COALESCE({i}aged, 0)" for i in range(101)])

    sql = f"""
    WITH MonthlySummed AS (
        -- 步驟 1：選出 date 和 gender，並計算橫向年齡加總
        SELECT 
            date,
            region, -- 👈 1. 這裡要加入 region
            {sql_sum_columns} AS total_population
        FROM dfmerge
    ),
    RankedMonths AS (
        -- 步驟 2：依據性別分組，並在各性別內依日期由新到舊排序
        SELECT 
            date,
            region, -- 👈 2. 這裡也要加入 region
            SUM(total_population) AS monthly_total,
            -- 👇 3. 關鍵！加上 PARTITION BY region，讓男女分開計算各自的「前12個月」
            ROW_NUMBER() OVER (PARTITION BY region ORDER BY date DESC) AS row_num
        FROM MonthlySummed
        GROUP BY date, region -- 👈 4. 這裡要改為依 date 和 region 共同群組
    )
    -- 步驟 3：只取男女各自最新 12 筆的月份數據
    SELECT 
        date,
        region, -- 👈 5. 最後輸出的欄位
        monthly_total
    FROM RankedMonths
    WHERE row_num <= 12
    ORDER BY region, date DESC; -- 👈 排序讓結果更容易閱讀（先排性別，再排日期）
    """

    try:
        cursor.execute(sql)

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


# 取得近12個月的總人口數（依性別分組）
def get_12m_by_gender():
    conn, cursor = open_db()

    result = {"success": True, "message": None, "columns": None, "rows": None}

    if not conn:
        result["success"] = False
        result["message"] = "資料庫開啟失敗！"
        return result

    # 1. 自動生成加總字串
    sql_sum_columns = " + ".join([f"COALESCE({i}aged, 0)" for i in range(101)])

    sql = f"""
    WITH MonthlySummed AS (
        -- 步驟 1：選出 date 和 gender，並計算橫向年齡加總
        SELECT 
            date,
            gender, -- 👈 1. 這裡要加入 gender
            {sql_sum_columns} AS total_population
        FROM dfmerge
    ),
    RankedMonths AS (
        -- 步驟 2：依據性別分組，並在各性別內依日期由新到舊排序
        SELECT 
            date,
            gender, -- 👈 2. 這裡也要加入 gender
            SUM(total_population) AS monthly_total,
            -- 👇 3. 關鍵！加上 PARTITION BY gender，讓男女分開計算各自的「前12個月」
            ROW_NUMBER() OVER (PARTITION BY gender ORDER BY date DESC) AS row_num
        FROM MonthlySummed
        GROUP BY date, gender -- 👈 4. 這裡要改為依 date 和 gender 共同群組
    )
    -- 步驟 3：只取男女各自最新 12 筆的月份數據
    SELECT 
        date,
        gender, -- 👈 5. 最後輸出的欄位
        monthly_total
    FROM RankedMonths
    WHERE row_num <= 12
    ORDER BY gender, date DESC; -- 👈 排序讓結果更容易閱讀（先排性別，再排日期）
    """

    try:
        cursor.execute(sql)

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


# 取得近12個月的總人口數
def get_12m():
    conn, cursor = open_db()

    result = {"success": True, "message": None, "columns": None, "rows": None}

    if not conn:
        result["success"] = False
        result["message"] = "資料庫開啟失敗！"
        return result

    # 1. 自動生成加總字串
    sql_sum_columns = " + ".join([f"COALESCE({i}aged, 0)" for i in range(101)])
    print(sql_sum_columns)

    sql = f"""
        WITH MonthlySummed AS (
            -- 步驟 1：先把每個月不分區域、性別的年齡加總算出來
            SELECT 
                date,
                {sql_sum_columns} AS total_population
            FROM dfmerge
        ),
        RankedMonths AS (
            -- 步驟 2：依據日期由新到舊進行排名，以此解決「缺失月自動往前遞補」的問題
            SELECT 
                date,
                SUM(total_population) AS monthly_total,
                ROW_NUMBER() OVER (ORDER BY date DESC) AS row_num
            FROM MonthlySummed
            GROUP BY date
        )
        -- 步驟 3：只取最新（排名前 12 筆）的月份數據
        SELECT 
            date,
            monthly_total
        FROM RankedMonths
        WHERE row_num <= 12
        ORDER BY date DESC;
        """

    try:
        cursor.execute(sql)

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


# 取得最新日期，並依性別分組加總
def get_data_by_gender_group():
    conn, cursor = open_db()

    result = {"success": True, "message": None, "columns": None, "rows": None}

    if not conn:
        result["success"] = False
        result["message"] = "資料庫開啟失敗！"
        return result

    # 1. 動態生成 SQL 的加總欄位字串 {i}aged (數字在前)
    # 2. 用反單引號 ` 把欄位名稱包起來，例如 `0aged`，避免數字開頭造成 SQL 語法錯誤
    sql_sum_columns = ", ".join(
        [f"SUM(COALESCE(`{i}aged`, 0)) AS `{i}aged`" for i in range(101)]
    )

    # 將動態生成的字串放入 SQL 之中
    sql = f"""
    SELECT 
        gender,
        {sql_sum_columns}
    FROM dfmerge
    WHERE date = (SELECT MAX(date) FROM dfmerge)
    GROUP BY gender;
    """

    try:
        cursor.execute(sql)

        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()

        result["success"] = True
        result["columns"] = columns
        result["rows"] = rows

        return result

    except Exception as e:
        result["success"] = False
        result["message"] = f"資料庫查詢失敗：{str(e)}"
        return result
    finally:
        cursor.close()
        conn.close()


# 取得最新日期，並依區域分組加總
def get_data_by_region_group():
    conn, cursor = open_db()

    result = {"success": True, "message": None, "columns": None, "rows": None}

    if not conn:
        result["success"] = False
        result["message"] = "資料庫開啟失敗！"
        return result

    # 1. 動態生成 SQL 的加總欄位字串 {i}aged (數字在前)
    # 2. 用反單引號 ` 把欄位名稱包起來，例如 `0aged`，避免數字開頭造成 SQL 語法錯誤
    sql_sum_columns = ", ".join(
        [f"SUM(COALESCE(`{i}aged`, 0)) AS `{i}aged`" for i in range(101)]
    )

    # 將動態生成的字串放入 SQL 之中
    sql = f"""
    SELECT 
        region,
        {sql_sum_columns}
    FROM dfmerge
    WHERE date = (SELECT MAX(date) FROM dfmerge)
    GROUP BY region;
    """

    try:
        cursor.execute(sql)

        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()

        result["success"] = True
        result["columns"] = columns
        result["rows"] = rows

        return result

    except Exception as e:
        result["success"] = False
        result["message"] = f"資料庫查詢失敗：{str(e)}"
        return result
    finally:
        cursor.close()
        conn.close()


# 取得資料庫裡 gender性別 + date最新的日期
def get_data_by_gender(gender):
    conn, cursor = open_db()

    result = {"success": True, "message": None, "columns": None, "rows": None}

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


# 取得資料庫裡 region區域 + date最新的日期
def get_data_by_region(region):
    conn, cursor = open_db()

    result = {"success": True, "message": None, "columns": None, "rows": None}

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
def get_date():
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


# 取得資料庫裡最新日期的數據
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


if __name__ == "__main__":
    # pass
    print(get_latest_data())
