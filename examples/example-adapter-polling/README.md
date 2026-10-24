# ErisPulse Example Polling Adapter

ErisPulse HTTP 轮询模式适配器参考实现：继承 `PollingAdapter` 接入「客户端定时拉取事件」的平台（Telegram getUpdates 型）——轮询循环与指数退避由基类管理，示例只实现 `fetch_events`（经 `client.get` 拉取占位 URL）与 `convert_one`（单条转 OneBot12），并在 `ConfigClass` 声明 `poll_interval` / `token` 配置。

## 运行方式

```bash
# 方式一：本地插件（免打包）
cp -r ExamplePollingAdapter /path/to/your-bot/plugins/
epsdk run

# 方式二：开发安装
pip install -e .
epsdk run
```

运行后在 `config.toml` 的 `[ExamplePollingAdapter]` 节填入真实平台的 `endpoint` 与 `token` 即可开始轮询（`poll_interval` 热更新即时生效）。

## 相关文档

- [适配器核心概念 - 连接模式半成品基类](../../docs/zh-CN/developer-guide/adapters/core-concepts.md)
- 脚手架一键生成同款骨架：`epsdk create adapter -n MyAdapter --template polling`
