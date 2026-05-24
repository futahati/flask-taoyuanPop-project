import io
import base64
import pandas as pd
import numpy as np
from flask import Flask, render_template_string
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import seaborn as sns
import database

# 🛠️ 1. 解決 Matplotlib 中文顯示問題（視您的作業系統選擇，這裡先用常見字體）
plt.rcParams["font.family"] = [
    "Microsoft JhengHei",
    "Arial Unicode MS",
]  # 微軟正黑體 / Mac 內建中文
plt.rcParams["axes.unicode_minus"] = False

app = Flask(__name__)

# --- 4. 年齡與顏色核心定義 ---
labor = {"幼年期": (0, 14), "青壯年期": (15, 64), "老年期": (65, 100)}


def addage(adfile):
    result = {}
    for i, (name, (start, end)) in enumerate(adfile.items()):
        age_end = end + 1 if i < len(adfile) - 1 else end
        result[name] = [start, age_end]
    return result


labor_bgage = addage(labor)
labor_bgclr = sns.color_palette("Pastel1", n_colors=len(labor_bgage)).as_hex()


# --- 5. 修改後的繪圖函式 (輸出 Base64 字串) ---
def get_chart_base64(datas, bgages, bgclrs, title_name):
    x_max_age = max(end for start, end in bgages.values())
    mligds_filtered = datas.loc[0:x_max_age]

    date_lbl = datas.columns.get_level_values("date")[0]
    y_max_total = max(mligds_filtered[[(date_lbl, "男"), (date_lbl, "女")]].max())
    y_min_total = min(mligds_filtered[[(date_lbl, "男"), (date_lbl, "女")]].min())

    # 繪製折線圖
    fig, ax = plt.subplots(figsize=(10, 6))
    mligds_filtered.plot(
        y=[(date_lbl, "男"), (date_lbl, "女")],
        ax=ax,
        linewidth=2,
        color=["skyblue", "pink"],
    )

    # 畫背景區塊與文字
    for i, (label, (start, end)) in enumerate(bgages.items()):
        rect = patches.Rectangle(
            (start, 0),
            end - start,
            y_max_total * 1.2,
            facecolor=bgclrs[i],
            edgecolor="none",
            alpha=0.2,
        )
        ax.add_patch(rect)
        vertical_text = "\n".join(list(label))
        ax.text(
            (start + end) / 2,
            y_max_total * 0.95,
            vertical_text,
            ha="center",
            va="center",
            fontsize=10,
        )

    data_str = date_lbl.strftime("%Y-%m")
    ax.set_title(f"桃園市 {data_str} {title_name}年齡區間曲線圖", fontsize=26)

    # X 軸與 Y 軸刻度調整
    x_ticks_sorted = sorted(list(set(sum(bgages.values(), []))))
    ax.set_xlim(0, x_max_age)
    ax.set_xticks(x_ticks_sorted)
    ax.set_xlabel("年齡", fontsize=12)
    ax.set_ylim(y_min_total * 0.95, y_max_total * 1.1)
    ax.set_ylabel("人\n口\n數", rotation=0, labelpad=10, fontsize=12)
    ax.grid(axis="y", linestyle="--", alpha=0.8)
    ax.legend(title="性別", labels=["男", "女"])
    plt.tight_layout()

    # 記憶體轉換為 Base64
    img = io.BytesIO()
    plt.savefig(img, format="png", dpi=100, bbox_inches="tight")
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode("utf8")
    plt.close()
    return plot_url


# --- 6. Flask 路由 (包含您的數據清洗步驟) ---
@app.route("/")
def index():
    # A. 從雲端撈資料
    db_res = database.get_latest_data()
    if not db_res["success"]:
        return f"<h3>數據載入失敗：{db_res['message']}</h3>"

    # B. 轉換為 DataFrame
    df = pd.DataFrame(db_res["rows"], columns=db_res["columns"])

    # C. 🛠️ 執行您的資料清洗與轉置邏輯
    df_drop = df.drop("region", axis=1)
    mligds = df_drop.groupby(["date", "gender"]).sum().T.reset_index(drop=True)
    mligds = mligds.sort_index(
        axis=1, level=["date", "gender"], ascending=[True, False]
    )

    # 確保 columns 的 date 格式是 datetime 物件，方便 strftime 格式化
    mligds.columns.set_levels(
        pd.to_datetime(mligds.columns.levels[0]), level=0, inplace=True
    )

    # D. 丟入繪圖函式，取得圖片
    chart_data = get_chart_base64(mligds, labor_bgage, labor_bgclr, "人口結構")

    # E. 簡單 HTML 前端顯示
    html_template = """
    <!DOCTYPE html>
    <html>
    <head><title>桃園市人口結構圖</title></head>
    <body style="text-align: center; background-color: #f7f9fa; padding-top: 50px;">
        <h2>Flask 實時雲端數據折線圖</h2>
        <div style="box-shadow: 0 4px 8px rgba(0,0,0,0.1); display: inline-block; padding: 10px; background: white; border-radius: 8px;">
            <img src="data:image/png;base64,{{ chart_data }}">
        </div>
    </body>
    </html>
    """
    return render_template_string(html_template, chart_data=chart_data)


if __name__ == "__main__":
    app.run(debug=True)
