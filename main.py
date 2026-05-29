from flask import Flask, render_template, jsonify
import pandas as pd
from datetime import datetime
import database

# 取得本地端的伺服器__name__
app = Flask(__name__)


# 12個月數據，依區域分組
@app.route("/api/data12m/<region>")
def api_data12m_by_region(region):
    rows = database.get_12m_by_region()["rows"]
    rows = [entry for entry in rows if entry[1] == region]
    rows = sorted(rows, key=lambda x: x[0])

    return jsonify(rows)


# 區域名單
@app.route("/api/regions")
def api_regions():
    regions = database.get_region()["rows"]
    regions = [r[0] for r in regions]

    return jsonify(regions)


# 幼年、青壯、老年各區分布百比
@app.route("/api/data1m/age-structure")
def get_latest_age_structure_pie_data():

    result = database.get_latest_age_structure_pie_data()

    return jsonify(result)


# 最新1個月數據，依性別分組
@app.route("/api/data1m/gender")
def get_data_by_gender_group():

    result = database.get_data_by_gender_group()

    return jsonify(result)


# 最新1個月數據，依區域分組
@app.route("/api/data1m/region")
def get_data_by_region_group():

    result = database.get_data_by_region_group()

    return jsonify(result)


@app.route("/")
def index():
    # 一個月數據
    result = database.get_latest_data()

    # 區域名單
    regions = database.get_region()["rows"]
    regions = [r[0] for r in regions]

    # 近一年日期區間
    raw_data = database.get_12m_by_region()["rows"]
    # 轉成 Pandas DataFrame，並設定欄位名稱
    df = pd.DataFrame(raw_data, columns=["date", "region", "monthly_total"])
    # 樞紐轉置 (Pivot) index=橫列關鍵字, columns=直欄關鍵字, values=格子裡要填的值
    pivot_df = df.pivot(index="region", columns="date", values="monthly_total")
    # 排序優化：讓日期從舊到新由左至右排列 (選填)
    pivot_df = pivot_df.reindex(sorted(pivot_df.columns), axis=1)
    # 產生直欄表頭：第一格是「區域名」，後面接所有排序好的日期
    pivot_df.columns = pivot_df.columns.map(
        lambda x: str(x)[:7]
    )  # ✨ 把欄位名稱批量換成 2025-04 格式
    cols = ["區域名"] + list(pivot_df.columns)
    # 產生橫列資料：每一列的第一格是區域名稱，後面接該區在各日期的數值
    rows = []
    for region_name, row_data in pivot_df.iterrows():
        # row_data.tolist() 會拿到該區所有日期的數值陣列，前面加上區域名稱
        current_row = [region_name] + row_data.tolist()
        rows.append(current_row)

    print(pivot_df.columns)

    # 取出所有日期
    dates = [row[0] for row in raw_data]
    # 找最新和最舊
    latest_date = max(dates)
    oldest_date = min(dates)

    return render_template(
        "index.html",
        result=result,
        regions=regions,
        cols=cols,
        rows=rows,
        latest_date=latest_date,
        oldest_date=oldest_date,
    )


if __name__ == "__main__":
    # pass
    # 最後一行，要執行
    app.run(debug=True)
