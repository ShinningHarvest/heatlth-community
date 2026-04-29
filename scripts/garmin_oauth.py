#!/usr/bin/env python3
"""
Garmin OAuth 2.0 授權輔助腳本
────────────────────────────────────────────────────────────────────
使用方式（每位成員各做一次，之後全自動）：

  python scripts/garmin_oauth.py --member karen

執行後：
  1. 終端機印出一個 Garmin 授權 URL
  2. 成員點開 URL，登入 Garmin，按 Allow
  3. 瀏覽器跳轉到 callback URL，複製網址貼回終端機
  4. 腳本自動取得 access_token 並印出
  5. 將 token 貼進 GitHub Secrets

注意：Garmin 個人版 API token 有效期為 1 年，之後需要重新授權
────────────────────────────────────────────────────────────────────
"""

import argparse
import hashlib
import base64
import secrets
import urllib.parse
import requests
import json
import sys

# ── 你需要向 Garmin 申請的 OAuth App 憑證 ─────────────────────────
# 申請地址：https://developer.garmin.com/gc-developer-program/overview/
# 申請 Consumer Key 和 Consumer Secret 後填入下方

GARMIN_CLIENT_ID     = "your_client_id_here"       # 從 Garmin Developer 取得
GARMIN_CLIENT_SECRET = "your_client_secret_here"   # 從 Garmin Developer 取得
REDIRECT_URI         = "https://shinningharvest.github.io/heatlth-community/auth/callback.html"

# Garmin OAuth 2.0 endpoints
AUTH_URL  = "https://connect.garmin.com/oauthConfirm"
TOKEN_URL = "https://connect.garmin.com/oauth-service/oauth/token"


def generate_pkce():
    """產生 PKCE code_verifier 和 code_challenge"""
    code_verifier  = secrets.token_urlsafe(64)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).rstrip(b'=').decode()
    return code_verifier, code_challenge


def get_auth_url(member_id: str) -> tuple[str, str]:
    """產生授權 URL 和 state"""
    code_verifier, code_challenge = generate_pkce()
    state = secrets.token_hex(16)

    params = {
        "response_type":         "code",
        "client_id":             GARMIN_CLIENT_ID,
        "redirect_uri":          REDIRECT_URI,
        "scope":                 "ACTIVITY_DATA SLEEP_DATA HEART_RATE BODY_COMPOSITION",
        "state":                 state,
        "code_challenge":        code_challenge,
        "code_challenge_method": "S256",
    }
    url = AUTH_URL + "?" + urllib.parse.urlencode(params)
    return url, code_verifier, state


def exchange_code_for_token(code: str, code_verifier: str) -> dict:
    """用授權碼換取 access_token"""
    data = {
        "grant_type":    "authorization_code",
        "code":          code,
        "redirect_uri":  REDIRECT_URI,
        "client_id":     GARMIN_CLIENT_ID,
        "client_secret": GARMIN_CLIENT_SECRET,
        "code_verifier": code_verifier,
    }
    r = requests.post(TOKEN_URL, data=data, timeout=15)
    if r.status_code == 200:
        return r.json()
    raise Exception(f"Token exchange failed {r.status_code}: {r.text}")


def main():
    parser = argparse.ArgumentParser(description="Garmin OAuth 授權工具")
    parser.add_argument("--member", required=True,
                        help="成員 ID（karen / joseph / juhua / cynthia / nana / jay / ray）")
    args = parser.parse_args()

    member_id = args.member.upper()
    secret_name = f"GARMIN_TOKEN_{member_id}"

    print(f"\n{'='*60}")
    print(f"  Garmin 授權流程 — {args.member}")
    print(f"{'='*60}\n")

    if GARMIN_CLIENT_ID == "your_client_id_here":
        print("⚠️  請先填入 GARMIN_CLIENT_ID 和 GARMIN_CLIENT_SECRET")
        print("   申請網址：https://developer.garmin.com/gc-developer-program/overview/")
        sys.exit(1)

    auth_url, code_verifier, state = get_auth_url(args.member)

    print("步驟 1：請將以下 URL 傳給成員，讓他們在瀏覽器中開啟並登入 Garmin：\n")
    print(f"  {auth_url}\n")
    print("步驟 2：成員登入後按『Allow』，瀏覽器會跳轉到一個網址")
    print("        請成員將完整的瀏覽器網址複製並傳回給你\n")

    callback_url = input("步驟 3：將成員傳回的完整網址貼在這裡：\n> ").strip()

    parsed = urllib.parse.urlparse(callback_url)
    params = urllib.parse.parse_qs(parsed.query)

    if "error" in params:
        print(f"\n❌ 授權失敗：{params.get('error_description', params['error'])}")
        sys.exit(1)

    received_state = params.get("state", [""])[0]
    if received_state != state:
        print(f"\n❌ State mismatch（安全性錯誤），請重試")
        sys.exit(1)

    code = params.get("code", [""])[0]
    if not code:
        print(f"\n❌ 找不到授權碼（code）")
        sys.exit(1)

    print("\n⏳ 正在換取 access token...")
    token_data = exchange_code_for_token(code, code_verifier)

    access_token  = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    expires_in    = token_data.get("expires_in", "unknown")

    print(f"\n✅ 授權成功！\n")
    print(f"{'='*60}")
    print(f"  GitHub Secret 名稱：{secret_name}")
    print(f"  Access Token（複製以下內容）：\n")
    print(f"  {access_token}\n")
    print(f"  Token 有效期：{expires_in} 秒（約 {int(expires_in)//86400} 天）")
    print(f"{'='*60}\n")
    print("下一步：")
    print(f"  1. 開啟 https://github.com/ShinningHarvest/heatlth-community/settings/secrets/actions")
    print(f"  2. 點『New repository secret』")
    print(f"  3. Name 填：{secret_name}")
    print(f"  4. Secret 填：上方的 Access Token")
    print(f"  5. 點『Add secret』\n")

    # 儲存 token 到本地（可選）
    token_file = f"auth/token_{args.member}.json"
    with open(token_file, "w") as f:
        json.dump({
            "member": args.member,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": expires_in,
        }, f, indent=2)
    print(f"  （Token 也已儲存到 {token_file}，請加入 .gitignore）")


if __name__ == "__main__":
    main()
