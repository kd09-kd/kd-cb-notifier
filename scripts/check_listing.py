#!/usr/bin/env python3
"""
可转债上市提醒脚本
- 检查监控清单中是否有可转债于今天上市
- 如有则在 9:15 推送到微信
"""
import json
import os
import urllib.request
from datetime import date, datetime, timedelta
from notifier import pushplus_send, wxpusher_send

# 推送配置（从环境变量读取）
PUSHPLUS_TOKEN = os.environ.get("PUSHPLUS_TOKEN", "")
WXPUSHER_APP_TOKEN = os.environ.get("WXPUSHER_APP_TOKEN", "")
WXPUSHER_UIDS_STR = os.environ.get("WXPUSHER_UIDS", "[]")

# 监控清单（申购代码, 债券名称, 债券代码, 市场, 已知上市日或 None）
MONITOR_LIST = [
    {"申购代码": "718484", "债券名称": "南芯转债", "债券代码": "118070",
     "市场": "上交所", "上市日": "2026-07-10"},
    {"申购代码": "718668", "债券名称": "鼎通转债", "债券代码": "118072",
     "市场": "上交所", "上市日": None},  # 待公告
    {"申购代码": "733456", "债券名称": "宝钛转债", "债券代码": None,
     "市场": "上交所", "上市日": None},  # 正股宝钛股份 600456
    {"申购代码": "127114", "债券名称": "宜化转债", "债券代码": "127114",
     "市场": "深交所", "上市日": None},  # 待公告
]


def get_today_str() -> str:
    return date.today().strftime("%Y-%m-%d")


def search_listing_date(code_or_name: str) -> str | None:
    """
    尝试从东方财富或巨潮资讯查询确认的上市日期
    返回 YYYY-MM-DD 或 None
    """
    today = date.today()
    # 尝试东方财富可转债详情页
    cb_detail_urls = [
        f"https://data.eastmoney.com/kzz/detail/{code_or_name}.html",
        f"https://quote.eastmoney.com/sz{code_or_name}.html",
        f"https://quote.eastmoney.com/sh{code_or_name}.html",
    ]
    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/125.0.0.0 Safari/537.36"),
    }

    # 尝试搜索同花顺
    url_10jqka = f"https://bond.10jqka.com.cn/kzz/{code_or_name}.html"
    try:
        req = urllib.request.Request(url_10jqka, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            import re
            # 匹配类似 "2026-07-10" 的日期
            dates = re.findall(r'2026-\d{2}-\d{2}', html)
            for d in dates:
                try:
                    dt = datetime.strptime(d, "%Y-%m-%d").date()
                    if date(2026, 1, 1) <= dt <= today + timedelta(days=90):
                        return d
                except ValueError:
                    continue
    except Exception:
        pass

    # 尝试搜索巨潮资讯
    search_url = (f"https://www.cninfo.com.cn/new/fulltextSearch/full?"
                  f"searchkey={code_or_name}&sdate=&edate=&isfulltext=false"
                  f"&sortName=pubdate&sortType=desc&pageNum=1")
    try:
        req = urllib.request.Request(search_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            import re
            dates = re.findall(r'2026-\d{2}-\d{2}', html)
            for d in dates:
                try:
                    dt = datetime.strptime(d, "%Y-%m-%d").date()
                    if date(2026, 1, 1) <= dt <= today + timedelta(days=90):
                        return d
                except ValueError:
                    continue
    except Exception:
        pass

    return None


def check_listing():
    today_str = get_today_str()
    print(f"[INFO] 检查上市日期: {today_str}")

    listing_today = []

    for bond in MONITOR_LIST:
        name = bond["债券名称"]
        code = bond["债券代码"]
        market = bond["市场"]
        known_date = bond["上市日"]

        # 如果有已知上市日且匹配
        if known_date and known_date == today_str:
            print(f"[INFO] {name}: 已知上市日 {known_date} == 今天 ✓")
            listing_today.append(bond)
            continue

        # 如果已知上市日但不是今天，跳过
        if known_date and known_date != today_str:
            continue

        # 上市日待公告 → 尝试查询
        print(f"[INFO] {name}: 上市日待公告，尝试在线查询 ...")
        # 先用申购代码查，再用债券代码查
        search_key = bond["申购代码"]
        if code:
            search_key = code
        found_date = search_listing_date(search_key)
        if found_date == today_str:
            print(f"[INFO] {name}: 查询到上市日 {found_date} == 今天 ✓")
            bond["上市日"] = found_date
            listing_today.append(bond)
        elif found_date:
            print(f"[INFO] {name}: 查询到上市日 {found_date}，非今天")
            bond["上市日"] = found_date
        else:
            print(f"[INFO] {name}: 暂未查到上市日期")

    if listing_today:
        lines = []
        for b in listing_today:
            code_str = b["债券代码"] or b["申购代码"]
            lines.append(f"🪙 **{b['债券名称']}（{code_str}）** — {b['市场']}")
        msg = (f"📢 **可转债上市提醒**  ⏰ 9:15\n\n"
               f"日期：{today_str}\n\n"
               f"今天上市的可转债：\n" + "\n".join(lines) + "\n\n"
               f"💡 集合竞价 9:15 开始，中签者请及时关注卖出时机！")
        print(f"[INFO] 推送上市提醒: {len(listing_today)} 只")
        _push("可转债上市提醒", msg)
    else:
        print("[INFO] 今天没有可转债上市，不推送")


def _push(title: str, content: str):
    """同时通过 PushPlus 和 WxPusher 推送"""
    errors = []

    if PUSHPLUS_TOKEN:
        try:
            r = pushplus_send(PUSHPLUS_TOKEN, title, content)
            print(f"[PushPlus] 推送结果: {r.get('code')} {r.get('msg', '')}")
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
    check_listing()
