#!/usr/bin/env python3
"""
三萬步健康社群 — Garmin 自動數據抓取腳本
==========================================
使用 garminconnect 套件（非官方，用帳號密碼登入）
由 GitHub Actions 每日 08:00 & 21:00 台灣時間自動執行

抓取每位成員：
  - 本週累計步數
  - 今日步數、距離、熱量
  - 靜息心率
  - 昨晚睡眠（深睡/REM/淺睡/清醒）
  - HRV、SpO2、Body Battery

輸出：data/daily.json（供網站即時顯示）
      data/weekly-steps.json（追加本週紀錄）
"""

import os, json, sys, time
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo

try:
    from garminconnect import Garmin, GarminConnectConnectionError, GarminConnectTooManyRequestsError
except ImportError:
    print("ERROR: garminconnect not installed. Run: pip install garminconnect")
    sys.exit(1)

# ── 時區 ──────────────────────────────────────────────────────────
TZ       = ZoneInfo("Asia/Taipei")
NOW      = datetime.now(TZ)
TODAY    = NOW.strftime("%Y-%m-%d")
YEST     = (NOW - timedelta(days=1)).strftime("%Y-%m-%d")

def week_start() -> str:
    """本週週日（Garmin 週期起點）"""
    d = NOW.date()
    offset = (d.weekday() + 1) % 7   # weekday(): Mon=0 … Sun=6
    return (d - timedelta(days=offset)).strftime("%Y-%m-%d")

WEEK_START = week_start()

# ── 成員設定（對應 GitHub Secrets） ──────────────────────────────
# Secret 命名規則：GARMIN_EMAIL_KAREN / GARMIN_PASS_KAREN …
MEMBERS = [
    {"id":"karen",   "name":"王正妹", "emoji":"🎯"},
    {"id":"joseph",  "name":"鳩鴿",   "emoji":"🕊️"},
    {"id":"juhua",   "name":"菊花",   "emoji":"🌸"},
    {"id":"cynthia", "name":"搖不停", "emoji":"🌀"},
    {"id":"nana",    "name":"Nana",   "emoji":"✨"},
    {"id":"jay",     "name":"Jay",    "emoji":"🎭"},
    {"id":"ray",     "name":"Ray",    "emoji":"⚡"},
]

# ── 輔助：安全除法 ─────────────────────────────────────────────────
def safe_int(v, default=0):
    try: return int(v or default)
    except: return default

def safe_round(v, n=1, default=None):
    try: return round(float(v), n)
    except: return default

# ── 從 Garmin API 回應解析各項指標 ────────────────────────────────

def parse_steps(client, date_str: str) -> tuple[int, int, float]:
    """回傳 (today_steps, week_steps, dist_km)"""
    today_steps, week_steps, dist_km = 0, 0, 0.0
    try:
        stats = client.get_stats(date_str)
        today_steps = safe_int(stats.get("totalSteps"))
        dist_km     = safe_round(safe_int(stats.get("totalDistanceMeters")) / 1000)
    except Exception as e:
        print(f"    steps error: {e}")

    # 本週累計：用 weekly summary
    try:
        ws = client.get_weekly_steps(WEEK_START, date_str)
        # 回傳可能是 list [{"startDate":…,"totalSteps":…}] 或單筆 dict
        if isinstance(ws, list) and ws:
            week_steps = safe_int(ws[-1].get("totalSteps", 0))
        elif isinstance(ws, dict):
            week_steps = safe_int(ws.get("totalSteps", 0))
        if week_steps == 0:
            week_steps = today_steps   # fallback
    except Exception as e:
        print(f"    weekly steps error: {e}")
        week_steps = today_steps

    return today_steps, week_steps, dist_km

