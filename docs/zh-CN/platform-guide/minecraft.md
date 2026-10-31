# Minecraft 平台特性文档

MinecraftAdapter 是基于 RCON 协议的 Minecraft Java 版服务器适配器，支持命令执行、消息发送与日志事件监听。

---

## 文档信息

- 对应模块版本: 0.1.0
- 维护者: ErisPulse

## 基本信息

- 平台简介：Minecraft Java 版服务器机器人（通过 RCON 远程控制台）
- 适配器名称：MinecraftAdapter
- 多服务器支持：支持（每账户一台服务器，断线自动重连）
- 连接方式：RCON TCP 长连接（保活 + 指数退避重连）
- 认证方式：RCON 密码（server.properties 的 rcon.password）
- 事件监听：日志 tail（可选，聊天/加入/退出）
- 链式修饰支持：支持 `.At()` 等链式修饰方法
- OneBot12 兼容：仅 text 段（RCON 无法发送媒体）

## 服务器前置配置

`server.properties`：

```properties
enable-rcon=true
rcon.port=25575
rcon.password=your_rcon_password
```

## 配置说明

```toml
[MinecraftAdapter.accounts.default]
host = "127.0.0.1"             # RCON 服务器地址
port = 25575                   # RCON 端口
password = "your_rcon_password"
bot_id = ""                    # 留空默认为账户名
enable_log_tail = false        # 启用日志监听（聊天/加入/退出事件）
log_path = "logs/latest.log"   # 日志文件路径
poll_interval = 1.0            # 日志扫描间隔（秒）
enabled = true
```

**配置项说明（每个账户）：**

- `host` / `port` / `password`：RCON 端点（必填）
- `bot_id`：事件中的机器人标识（默认为账户名），同时作为全服广播的 `group_id`
- `enable_log_tail`：日志事件开关（默认关闭）。关闭时适配器为纯命令模式（只发送、不产生事件）
- `log_path`：日志文件路径。要求适配器与服务器**同机运行**或日志目录已挂载；支持日志滚动（latest.log 轮转后自动重置读取位置）
- `poll_interval`：日志扫描间隔（秒，最小 0.2）

## 消息发送

所有发送方法返回 Task，await 后得到标准响应（见「返回值格式」）。

### 基础发送

```python
from ErisPulse import sdk
mc = sdk.adapter.get("minecraft")

# 单人消息（tellraw 纯文本）
await mc.Send.To("user", "Steve").Text("Hello Steve")

# 全服广播（say）
await mc.Send.To("server", "myserver").Text("服务器广播")
```

### 链式修饰方法

```python
# @玩家（tellraw 中内联渲染为玩家名）
await mc.Send.To("server", "myserver").At("Steve").Text(" 看看这个")
```

### 多服务器发送

```python
await mc.Send.Using("server2").To("server", "s2").Text("来自第二台服务器")
```

### 支持与不支持的消息段

| 段 | 支持 | 说明 |
|----|------|------|
| `text` | 支持 | 拼接后按目标类型转 tellraw / say |
| `mention` | 支持 | 渲染为玩家名内联 |
| `reply` | 部分支持 | 接受但 Minecraft 无引用展示 |
| `image` / `audio` / `video` / `file` | 不支持 | 返回 `retcode=10002` 并列出段类型 |

### 目标类型

| target_type | 行为 |
|-------------|------|
| `user` | `tellraw <玩家名> {"text":"..."}` 仅该玩家可见 |
| `server` / `group` | `say <内容>` 全服广播（group_id 为 bot_id） |

## 标准 API 动作（Api）

```python
from ErisPulse import sdk
mc = sdk.adapter.get("minecraft")

# 在线玩家列表（解析 list 命令输出）
result = await mc.Api.get_player_list()       # {"players": ["Steve", "Alex"], "raw": "..."}

# 连接状态
result = await mc.Api.get_status()            # {"status": "ok", "connected": true}

# 服务器身份
result = await mc.Api.get_self_info()         # {user_id, user_name, host}

# 版本
result = await mc.Api.get_version()

# 多服务器
result = await mc.Api.Using("server2").get_player_list()
```

### 支持的标准动作

| 方法 | 说明 | 数据来源 |
|------|------|---------|
| `get_status()` | RCON 连接状态 | 本地 |
| `get_self_info()` | 服务器身份（bot_id/账户名/host:port） | 本地 |
| `get_player_list()` | 在线玩家列表（解析 `list` 命令输出） | RCON |
| `get_version()` | 适配器版本 | 本地 |

