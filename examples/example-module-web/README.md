# ErisPulse Web 能力示例模块

演示框架 Web 层能力：路由装饰器、中间件、WebSocket 生命周期钩子与 `router.app` 逃生舱。

## 功能特性

- HTTP 路由：`@router.http`（GET / POST，`HttpRequest` 自动注入）
- 中间件：`@router.middleware` glob 路径匹配（鉴权示例，令牌走环境变量）
- WebSocket：`@router.ws` 回显服务 + `on_disconnect` / `on_error` 生命周期钩子
- 逃生舱：`router.app` 直接挂载底层 FastAPI 路由（含兼容性边界说明）

## 安装

```bash
pip install -e .
```

## 使用

安装模块并启用后（Web 服务由 `ErisPulse.server` 配置控制），可用端点：

- `GET /webmodule/hello?name=xxx` - 问候接口（query 参数）
- `POST /webmodule/echo` - 回显请求 JSON（演示 `await request.json()`）
- `WS /webmodule/ws/echo` - WebSocket 回显（断开 / 错误钩子打日志）
- `GET /webmodule/direct` - 经 `router.app` 逃生舱注册的直连路由

中间件示例要求 `Authorization` 请求头等于环境变量 `ERISPULSE_WEB_TOKEN`，
未设置该环境变量时中间件直接放行（示例默认不拦截）。

## 开发

参考 ErisPulse 路由系统文档了解全部 Web 能力。
