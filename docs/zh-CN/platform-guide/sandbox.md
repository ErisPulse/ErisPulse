# Sandbox 平台特性文档

SandboxAdapter 是 ErisPulse 内置的沙盒适配器，用于本地开发与模块调试——无需真实平台即可模拟消息收发。

---

## 文档信息

- 对应模块版本: 4.1.0
- 维护者: ErisPulse

## 基本信息

- 平台简介：本地沙盒环境，提供虚拟用户/群组、Web 调试面板与消息持久化
- 适配器名称：SandboxAdapter
- 平台标识：`sandbox`
- 单账户设计（本地调试场景）
- 框架要求：软依赖 `ErisPulse>=2.7.1`（运行时检测提示，不强制）

## v5 范式更新（4.1.0）

- **Api DSL 最小集**：`get_self_info` / `get_status` / `get_version` / `get_supported_actions`
- **spawn_background 任务归属**：心跳任务改用 `runtime.spawn_background`
- **框架软依赖**：运行时检测 `ErisPulse>=2.7.1` 并提示
- 导入路径更新至 `Core.Bases`（BaseConfig）

## 标准Api动作示例

```python
from ErisPulse import sdk
sandbox = sdk.adapter.get("sandbox")

result = await sandbox.Api.get_self_info()   # 沙盒机器人身份
result = await sandbox.Api.get_status()
result = await sandbox.Api.get_supported_actions()
```

## 使用说明

- 沙盒提供虚拟用户与群组，模块可像真实平台一样收发消息
- Web 调试面板可手动发送消息触发模块处理逻辑
- 消息数据持久化存储，重启后可恢复
