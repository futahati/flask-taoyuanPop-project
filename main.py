from flask import Flask, render_template, jsonify
import pandas as pd
from datetime import datetime
import database

# 取得本地端的伺服器__name__
app = Flask(__name__)


@app.route("/")
def index():
    result = database.get_latest_data()

    return render_template("index.html", result=result)


if __name__ == "__main__":
    # pass
    # 最後一行，要執行
    app.run(debug=True)
