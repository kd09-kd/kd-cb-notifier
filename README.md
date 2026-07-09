# 可转债打新 & 上市提醒

通过 GitHub Actions 定时运行，自动检查集思录数据并通过微信推送通知。

## 推送渠道

- **PushPlus**: 免费，无需额外配置
- **WxPusher**: 备用渠道

## GitHub Secrets 配置

在仓库 Settings → Secrets and variables → Actions 中添加：

| Secret | 说明 |
|--------|------|
| `PUSHPLUS_TOKEN` | PushPlus 推送 Token |
| `WXPUSHER_APP_TOKEN` | WxPusher 应用 Token |
| `WXPUSHER_UIDS` | WxPusher 用户 UID 列表 JSON 字符串 |

## 运行时间（北京时间）

- **打新提醒**: 工作日 9:30
- **上市提醒**: 工作日 9:15
