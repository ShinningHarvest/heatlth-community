#!/usr/bin/env python3
"""
Garmin Connect 自動數據抓取腳本
每天由 GitHub Actions 執行，抓取所有成員的：
- 今日步數、距離、熱量
- 昨晚睡眠（深睡/REM/淺睡）
- 靜息心率、HRV、SpO2
- Body Battery
更新 data/daily.json 和 data/weekly-steps.json
"""

import os
import json
import requests
from datetime import datetime, timedelta, date
import pytz

TAIPEI = pytz.timezone('Asia/Taipei')
TODAY = datetime.now(TAIPEI).strftime('%Y-%m-%d')
YESTERDAY = (datetime.now(TAIPEI) - timedelta(days=1)).strftime('%Y-%m-%d')

# ── 成員設定（對應 GitHub Secrets 名稱）──────────────────────────
MEMBERS = [
    {"id": "karen",   "name": "王正妹", "emoji": "🎯", "secret": "GARMIN_TOKEN_KAREN"},
    {"id": "joseph",  "name": "鳩鴿",   "emoji": "🕊️", "secret": "GARMIN_TOKEN_JOSEPH"},
    {"id": "juhua",   "name": "菊花",   "emoji": "🌸", "secret": "GARMIN_TOKEN_JUHUA"},
    {"id": "cynthia", "name": "搖不停", "emoji": "🌀", "secret": "GARMIN_TOKEN_CYNTHIA"},
    {"id": "nana",    "name": "Nana",   "emoji": "✨", "secret": "GARMIN_TOKEN_NANA"},
    {"id": "jay",     "name": "Jay",    "emoji": "🎭", "secret": "GARMIN_TOKEN_JAY"},
    {"id": "ray",     "name": "Ray",    "emoji": "⚡", "secret": "GARMIN_TOKEN_RAY"},
]

GARMIN_API = "https://connectapi.garmin.com"

# ── Garmin API 呼叫函數 ────────────────────────────────────────────

def get_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "DI-Backend": "connectapi.garmin.com",
        "Content-Type": "application/json",
    }

def fetch_daily_summary(token: str, date_str: str) -> dict:
    """抓取每日健康摘要（步數、熱量、心率等）"""
    url = f"{GARMIN_API}/wellness-service/wellness/dailySummary/{date_str}"
    r = requests.get(url, headers=get_headers(token), timeout=15)
    if r.status_code == 200:
        return r.json()
    print(f"  daily_summary HTTP {r.status_code}: {r.text[:100]}")
    return {}

def fetch_sleep(token: str, date_str: str) -> dict:
    """抓取睡眠數據"""
    url = f"{GARMIN_API}/wellness-service/wellness/dailySleepData/{date_str}"
    r = requests.get(url, headers=get_headers(token), timeout=15)
    if r.status_code == 200:
        return r.json()
    return {}

def fetch_hrv(token: str, date_str: str) -> dict:
    """抓取 HRV 數據"""
    url = f"{GARMIN_API}/hrv-service/hrv/{date_str}"
    r = requests.get(url, headers=get_headers(token), timeout=15)
    if r.status_code == 200:
        return r.json()
    return {}

def fetch_body_battery(token: str, date_str: str) -> dict:
    """抓取 Body Battery"""
    url = f"{GARMIN_API}/wellness-service/wellness/bodyBattery/date/{date_str}"
    r = requests.get(url, headers=get_headers(token), timeout=15)
    if r.status_code == 200:
        return r.json()
    return {}

def fetch_weekly_steps(token: str, week_start: str) -> int:
    """抓取本週累計步數"""
    url = f"{GARMIN_API}/wellness-service/wellness/weeklySummary/{week_start}"
    r = requests.get(url, headers=get_headers(token), timeout=15)
    if r.status_code == 200:
        d = r.json()
        return d.get("totalSteps", 0)
    return 0

# ── 計算本週開始（週日）─────────────────────────────────────────

def get_week_start() -> str:
    today = date.today()
    # Garmin 週期：週日開始
    days_since_sunday = today.weekday() + 1 if today.weekday() != 6 else 0
    sunday = today - timedelta(days=days_since_sunday)
    return sunday.strftime('%Y-%m-%d')

# ── 主要執行邏輯 ───────────────────────────────────────────────────

