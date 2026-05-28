from flask import Flask, render_template, jsonify
import pandas as pd
from datetime import datetime
import database

# 取得本地端的伺服器__name__
app = Flask(__name__)


@app.route("/api/data12m/<region>")
def api_data12m_by_region(region):
    rows = database.get_12m_by_region()["rows"]
    region_data = [entry for entry in rows if entry[1] == region]
    region_sorted = sorted(region_data, key=lambda x: x[0])

    return jsonify(region_sorted)


@app.route("/api/regions")
def api_regions():
    regions = database.get_region()["rows"]
    regions = [r[0] for r in regions]

    return jsonify(regions)


@app.route("/")
def index():
    # 一個月數據
    result = database.get_latest_data()

    # 區域資料
    regions = database.get_region()["rows"]
    regions = [r[0] for r in regions]

    # 近一年日期區間
    rows = database.get_12m_by_region()["rows"]
    # 取出所有日期
    dates = [row[0] for row in rows]
    # 找最新和最舊
    latest_date = max(dates)
    oldest_date = min(dates)

    return render_template(
        "index.html",
        result=result,
        regions=regions,
        latest_date=latest_date,
        oldest_date=oldest_date,
    )


if __name__ == "__main__":
    # pass
    # 最後一行，要執行
    app.run(debug=True)