def parse_hr(client, date_str: str) -> tuple[int|None, float|None]:
    """回傳 (resting_hr, spo2)"""
    rhr, spo2 = None, None
    try:
        hr_data = client.get_heart_rates(date_str)
        rhr = safe_int(hr_data.get("restingHeartRate")) or None
    except Exception as e:
        print(f"    HR error: {e}")
    try:
        ox = client.get_spo2_data(date_str)
        if isinstance(ox, list) and ox:
            vals = [x.get("spO2Reading") for x in ox if x.get("spO2Reading")]
            if vals: spo2 = safe_round(sum(vals)/len(vals))
        elif isinstance(ox, dict):
            spo2 = safe_round(ox.get("averageSpO2"))
    except Exception as e:
        print(f"    SpO2 error: {e}")
    return rhr, spo2

def parse_sleep(client, date_str: str) -> dict:
    """回傳睡眠各階段（分鐘）"""
    try:
        sd = client.get_sleep_data(date_str)
        if not sd:
            return {}
        daily = sd.get("dailySleepDTO") or sd
        def to_min(key): return round(safe_int(daily.get(key, 0)) / 60)
        total  = to_min("sleepTimeSeconds")
        deep   = to_min("deepSleepSeconds")
        rem    = to_min("remSleepSeconds")
        light  = to_min("lightSleepSeconds")
        awake  = to_min("awakeSleepSeconds")
        if total == 0:
            total = deep + rem + light + awake
        score = None
        sc = daily.get("sleepScores")
        if isinstance(sc, dict):
            score = sc.get("overall", {}).get("value")
        return {"total_min":total,"deep_min":deep,"rem_min":rem,
                "light_min":light,"awake_min":awake,"score":score}
    except Exception as e:
        print(f"    sleep error: {e}")
        return {}

def parse_hrv(client, date_str: str) -> int|None:
    try:
        h = client.get_hrv_data(date_str)
        if not h: return None
        ln = h.get("hrvSummary") or h.get("lastNight") or {}
        return safe_int(ln.get("weeklyAvg") or ln.get("avg") or ln.get("lastNight5MinHigh")) or None
    except Exception as e:
        print(f"    HRV error: {e}")
        return None

def parse_body_battery(client, date_str: str) -> tuple[int|None, int|None]:
    try:
        bb = client.get_body_battery(date_str)
        if not bb: return None, None
        if isinstance(bb, list): bb = bb[0] if bb else {}
        hi = safe_int(bb.get("charged") or bb.get("bodyBatteryHighestValue")) or None
        lo = safe_int(bb.get("drained") or bb.get("bodyBatteryLowestValue")) or None
        return hi, lo
    except Exception as e:
        print(f"    Body Battery error: {e}")
        return None, None

def parse_calories(client, date_str: str) -> tuple[int, int]:
    try:
        s = client.get_stats(date_str)
        total  = safe_int(s.get("totalKilocalories"))
        active = safe_int(s.get("activeKilocalories"))
        return total, active
    except:
        return 0, 0

# ── 主流程 ────────────────────────────────────────────────────────