### 平台扩展动作

通过 `Api.exec(cmd)` 执行任意 RCON 命令（等价于 `call_api("exec", command=...)`）：

```python
# 白名单管理
await mc.Api.exec("whitelist add Alex")
await mc.Api.exec("whitelist remove Alex")

# 服务器管理
await mc.Api.exec("time set day")
await mc.Api.exec("weather clear")
await mc.Api.exec("op Alex")
await mc.Api.exec("kick Steve")

# 数据与计分板
await mc.Api.exec("scoreboard objectives add kills deathCount")
```

> **安全提醒**：`Api.exec` 拥有服务器控制台完整权限（包括 stop/deop 等），请勿将未鉴权的入口暴露给不可信调用方。

### 不支持的标准动作

以下标准动作 RCON 无对应能力，调用返回 `retcode=10002` 或 `33001`（未连接）：

- `delete_message`（Minecraft 无消息撤回）
- `get_friend_list` / `get_group_list`（用 `get_player_list` 替代）

### 通用动作入口

```python
# send_message：等价于 Send 链
result = await mc.call_api(
    "send_message",
    _account_id="default",
    target_type="user", target_id="Steve",
    message=[{"type": "text", "data": {"text": "hi"}}],
)
```

## 发送方法返回值

```python
{
    "status": "ok",                  # ok / failed
    "retcode": 0,                    # 0 成功；33001 未连接/执行失败；10002 不支持
    "data": {"command_output": "..."},  # RCON 命令回显
    "self": {"platform": "minecraft", "user_id": "mc1"},
    "message_id": "uuid",            # 生成的消息标识（tellraw/say 无真实消息 ID）
    "message": "",
    "minecraft_raw": {"output": "..."}
}
```

## 事件类型（enable_log_tail = true）

需要 `platform == "minecraft"` 检测再使用本平台特性。**RCON 协议收不到聊天事件**（纯请求-响应协议），事件面依赖日志监听。

### 事件映射

| 服务器日志行 | Adapter 事件 | 说明 |
|--------------|--------------|------|
| `[12:34:56] [...]: <Steve> 你好` | message（`detail_type: server`） | 玩家聊天 |
| `[12:35:00] [...]: Alex joined the game` | notice（`detail_type: server_joined`） | 玩家加入 |
| `[12:36:00] [...]: Alex left the game` | notice（`detail_type: server_left`） | 玩家退出 |

### 事件字段示例

```python
# 聊天
{
  "id": "uuid",
  "time": 1793277000,
  "type": "message",
  "detail_type": "server",
  "platform": "minecraft",
  "self": {"platform": "minecraft", "user_id": "mc1", "user_name": "mc1", "account_id": "default"},
  "user_id": "Steve",                      # 玩家名
  "message": [{"type": "text", "data": {"text": "你好世界"}}],
  "alt_message": "你好世界",
  "group_id": "mc1",                       # bot_id
  "minecraft_raw": {"line": "[12:34:56] [Server thread/INFO]: <Steve> 你好世界"},
  "minecraft_raw_type": "log_line"
}

# 加入（notice）
{
  "type": "notice",
  "detail_type": "server_joined",          # 或 server_left
  "user_id": "Alex",
  "operator_id": "Alex",
  "group_id": "mc1",
  "minecraft_raw": {"line": "..."},
  "minecraft_raw_type": "log_line"
}
```

### 回环去重

`say` / `tellraw` 命令的回显同样会写入日志。适配器在发送时记录内容指纹（30 秒窗口），日志中出现相同内容时跳过发射，避免 bot 发出的消息被当成收到的事件回环。

## 注意事项

1. **RCON 无法接收聊天事件**：协议本身限制（纯请求-响应），事件面必须启用日志监听
2. **日志路径可达性**：适配器与服务器同机运行，或日志目录已挂载（容器场景挂载 `logs/`）
3. **日志格式**：依赖 vanilla / 主流服务端（Paper、Fabric 等）默认格式；修改过日志格式的插件（如自定义 chat 插件）可能解析不到
4. **RCON 并发限制**：Minecraft RCON 为单连接串行处理；适配器内置锁与保活（30 秒空命令）
5. **回环去重窗口**：30 秒内相同内容只发射一次
6. **安全**：`Api.exec` 为控制台级权限，请勿暴露给不可信调用方
