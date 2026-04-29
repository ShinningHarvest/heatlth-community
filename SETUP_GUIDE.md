# 🔧 Garmin 自動同步設定指南

> 完成以下步驟後，7 位成員的步數與睡眠數據將**每天 08:00 & 21:00 自動更新**。

---

## 整體流程

```
成員提供 Garmin 帳號密碼
        ↓
你將帳密存入 GitHub Secrets（加密儲存，你自己也看不到）
        ↓
GitHub Actions 每天定時登入 Garmin Connect
        ↓
自動抓取步數、睡眠、心率等數據
        ↓
更新 data/daily.json
        ↓
網站自動顯示最新數據
```

---

## Step 1 — 收集所有成員的 Garmin 帳號密碼

請透過私訊（不要在群組）向每位成員收集：

| 成員 | Garmin 帳號 Email | Garmin 密碼 |
|------|------------------|------------|
| 王正妹 | ______________ | ______________ |
| 鳩鴿   | ______________ | ______________ |
| 菊花   | ______________ | ______________ |
| 搖不停 | ______________ | ______________ |
| Nana   | ______________ | ______________ |
| Jay    | ______________ | ______________ |
| Ray    | ______________ | ______________ |

⚠️ **安全說明**：帳密只會存在 GitHub Secrets（加密），GitHub Actions 執行時讀取，
任何人（包含你）都無法在 GitHub 介面上看到原始值。

---

## Step 2 — 存入 GitHub Secrets

開啟：**https://github.com/ShinningHarvest/heatlth-community/settings/secrets/actions**

點「**New repository secret**」，依序新增 **14 個 Secrets**：

### 王正妹 (Karen)
| Name | Secret |
|------|--------|
| `GARMIN_EMAIL_KAREN` | karen 的 Garmin Email |
| `GARMIN_PASS_KAREN`  | karen 的 Garmin 密碼 |

### 鳩鴿 (Joseph)
| Name | Secret |
|------|--------|
| `GARMIN_EMAIL_JOSEPH` | joseph 的 Garmin Email |
| `GARMIN_PASS_JOSEPH`  | joseph 的 Garmin 密碼 |

### 菊花 (Juhua)
| Name | Secret |
|------|--------|
| `GARMIN_EMAIL_JUHUA` | 菊花的 Garmin Email |
| `GARMIN_PASS_JUHUA`  | 菊花的 Garmin 密碼 |

### 搖不停 (Cynthia)
| Name | Secret |
|------|--------|
| `GARMIN_EMAIL_CYNTHIA` | cynthia 的 Garmin Email |
| `GARMIN_PASS_CYNTHIA`  | cynthia 的 Garmin 密碼 |

### Nana
| Name | Secret |
|------|--------|
| `GARMIN_EMAIL_NANA` | nana 的 Garmin Email |
| `GARMIN_PASS_NANA`  | nana 的 Garmin 密碼 |

### Jay
| Name | Secret |
|------|--------|
| `GARMIN_EMAIL_JAY` | jay 的 Garmin Email |
| `GARMIN_PASS_JAY`  | jay 的 Garmin 密碼 |

### Ray
| Name | Secret |
|------|--------|
| `GARMIN_EMAIL_RAY` | ray 的 Garmin Email |
| `GARMIN_PASS_RAY`  | ray 的 Garmin 密碼 |

---

## Step 3 — 手動觸發第一次同步（測試）

1. 開啟 **https://github.com/ShinningHarvest/heatlth-community/actions**
2. 左側點「**🦶 每日 Garmin 數據同步**」
3. 右側點「**Run workflow**」→ 再點「**Run workflow**」
4. 等待約 2–3 分鐘（7 人各需幾秒）
5. 看到綠色 ✅ 代表成功
6. 開啟 **https://shinningharvest.github.io/heatlth-community/** 確認數據出現

---

## Step 4 — 完成！之後全自動

每天台灣時間 **08:00** 和 **21:00** 自動執行，無需任何人工操作。

---

## 常見問題

**Q：成員不想提供密碼怎麼辦？**
A：沒有提供的成員，網站會顯示「待授權」，其他人正常顯示。

**Q：Garmin 有啟用兩步驟驗證怎麼辦？**
A：需要暫時關閉 Garmin 帳號的 Two-Factor Authentication。
   Garmin Connect → 設定 → 帳號安全 → 關閉兩步驟驗證。

**Q：密碼被改了怎麼辦？**
A：重新到 GitHub Secrets 更新那個人的 `GARMIN_PASS_XXX` 即可。

**Q：Actions 失敗怎麼看原因？**
A：點 Actions → 點那次失敗的 run → 展開 "Fetch all members" 步驟 → 看錯誤訊息。

**Q：Nana 的 Apple Watch 可以用嗎？**
A：如果 Nana 的 Apple Watch 有同步到 Garmin Connect App，就可以抓到。
   如果沒有 Garmin 帳號，需要另外設定 Google Form 手動填步數。