def fetch_member(member: dict) -> dict:
    mid = member["id"].upper()
    email = os.environ.get(f"GARMIN_EMAIL_{mid}", "")
    pwd   = os.environ.get(f"GARMIN_PASS_{mid}",  "")

    base = {
        "id":     member["id"],
        "name":   member["name"],
        "emoji":  member["emoji"],
        "status": "no_credentials",
        "today_steps":  0,
        "week_steps":   0,
        "week_goal":    30000,
        "week_reached": False,
        "dist_km":      0,
        "active_cal":   0,
        "total_cal":    0,
        "resting_hr":   None,
        "spo2":         None,
        "hrv":          None,
        "body_battery_high": None,
        "body_battery_low":  None,
        "sleep": {},
    }

    if not email or not pwd:
        print(f"  ⚠  {member['name']}: no credentials in Secrets")
        return base

    print(f"  🔑 Logging in as {email}")
    try:
        client = Garmin(email, pwd)
        client.login()
    except GarminConnectConnectionError as e:
        print(f"  ❌ Login failed: {e}")
        base["status"] = "login_error"
        return base
    except Exception as e:
        print(f"  ❌ Unexpected login error: {e}")
        base["status"] = "login_error"
        return base

    print(f"  ✅ Login OK")

    today_steps, week_steps, dist_km = parse_steps(client,  TODAY)
    rhr, spo2                        = parse_hr(client,      TODAY)
    sleep                            = parse_sleep(client,   YEST)
    hrv                              = parse_hrv(client,     YEST)
    bb_hi, bb_lo                     = parse_body_battery(client, TODAY)
    total_cal, active_cal            = parse_calories(client, TODAY)

    print(f"     steps={today_steps:,}  week={week_steps:,}  rHR={rhr}  HRV={hrv}")
    if sleep:
        print(f"     sleep={sleep.get('total_min')}min  deep={sleep.get('deep_min')}  REM={sleep.get('rem_min')}")

    # Garmin rate-limit protection
    time.sleep(2)

    return {**base,
        "status":          "ok",
        "today_steps":     today_steps,
        "week_steps":      week_steps,
        "week_goal":       30000,
        "week_reached":    week_steps >= 30000,
        "dist_km":         dist_km,
        "total_cal":       total_cal,
        "active_cal":      active_cal,
        "resting_hr":      rhr,
        "spo2":            spo2,
        "hrv":             hrv,
        "body_battery_high": bb_hi,
        "body_battery_low":  bb_lo,
        "sleep":           sleep,
    }


def main():
    print(f"\n{'='*55}")
    print(f"  三萬步 Garmin Sync — {NOW.strftime('%Y-%m-%d %H:%M')} CST")
    print(f"  Today: {TODAY}  |  Week start: {WEEK_START}")
    print(f"{'='*55}\n")

    results = []
    for member in MEMBERS:
        print(f"\n👤 {member['name']} ({member['id']})")
        results.append(fetch_member(member))

    # 按本週步數排序
    results.sort(key=lambda x: x["week_steps"], reverse=True)
    for i, r in enumerate(results):
        r["rank"] = i + 1

    # ── 寫入 data/daily.json ──────────────────────────────────────
    daily = {
        "last_updated": NOW.strftime("%Y-%m-%d %H:%M"),
        "date":         TODAY,
        "week_start":   WEEK_START,
        "members":      results,
    }
    with open("data/daily.json", "w", encoding="utf-8") as f:
        json.dump(daily, f, ensure_ascii=False, indent=2)
    print(f"\n✅ data/daily.json updated")

    # ── 更新 data/weekly-steps.json（本週區塊） ───────────────────
    with open("data/weekly-steps.json", encoding="utf-8") as f:
        weekly = json.load(f)

    weeks = weekly.get("weeks", [])
    entry = {
        "week_start": WEEK_START,
        "period":     f"{WEEK_START} ~ {TODAY}",
        "last_sync":  NOW.strftime("%Y-%m-%d %H:%M"),
        "results": [
            {"rank": r["rank"], "name": r["name"],
             "steps": r["week_steps"], "reached": r["week_reached"]}
            for r in results
        ]
    }
    idx = next((i for i, w in enumerate(weeks)
                if w.get("week_start") == WEEK_START), None)
    if idx is not None:
        weeks[idx] = entry
    else:
        weeks.append(entry)

    weekly["meta"]["last_updated"] = TODAY
    with open("data/weekly-steps.json", "w", encoding="utf-8") as f:
        json.dump(weekly, f, ensure_ascii=False, indent=2)
    print(f"✅ data/weekly-steps.json updated")

    # ── 排名報告 ──────────────────────────────────────────────────
    print(f"\n🏆 本週排名：")
    for r in results:
        ok = "✓" if r["week_reached"] else "✗"
        print(f"  {r['rank']}. {r['name']:5}  {r['week_steps']:>8,} 步  {ok}")

    ok_count = sum(1 for r in results if r["status"] == "ok")
    print(f"\n  同步成功：{ok_count}/{len(results)} 人\n")


if __name__ == "__main__":
    main()