def main():
    week_start = get_week_start()
    print(f"📅 Fetching data for {TODAY} (week start: {week_start})")

    # 讀取現有數據
    daily_path = "data/daily.json"
    weekly_path = "data/weekly-steps.json"

    try:
        with open(daily_path) as f:
            daily_data = json.load(f)
    except FileNotFoundError:
        daily_data = {"last_updated": "", "date": "", "members": []}

    try:
        with open(weekly_path) as f:
            weekly_data = json.load(f)
    except FileNotFoundError:
        weekly_data = {"meta": {}, "weeks": []}

    results = []

    for member in MEMBERS:
        token = os.environ.get(member["secret"], "")
        print(f"\n👤 {member['name']} ({member['id']})")

        if not token or token == "":
            print(f"  ⚠ No token — skipping")
            results.append({
                "id": member["id"],
                "name": member["name"],
                "emoji": member["emoji"],
                "status": "no_token",
                "today_steps": 0,
                "week_steps": 0,
                "sleep": {},
                "hrv": None,
                "resting_hr": None,
                "spo2": None,
                "body_battery_high": None,
                "body_battery_low": None,
            })
            continue

        # 今日步數
        summary = fetch_daily_summary(token, TODAY)
        today_steps = summary.get("totalSteps", 0) or 0
        resting_hr = summary.get("restingHeartRateValue") or summary.get("averageHeartRate")
        spo2 = summary.get("averageSpo2")
        bb = summary.get("bodyBatteryHighestValue"), summary.get("bodyBatteryLowestValue")
        dist_m = summary.get("totalDistanceMeters", 0) or 0
        active_cal = summary.get("activeKilocalories", 0) or 0
        total_cal = summary.get("totalKilocalories", 0) or 0
        print(f"  Steps today: {today_steps:,}")

        # 本週累計步數
        week_steps = fetch_weekly_steps(token, week_start)
        if week_steps == 0:
            week_steps = today_steps  # fallback
        print(f"  Week steps: {week_steps:,}")

        # 昨晚睡眠
        sleep_raw = fetch_sleep(token, YESTERDAY)
        sleep = {}
        if sleep_raw:
            sleep = {
                "total_min": round((sleep_raw.get("sleepTimeSeconds", 0) or 0) / 60),
                "deep_min": round((sleep_raw.get("deepSleepSeconds", 0) or 0) / 60),
                "rem_min": round((sleep_raw.get("remSleepSeconds", 0) or 0) / 60),
                "light_min": round((sleep_raw.get("lightSleepSeconds", 0) or 0) / 60),
                "awake_min": round((sleep_raw.get("awakeSleepSeconds", 0) or 0) / 60),
                "score": sleep_raw.get("sleepScores", {}).get("overall", {}).get("value") if isinstance(sleep_raw.get("sleepScores"), dict) else None,
            }
            print(f"  Sleep: {sleep.get('total_min')}min (deep={sleep.get('deep_min')}, REM={sleep.get('rem_min')})")

        # HRV
        hrv_raw = fetch_hrv(token, YESTERDAY)
        hrv_val = None
        if hrv_raw:
            hrv_val = hrv_raw.get("lastNight", {}).get("avg") or hrv_raw.get("avgHrv")

        results.append({
            "id": member["id"],
            "name": member["name"],
            "emoji": member["emoji"],
            "status": "ok",
            "today_steps": today_steps,
            "week_steps": week_steps,
            "week_goal": 30000,
            "week_reached": week_steps >= 30000,
            "dist_km": round(dist_m / 1000, 1),
            "active_cal": active_cal,
            "total_cal": total_cal,
            "resting_hr": resting_hr,
            "spo2": spo2,
            "hrv": hrv_val,
            "body_battery_high": bb[0],
            "body_battery_low": bb[1],
            "sleep": sleep,
        })

    # 排序（本週步數降序）
    results.sort(key=lambda x: x["week_steps"], reverse=True)
    for i, r in enumerate(results):
        r["rank"] = i + 1

    # 寫入 daily.json
    daily_output = {
        "last_updated": datetime.now(TAIPEI).strftime('%Y-%m-%d %H:%M'),
        "date": TODAY,
        "week_start": week_start,
        "members": results,
    }
    with open(daily_path, "w", encoding="utf-8") as f:
        json.dump(daily_output, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Wrote {daily_path}")

    # 更新 weekly-steps.json（本週區塊）
    week_num_label = f"W{week_start}"
    weeks = weekly_data.get("weeks", [])
    current_week_idx = next((i for i, w in enumerate(weeks) if w.get("period_start") == week_start), None)
    week_entry = {
        "week_start": week_start,
        "results": [
            {
                "rank": r["rank"],
                "name": r["name"],
                "steps": r["week_steps"],
                "reached": r["week_reached"],
            }
            for r in results
        ]
    }
    if current_week_idx is not None:
        weeks[current_week_idx] = week_entry
    else:
        weeks.append(week_entry)

    weekly_data["meta"]["last_updated"] = TODAY
    with open(weekly_path, "w", encoding="utf-8") as f:
        json.dump(weekly_data, f, ensure_ascii=False, indent=2)
    print(f"✅ Wrote {weekly_path}")
    print(f"\n🏆 Ranking:")
    for r in results:
        reached = "✓" if r["week_reached"] else "✗"
        print(f"  {r['rank']}. {r['name']:6} {r['week_steps']:>8,} 步 {reached}")

if __name__ == "__main__":
    main()
