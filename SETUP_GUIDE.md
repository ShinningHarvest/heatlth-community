# 🔧 Garmin 自動同步設定指南

> 完成以下步驟後，7 位成員的數據將**每天 08:00 & 21:00 自動更新**，無需任何人工操作。

---

## 第一步：申請 Garmin Developer 帳號

1. 開啟 https://developer.garmin.com/gc-developer-program/overview/
2. 點「Apply Now」填寫申請表
3. Application Type 選：**Personal / Non-Commercial**
4. Use Case 描述（英文）：
   > "A private health community dashboard for 7 members to track weekly step counts and sleep quality from Garmin Connect. Non-commercial, personal use only."
5. 等待 Garmin 審核（通常 1–3 個工作天）
6. 收到核准 Email 後，在 Developer Portal 取得：
   - `Consumer Key`（即 Client ID）
   - `Consumer Secret`（即 Client Secret）

---

## 第二步：填入 Client ID & Secret

開啟 `scripts/garmin_oauth.py`，找到這兩行並填入你的值：

```python
GARMIN_CLIENT_ID     = "your_client_id_here"    ← 改這裡
GARMIN_CLIENT_SECRET = "your_client_secret_here" ← 改這裡
```

---

## 第三步：每位成員各做一次 OAuth 授權

在你的電腦執行（每位成員各做一次）：

```bash
# 安裝依賴
pip install requests

# 為每位成員分別執行
python scripts/garmin_oauth.py --member karen
python scripts/garmin_oauth.py --member joseph
python scripts/garmin_oauth.py --member juhua
python scripts/garmin_oauth.py --member cynthia
python scripts/garmin_oauth.py --member nana
python scripts/garmin_oauth.py --member jay
python scripts/garmin_oauth.py --member ray
```

腳本會印出一個 Garmin 授權連結，傳給成員點開，成員點「Allow」後把回傳網址貼回給你，腳本自動完成 token 交換。

---

## 第四步：把 Token 存入 GitHub Secrets

1. 開啟 https://github.com/ShinningHarvest/heatlth-community/settings/secrets/actions
2. 點「New repository secret」
3. 依序新增 7 個 Secrets：

| Secret Name           | 值                     |
|-----------------------|------------------------|
| GARMIN_TOKEN_KAREN    | Karen 的 access token  |
| GARMIN_TOKEN_JOSEPH   | Joseph 的 access token |
| GARMIN_TOKEN_JUHUA    | 菊花的 access token    |
| GARMIN_TOKEN_CYNTHIA  | Cynthia 的 access token|
| GARMIN_TOKEN_NANA     | Nana 的 access token   |
| GARMIN_TOKEN_JAY      | Jay 的 access token    |
| GARMIN_TOKEN_RAY      | Ray 的 access token    |

---

## 第五步：手動觸發第一次同步（測試）

1. 開啟 https://github.com/ShinningHarvest/heatlth-community/actions
2. 點左側「🦶 每日 Garmin 數據同步」
3. 點「Run workflow」→「Run workflow」
4. 等待約 1 分鐘
5. 開啟 https://shinningharvest.github.io/heatlth-community/ 確認數據出現

---

## 之後完全自動

每天台灣時間 **08:00** 和 **21:00** 自動執行，更新後網站立刻反映最新數據。

---

## Token 有效期與更新

Garmin token 有效期 **1 年**，到期前你會收到 GitHub Actions 失敗通知。
到時重新執行 `garmin_oauth.py` 取得新 token，更新 GitHub Secrets 即可。

---

## 常見問題

**Q：成員不想授權怎麼辦？**
A：該成員數據會顯示「待授權」，其他人正常顯示，不影響整體功能。

**Q：Apple Watch 的 Nana 和 Jay 後來加入了？**
A：Apple Watch 不支援 Garmin API，他們需要手動每週填步數（可額外設定 Google Form）。

**Q：Garmin Developer 申請被拒？**
A：可以改用「個人手動截圖 + 每週更新 weekly-steps.json」的方式，繼續使用現有排行榜。
