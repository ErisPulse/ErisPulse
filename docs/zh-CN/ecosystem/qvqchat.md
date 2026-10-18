# ErisPulse-QvQChat 通用智能体

[ErisPulse-QvQChat](https://pypi.org/project/ErisPulse-QvQChat/) 是一个 **通用智能体模块**，围绕工具循环构建：收发消息、调用生态模块服务、编写并运行代码、操作电脑、生成图片语音、管理定时任务与长期记忆——全部通过同一套工具协议完成。

> [!IMPORTANT]
> QvQChat 需要单独安装：
>
> ```bash
> epsdk install ErisPulse-QvQChat
> ```
>
> 同时需要在「模型池」添加至少一个 OpenAI 兼容模型（Base URL、API Key、模型名）。

## 核心能力

| 能力 | 说明 |
|---|---|
| 工具循环 | 模型输出工具调用 → 并发执行 → 结果回填 → 继续推理，直到给出最终回答 |
| 流式对话 | SSE 逐字输出，工具步骤实时可见；刷新 / 切走再回来，进度不丢 |
| 上下文压缩 | 超过 token 阈值自动把旧对话压缩为摘要（默认 128000 估算，可自定义） |
| 生态服务桥 | 自动发现模块声明的服务并转为工具，装卸模块即增减能力 |
| MCP 客户端 | stdio 与 Streamable HTTP，MCP 工具并入同一工具集 |
| 子智能体 | `spawn_agent` 派出独立会话的子智能体探索任务，只汇报结论 |
| 进程内执行 | `run_python_sdk` 主进程内运行 Python，直接访问运行时对象 |
| 电脑操作 | 三级安全沙箱（strict / standard / permissive），危险操作确认，全程审计 |
| 视觉理解 | 图片自动注入模型（不支持图片时自动剥离重试） |
| 附件 | 任意文件按 hash 去重落盘，路径交给 AI 自行处理；Ctrl+V 粘贴截图 |
| 分享会话 | 临时只读链接（有效期 + token 预算），导出 Markdown |
| 定时任务 | cron / 一次性 / 间隔，持久化，权限随创建者 |
| 会话接管 | 管理员可让智能体独占一个会话 |
| 人格系统 | 系统提示词 + 开场对话 + 工具白名单，可按会话绑定 |
| 长期记忆 | 每会话记忆条目，按相似度检索注入 |
| AI 自动命名 | 会话首轮回复后自动生成简短标题 |

## 模块扩展

任何 ErisPulse 模块声明 `services` 即自动成为 QvQChat 的工具，无需专门接口：

```python
from ErisPulse.Core.Bases import BaseModule, ModuleMeta

class Main(BaseModule):
    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(name="Draw", services=[
            {"name": "draw", "description": "根据描述生成图片，返回图片 URL"},
        ])

    async def draw(self, prompt: str, size: str = "1024x1024"):
        return {"image_url": "https://..."}
```

服务的方法签名自动映射为工具的 JSON Schema 参数定义，docstring 首行作为参数说明。

### 深度集成（可选）

模块可以额外实现以下任意服务，每个服务**独立可选**——一个模块可以只做人格扩展，也可以只注入提示词：

#### `qvq_prompts()` → 注入系统提示词

返回 `list[str]` 或 `list[{"text": str, "priority": int}]`，按 `priority` 升序拼接。

```python
async def qvq_prompts(self):
    return [
        {"text": "画图后用 send_message 把图片发给用户。", "priority": 10},
        {"text": "支持的风格：动漫、写实、水彩、像素。", "priority": 20},
    ]
```

#### `qvq_personas()` → 注册人格预设

返回人格列表，id 自动加 `ext.<模块名>.` 前缀，模块卸载自动清理。适合专门提供人格扩展的模块（如情感陪伴、翻译专员、代码审查员等）。

```python
async def qvq_personas(self):
    return [
        {"id": "companion", "name": "暖男", "system": "你是一个温暖体贴的聊天伙伴..."},
        {"id": "coder", "name": "代码导师", "system": "...", "tools": ["read_file", "run_python"]},
    ]
```

`tools` 可选限定该人格可用的工具子集。

#### `qvq_schemas()` → 显式参数 schema

返回 `dict[服务名, JSON Schema]`，覆盖方法签名推断。参数复杂或需要严格校验时使用。

```python
async def qvq_schemas(self):
    return {
        "draw": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "画面描述"},
                "size": {"type": "string", "enum": ["512x512", "1024x1024"]},
            },
            "required": ["prompt"],
        },
    }
```

### 刷新时机

深度集成服务的刷新时机：启动、模块装卸、Dashboard「工具」页手动刷新。

## 事件订阅

QvQChat 广播两个生命周期事件：

| 事件 | 时机 | 载荷 |
|---|---|---|
| `qvq.message` | 收到用户消息 | `chat_key` `platform` `sender_id` `sender_name` `text` `is_group` |
| `qvq.replied` | 回复发出后 | `chat_key` `reply` `tools` |

```python
async def setup(self):
    sdk.lifecycle.on("qvq.message", self.on_message)
```

## 作为服务被调用

| 服务 | 签名 | 说明 |
|---|---|---|
| `chat` | `(session_id, prompt, persona="")` | 与智能体对话，返回文本 |
| `run_prompt` | `(chat_key, prompt, ...)` | 运行提示词，结果可发送到目标会话 |
| `get_status` | `()` | 运行状态摘要 |

## 界面

通过 `/QvQChat/view` 独立访问，或嵌入 Dashboard 侧边栏。

![概览](https://raw.githubusercontent.com/wsu2059q/ErisPulse-QvQChat/main/.github/assets/overview.png)

![对话](https://raw.githubusercontent.com/wsu2059q/ErisPulse-QvQChat/main/.github/assets/chat.png)
