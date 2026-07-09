"""推送工具模块 - PushPlus & WxPusher"""
import json
import os
import urllib.request


def pushplus_send(token: str, title: str, content: str) -> dict:
    """通过 PushPlus 发送微信推送"""
    url = "https://www.pushplus.plus/send"
    data = json.dumps({
        "token": token,
        "title": title,
        "content": content
    }).encode("utf-8")
    req = urllib.request.Request(url, data=data,
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def wxpusher_send(app_token: str, content: str, summary: str, uids: list) -> dict:
    """通过 WxPusher 发送微信推送"""
    url = "https://wxpusher.zjiecode.com/api/send/message"
    data = json.dumps({
        "appToken": app_token,
        "content": content,
        "summary": summary,
        "contentType": 1,
        "uids": uids,
        "url": ""
    }).encode("utf-8")
    req = urllib.request.Request(url, data=data,
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))
