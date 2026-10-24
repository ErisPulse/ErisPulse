# ErisPulse Example Webhook Adapter

ErisPulse HTTP 回调模式适配器参考实现：继承 `WebhookAdapter` 接入「平台主动推送回调」的平台——接收路由（POST `/example_webhook/webhook`）的注册与按 owner 自动清理由基类管理，示例只实现 `convert`（载荷转 OneBot12）并覆写 `verify_request` 做 Bearer Token 校验示范。

## 运行方式

```bash
# 方式一：本地插件（免打包）
cp -r ExampleWebhookAdapter /path/to/your-bot/plugins/
epsdk run

# 方式二：开发安装
pip install -e .
epsdk run
```

运行后用 `sdk.adapter.get_connection_info("example_webhook")` 查询回调地址填到平台后台；在 `config.toml` 的 `[ExampleWebhookAdapter]` 节配置 `token` 后仅放行携带 `Authorization: Bearer <token>` 的回调（留空放行全部，便于本地联调）。

## 相关文档

- [适配器核心概念 - 连接模式半成品基类](../../docs/zh-CN/developer-guide/adapters/core-concepts.md)
- 脚手架一键生成同款骨架：`epsdk create adapter -n MyAdapter --template webhook`
