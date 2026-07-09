#!/usr/bin/env python3
"""
可转债打新检查脚本
- 每日（工作日）查询集思录，检查当天是否有可转债申购
- 如果有则推送详情，如果没有则推送"今天没有可转债打新"
"""
import json
import os
import urllib.request
from datetime import date, datetime
from notifier import pushplus_send, wxpusher_send

# 推送配置（从环境变量读取）
PUSHPLUS_TOKEN = os.environ.get("PUSHPLUS_TOKEN", "")
WXPUSHER_APP_TOKEN = os.environ.get("WXPUSHER_APP_TOKEN", "")
WXPUSHER_UIDS_STR = os.environ.get("WXPUSHER_UIDS", "[]")


def fetch_jisilu_prelist() -> list:
    """从集思录获取待发行可转债列表"""
    url = "https://www.jisilu.cn/data/cbnew/pre_list/"
    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/125.0.0.0 Safari/537.36"),
        "Referer": "https://www.jisilu.cn/",
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8")
        data = json.loads(raw)
        return data.get("rows", [])
    except Exception as e:
        print(f"[ERROR] 获取集思录数据失败: {e}")
        return []


def get_today_str() -> str:
    """返回今天的日期字符串 YYYY-MM-DD"""
    return date.today().strftime("%Y-%m-%d")


def check_subscribe():
    today_str = get_today_str()
    print(f"[INFO] 检查日期: {today_str}")

    rows = fetch_jisilu_prelist()
    if not rows:
        msg = f"📅 {today_str} 今天没有可转债打新（数据为空，可能非交易日）"
        print(msg)
        # 依然推送告知
        _push("可转债打新提醒", msg)
        return

    subscribe_today = []
    for row in rows:
        cell = row.get("cell", {})
        bond_nm = (cell.get("bond_nm") or "").strip()
        apply_date = (cell.get("apply_date") or "").strip()
        bond_id = (cell.get("bond_id") or "").strip()
        status_cd = (cell.get("status_cd") or "").strip()

        # 申购日期匹配今天，或状态为"申购"的
        if apply_date == today_str or status_cd == "申购":
            subscribe_today.append({
                "name": bond_nm,
                "code": bond_id,
                "status": status_cd,
                "apply_date": apply_date,
            })

    if subscribe_today:
        lines = [f"🪙 **{s['name']} ({s['code']})**" for s in subscribe_today]
        msg = (f"📢 **今天有可转债打新！**\n\n"
               f"日期：{today_str}\n\n"
               f"共 {len(subscribe_today)} 只：\n" + "\n".join(lines) + "\n\n"
               f"💡 记得在交易时段内申购（9:30-15:00）")
        print(f"[INFO] 发现 {len(subscribe_today)} 只可转债可申购")
        _push("可转债打新提醒", msg)
    else:
        msg = f"📅 {today_str} 今天没有可转债打新"
        print(msg)
        _push("可转债打新提醒", msg)


def _push(title: str, content: str):
    """同时通过 PushPlus 和 WxPusher 推送"""
    errors = []

    if PUSHPLUS_TOKEN:
        try:
            r = pushplus_send(PUSHPLUS_TOKEN, title, content)
            print(f"[PushPlus] 推送结果: {r.get('code')} {r.get('msg', '')}")
            if r.get("code") != 200:
                errors.append(f"PushPlus: {r}")
        except Exception as e:
            errors.append(f"PushPlus 异常: {e}")

    if WXPUSHER_APP_TOKEN:
        try:
            uids = json.loads(WXPUSHER_UIDS_STR)
            r = wxpusher_send(WXPUSHER_APP_TOKEN, content, title, uids)
            print(f"[WxPusher] 推送结果: code={r.get('code')} success={r.get('success')}")
        except Exception as e:
            errors.append(f"WxPusher 异常: {e}")

    if errors:
        print(f"[WARN] 部分推送失败: {'; '.join(errors)}")


if __name__ == "__main__":
    check_subscribe()
