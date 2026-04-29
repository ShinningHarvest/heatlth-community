# 三萬步健康社群 🦶

> 一起慢慢走，別氣餒，加油！

## 網站頁面

| 頁面 | 說明 |
|------|------|
| [🏠 排行榜首頁](https://shinningharvest.github.io/heatlth-community/) | 每週步數競賽排行榜、歷史戰報、成員名單 |
| [📊 個人儀表板](https://shinningharvest.github.io/heatlth-community/dashboard.html) | Joser 個人 Garmin 健康數據（體重、睡眠、HRV、VO2 Max） |

## 成員（7 人）

| 暱稱 | 裝置 | 特色 |
|------|------|------|
| 王正妹 (Karen) | Garmin Forerunner S70 | 班長、創辦人 |
| 鳩鴿 (Joseph) | Garmin Connect | 每週賽評 |
| 菊花 (陳菊花) | Garmin Vivosmart | 步數之王、4週冠軍 |
| 搖不停 (Cynthia) | Garmin Vivosmart | REM 睡眠最佳 |
| Nana (單庶娜) | Apple Watch | 出差也不停 |
| Jay (盧美凡) | Garmin Vivosmart | 無臉男 |
| Ray | Garmin Connect | W8 空降最高紀錄 124,321 步 |

## 競賽規則

- 每週目標：**30,000 步**
- 計算週期：週日 00:00 — 週六 23:59
- 使用設備：Garmin Connect / Apple Watch
- 大獎：連續 4 週達標者可獲得 **Shokz 骨傳導耳機**

## 每週更新方式

1. 截圖 Garmin Connect 週挑戰排名
2. 修改 `index.html` 中 `const members` 的步數數字
3. 上傳覆蓋舊檔案到本 repo
4. GitHub Pages 自動 1-2 分鐘內更新

## 資料夾結構

```
heatlth-community/
├── index.html        ← 社群排行榜首頁
├── dashboard.html    ← Joser 個人健康儀表板
├── README.md         ← 本說明文件
└── data/
    ├── weekly-steps.json   ← 歷史步數資料
    └── members.json        ← 成員基本資料
```

## 社群歷程

- **2026/02/26** 群組成立
- **2026/03/01** 第一週挑戰開始
- **2026/04/28** 第九週，Ray 創下 124,321 步全群最高紀錄

---

*Powered by GitHub Pages · Data from Garmin Connect*
