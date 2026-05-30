# 🗺️ 桃園市各區人口結構與動態視覺化系統 (TAOYUAN POP)

![Version](https://img.shields.io/badge/Version-V1.0-blue)
![Python](https://img.shields.io/badge/Backend-Python%20%7C%20Flask-green)
![Frontend](https://img.shields.io/badge/Frontend-HTML5%20%7C%20CSS3%20%7C%20JavaScript-orange)
![Chart.js](https://img.shields.io/badge/Charts-Chart.js-lightgrey)

本專案是一個基於 **桃園資料開放平台** 數據所開發的跨平台跨瀏覽器人口結構視覺化儀表板。前端利用響應式網頁設計 (RWD) 概念呈現清晰的數據報表，並整合 Chart.js 提供全方位的互動式圖表分析，協助使用者一目了然地掌握桃園市各行政區的人口老化、性別比例與近一年人口流動變化。

---

## ✨ 核心功能與視覺亮點

### 1. 📊 即時數據整合與動態圖表

- **各區總人口數柱狀圖**：直觀呈現桃園 13 個行政區的人口規模對比（優化為 3:1 黃金視覺比例）。
- **男女年齡結構折線圖**：
  - 細緻繪製 0~100 歲的人口連續線條。
  - **創新功能**：整合 `Chart.js Annotation 插件`，將圖表背景直觀切換為 **幼年期 (0-14歲)**、**青壯年期 (15-64歲)** 與 **老年期 (65歲以上)** 三大核心生命週期。
  - **UI 優化**：自訂圖例為實心橫線（非預設空心框），並全面放大文字級距，提升大螢幕易讀性。
- **人口三階段權重百分比（圓餅圖三聯星）**：橫向等比例並排幼年、青壯年、老年權重，秒懂哪一區最年輕、哪一區面臨高齡化。
- **近一年人口趨勢動態監控**：整合非同步控制列（Dropdown Selector），使用者可隨時切換指定行政區，動態追蹤 12 個月內的人口消長與波動。

### 2. ⚡ 精緻無瑕的 CSS UI 介面

- 採用現代化 **冷色調灰綠背景** (`#f4f7f6`) 搭配深色質感文字。
- **Sticky Table Header**：大數據表格在垂直滾動時，表頭自動固定於頂部。
- **等比例縮放保護**：圖表全面導入 `aspect-ratio` 鎖定比例，在大螢幕/桌機環境下展現完美的呼吸空間與留白。

---

## 🛠️ 技術棧 (Tech Stack)

- **後端架構 (Backend)**：Python / Flask (Jinja2 模板引擎)
- **前端核心 (Frontend)**：HTML5, CSS3 (Variables, Flexbox, Sticky), JavaScript (Vanilla JS / Fetch API)
- **資料視覺化 (Data Visualization)**：Chart.js v4.x + Chart.js Annotation Plugin
- **資料庫 (Database)**：**TiDB Cloud (Distributed SQL Server)**
- **數據來源 (Data Source)**：桃園市政府資料開放平台

---

## 💾 資料管道與數據清洗 (Data Pipeline & Preprocessing)

本專案的原始數據來自開放平台 API。由於原始 CSV 數據存在多處不一致與缺失或數據值錯亂資料，在進入前端視覺化之前，於後端（Jupyter Notebook / Python）進行了嚴格的 ETL (Extract, Transform, Load) 數據清洗程序：

### 1. 數據獲取與結構

- **取得方式**：透過自動化腳本調用政府開放平台 API。
- **原始結構**：採用標準 `CSV` 格式。

### 2. 資料清洗與轉換 (Data Cleaning)

為了確保 Chart.js 能精準讀取且前端表格呈現一致，我們處理了以下核心問題：

- **處理資料列數不一致**：部分月份或區域的資料行數有缺漏，後端已進行對齊與補值處理，確保結構完整。
- **性別欄位規格化**：統一性別文字格式，以便前端進行多維度的分組與過濾。
- **行政區域名稱修正**：將歷史數據或誤植的「市、鎮、鄉」等舊制或錯字，一律自動映射轉換為現行的**「區」**（例如：將符合桃園範圍的名稱統一）。
- **排除數值誤植**：偵測並修正原始資料中不合理的異常極端值（如打錯字導致的人口暴增或暴跌）。
- **統一數值顯示格式**：
  - **千分位符號處理**：清除原始字串中的千分位逗號（如 `203,455` 轉為 `203455`），避免 JavaScript 在轉 `Number()` 時解析失敗。
  - **零值（Zero/Null）顯示優化**：將原始資料中的空字串、`NaN` 或特殊符號，統一校正為數字 `0`，防止圖表斷線或破版。

### ⚠️ 已知資料限制與缺陷 (Data Issues & Caveats)

本專案忠實呈現官方開放資料，但因公部門原始資料來源問題，特別註記以下特殊月份處理：

1. **民國 109 年 7 月 (10907)**：因官方網頁及 API 該月份無數據提供，此段時間序列採取留空/跳過處理。
2. **民國 110 年 6 月 (11006)**：該月份官方釋出的數據內容錯誤率過高（包含嚴重欄位錯位與數值邏輯矛盾），經評估後列為無法使用之無效數據，故予以剔除，以維護整體趨勢圖表的正確性。

---

## 🔗 參考資源

- [桃園資料開放平台](https://opendata.tycg.gov.tw/)
- [政府資料開放平臺](https://data.gov.tw/)

---

## 📂 專案目錄結構 (Project Structure)

```text
├── main.py                 # Flask 後端主程式、API 路由與伺服器核心
├── database.py             # 核心資料庫連接函式庫 (封裝 TiDB 連線與 SQL 查詢邏輯)
├── pop.py                  # 資料庫推進腳本 (負責將清洗後的最新數據上傳/同步至 TiDB 雲端)
├── templates/
│   └── index.html          # 核心前端儀表板頁面 (整合 Jinja2 模板渲染)
├── datas_one.ipynb         # 數據清洗、轉換與測試用 Jupyter Notebook (已列入 .gitignore)
├── .gitignore              # 專案版本控制忽略清單
└── README.md               # 專案說明文件

```

---

## 👨‍🏫 製作團隊與致謝

- 指導老師 (Instructor)：聯成電腦 陳岳洋老師

- 開發作者 (Developer by)：irw

- 技術協作 (Powered by)：Gemini & GitHub Copilot 雙 AI 協作夥伴

- 當前版本：TAOYUAN POP V1.0
