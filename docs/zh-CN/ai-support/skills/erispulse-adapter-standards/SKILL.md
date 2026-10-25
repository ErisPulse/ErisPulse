---
name: erispulse-adapter-standards
description: "适用于：实现/评审适配器时需要对照的硬性技术规范。覆盖场景：当你开发新适配器，或要为某个平台新增能力、需要决定"进标准还是走 `{platform}_` 扩展"、命名怎么起、平台差异怎么处理时先读本文。只是查某一领域的具体规范，可直接跳到 §2 标准地图对应的文档。当你在适配器中把平台原生会话映射到标准类型（private/group/channel/guild/thread），或在模块中不确定 `Send.To()` 该传什么目标类型、想搞清 `event.reply()` 的自动转换时对照本文。当你在适配器中把平台原生事件转换为 OneBot12 标准事件——确认必须字段、消息段结构、扩展字段命名（`{platform}_` 前缀）、会话类型推断时对照本文。当你在适配器中实现 Send 类——方法命名、媒体参数（URL/路径/bytes）的形态支持、`Raw_ob12` 反向转换、合并转发能力时对照本文。当你在适配器中实现 Api DSL 标准动作（get_user_info / delete_message 等），或在模块中跨平台调用这些标准动作、需要确认参数与 data 字段时对照本文。当你在适配器中实现 `call_api` / Send / Request 的返回值，需要确认响应结构与返回码是否符合 ErisPulse 标准，或排查某个 `retcode` 的含义时对照本文。当你的适配器需要处理好友请求/群邀请（转换请求事件、实现 `accept`/`reject`），或模块中要用 `event.approve()` / `event.reject()` 审批请求时对照本文。"
---

# ErisPulse 适配器技术标准

本技能由 ErisPulse 文档自动构建（generate-skills.py）。
仓库：https://github.com/ErisPulse/ErisPulse
各节末尾标注了来源文档路径，需要最新内容请以仓库 docs/zh-CN/ 为准。

## 内容大纲

AI 按需读取：只读需要的章节即可，不必全文加载。

- 标准化总纲: 88-102 行
- 1. 标准化原则: 104-117 行
- 2. 标准地图: 119-129 行
- 3. 标准化工作流（新能力如何进入标准）: 131-170 行
- 4. 差异处理模式（适配器层）: 172-185 行
- 5. 交互组件标准: 187-309 行
- 6. 未来候选（Roadmap）: 311-324 行
- 7. 新适配器开发者的标准 Checklist: 326-345 行
- 8. 相关文档: 347-350 行
- 会话类型: 352-361 行
- 1. 核心概念: 363-389 行
- 2. 标准会话类型: 391-437 行
- 3. 平台类型映射: 439-478 行
- 4. 自定义类型扩展: 480-522 行
- 5. 自动类型推断: 524-559 行
- 6. API 使用示例: 561-600 行
- 7. 核心 API 参考: 602-650 行
- 8. 工具方法: 652-674 行
- 9. 最佳实践: 676-696 行
- 10. 常见问题: 698-718 行
- 11. 相关文档: 720-728 行
- 事件转换: 730-737 行
- 1. 核心原则: 739-744 行
- 2. 标准字段要求: 746-792 行
- 3. 事件格式示例: 794-869 行
- 4. 消息段标准: 871-974 行
- 5. 未知事件处理: 976-992 行
- 6. 扩展命名规范: 994-1087 行
- 7. 会话类型扩展: 1089-1123 行
- 8. 模块开发者指南: 1125-1238 行
- 9. notice / request 事件的会话类型推断: 1240-1305 行
- 10. 相关文档: 1307-1318 行
- 发送方法规范: 1320-1329 行
- 0. 关键词约定: 1331-1339 行
- 1. 标准方法命名: 1341-1393 行
- 2. 参数规范详解: 1395-1585 行
- 3. 平台特有方法命名: 1587-1616 行
- 4. 参数命名规范: 1618-1628 行
- 5. 返回值规范: 1630-1635 行
- 6. 反向转换规范（OneBot12 → 平台）: 1637-1819 行
- 7. 方法发现: 1821-1843 行
- 9. 适配器开发注意事项: 1845-1851 行
- 10. 适配器实现检查清单: 1853-1883 行
- 11. 消息构建器（MessageBuilder）——适配器侧须知: 1885-1897 行
- 12. 相关文档: 1899-1907 行
- API 动作规范: 1909-1924 行
- 1. 设计背景: 1926-1938 行
- 2. 三层 DSL 并行结构: 1940-1955 行
- 3. 标准动作列表: 1957-2083 行
- 4. 使用方式: 2085-2138 行
- 5. 适配器实现: 2140-2214 行
- 6. 响应格式: 2216-2231 行
- 7. 与 SendDSL / RequestDSL 的关系: 2233-2241 行
- 8. 适配器实现检查清单: 2243-2256 行
- 9. 相关文档: 2258-2268 行
- API 响应规范: 2270-2277 行
- 1. 说明: 2279-2286 行
- 2. 基础返回结构: 2288-2303 行
- 3. 完整字段规范: 2305-2374 行
- 4. 实现要求: 2376-2380 行
- 5. 扩展规范: 2382-2457 行
- 6. 注意事项: 2459-2465 行
- 请求动作规范: 2467-2476 行
- 1. 概述: 2478-2511 行
- 2. 请求事件字段要求: 2513-2557 行
- 3. Request DSL: 2559-2624 行
- 4. Event 便捷方法: 2626-2660 行
- 5. 适配器实现要求: 2662-2807 行
- 6. 适配器实现检查清单: 2809-2826 行
- 7. 错误码扩展: 2828-2843 行
- 8. 相关文档: 2845-2854 行

## 标准化总纲

> 来源: `docs/zh-CN/standards/standardization-guide.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-CN/standards/standardization-guide.md）

# 适配器标准化指南（总纲）

> [!TIP]
> **什么时候需要读这篇**：当你开发新适配器，或要为某个平台新增能力、需要决定"进标准还是走 `{platform}_` 扩展"、命名怎么起、平台差异怎么处理时先读本文。只是查某一领域的具体规范，可直接跳到 §2 标准地图对应的文档。

本文档是 ErisPulse 适配器标准化的**总纲**：确立跨平台标准化的原则、标准地图、
差异处理模式、新能力进入标准的流程，并给出**交互组件标准**（按钮/键盘、下拉选择等）
与**交互回调事件**的完整定义。任何适配器开发者在实现新功能时应**优先采用标准定义**，
使模块开发者用同一份代码在任意平台获得一致的体验——命名一致、参数一致、返回一致。

---

## 1. 标准化原则

1. **命名一致**：同一概念在所有平台使用同一命名（如撤回统一 `delete_message`，
   按钮段统一 `keyboard`），不因平台而异
2. **参数一致**：标准动作/段/方法的参数结构在所有平台保持一致；平台特有参数
   以**可选扩展参数**或**扩展字段**提供，不污染标准签名
3. **返回一致**：所有 API/发送调用返回标准响应结构（`status/retcode/data/message_id/message`），
   `data` 内的标准字段（如 `user_id/user_name`）语义一致；平台原始数据放 `{platform}_raw`
4. **扩展有据**：平台特有能力按 `{platform}_` 前缀命名（段：`yunhu_form`；
   动作：`yunhu.board`；事件字段：`qqbot_button_id`），明确标识非跨平台
5. **差异在适配器层吸收**：模块代码面向标准编程，平台差异由适配器转换
   （参数映射、字段标准化、能力降级），不要求模块写平台分支
6. **能力降级不报错**：平台不支持某标准能力时，优雅降级（返回 `retcode=10002`、
   组件文本化进 `alt_message`），不抛异常中断模块逻辑

## 2. 标准地图

| 领域 | 标准文档 | 覆盖内容 |
|------|---------|---------|
| 事件转换 | [事件转换标准](event-conversion.md) | 事件结构、标准消息段（text/image/mention/reply/keyboard 等）、平台扩展段规范 |
| 交互组件 | **本文档 §5** | 按钮/键盘、下拉选择、卡片、交互回调事件标准字段、修饰器约定、各平台映射 |
| API 动作 | [API 动作标准](api-action-spec.md) | OneBot12 标准动作（用户/群/频道/消息管理/元动作）的统一接口与 `ApiDSL` |
| 请求操作 | [请求操作规范](request-action-spec.md) | 请求事件字段（request_id）与 Request DSL（approve/reject） |
| 发送方法 | [发送方法规范](send-method-spec.md) | Send 类方法命名、参数、修饰器、反向转换（OB12→平台） |
| 会话类型 | [会话类型标准](session-types.md) | user/group/channel/guild/dms 等会话类型定义与映射 |
| API 响应 | [API 响应标准](api-response.md) | 标准响应结构与 retcode 约定 |

## 3. 标准化工作流（新能力如何进入标准）

```
平台特有能力（{platform}_ 前缀）
        │  ≥2 个平台出现同类能力
        ▼
识别共性（抽取通用概念与参数子集）
        │
        ▼
标准草案（命名 + 参数 + 返回 + 各平台映射表）
        │  评审
        ▼
写入本总纲/各领域标准文档 + 框架基类/适配器实现兼容层
        │
        ▼
标准段/动作（无前缀）——模块可跨平台使用
```

**示例**：按钮最初各平台独立实现（`telegram_inline_keyboard` / 云湖 buttons /
QQBot keyboard）→ 出现在 ≥3 个平台 → 抽取通用结构（`label/type/data` + rows）
→ 发布标准 `keyboard` 段 → 各适配器实现兼容层（修饰器接受通用结构 + 标准段转换 + 原生段透传）。

### 3.1 命名规则

| 对象 | 规则 | 示例 |
|------|------|------|
| 标准消息段 | 小写，通用概念无前缀 | `keyboard`、`select`、`mention` |
| 平台扩展段 | `{platform}_` 前缀 | `telegram_sticker`、`yunhu_form` |
| 标准Api动作 | OB12 标准名（snake_case） | `get_group_info`、`delete_message` |
| 平台扩展动作 | `{platform}.` 前缀或协议通用名 | `yunhu.board`、`send_poke`（OB11 扩展） |
| 修饰器 | PascalCase，通用能力进框架基类 | `.Keyboard(rows)`、`.At(uid)` |
| 事件标准字段 | 通用概念无前缀 | `interaction_id`、`button_data`、`request_id` |
| 事件平台字段 | `{platform}_` 前缀 | `qqbot_event_id`、`telegram_chat_id` |

### 3.2 参数与返回规则

- 标准参数在所有平台**同名同义**；单位/格式在标准文档中明确（如秒级时间戳、字符串ID）
- 必填参数取各平台能力的**公共子集**；平台增强能力为可选参数
- 平台强约束（如 QQBot 富媒体不能与 event_id 混发）由适配器自动处理/降级，不暴露给模块
- 返回 `data` 的标准字段全平台一致；平台额外信息放 `data` 内平台命名字段或 `{platform}_raw`

## 4. 差异处理模式（适配器层）

| 模式 | 说明 | 示例 |
|------|------|------|
| **参数映射** | 标准参数 → 平台原生参数 | `delete_message(message_id)` → TG `deleteMessage(chat_id, message_id)`（登记表补全 chat_id） |
| **结构转换** | 标准段 → 平台原生结构 | `keyboard` 段 → `inline_keyboard` / buttons / QQBot keyboard |
| **动作映射** | 标准动作名 → 平台动作名 | `get_self_info` → `get_login_info`（OB11） |
| **字段标准化** | 平台响应 → 标准字段 | `getMe()` → `{user_id, user_name, user_displayname}` |
| **合成标识** | 平台无原生标识时生成确定性ID | TG join request 无ID → `tjr_{chat}_{user}_{date}` |
| **能力降级** | 不支持时文本化/返回10002 | Kook 无 keyboard → alt_message 文本化；`get_friend_list` → 10002 |
| **归一化** | 平台脏数据 → 标准格式 | QQBot @标记 openid → bot_id（名称归一化） |
| **双轨兼容** | 标准结构与平台原生结构同时接受 | `.Keyboard()` 接受通用 rows 或原生结构 |

---

## 5. 交互组件标准

### 5.1 组件清单与状态

| 组件 | 标准段 type | 状态 | 已支持平台 |
|------|------------|------|-----------|
| 按钮/键盘（keyboard） | `keyboard` | ✅ 已标准化 | Telegram / 云湖 / QQBot |
| 下拉选择（select） | `select` | 📋 预留（结构见 §5.4） | Discord / Telegram(bot) |
| 卡片（card） | `card` | 📋 预留（见 §5.5） | Kook / 云湖(html) |
| 模态框（modal） | `modal` | 📋 预留 | Discord |

> 修饰器层级约定：通用交互组件的 Send 修饰器由**适配器 Send 类实现**（框架基类
> 不内置），命名遵循 §5.2 约定，参数遵循本文档标准结构。

### 5.2 keyboard 按钮/内联键盘

#### 消息段结构（发送方向）

标准 `keyboard` 段 = `rows` 二维数组，每个按钮为
`{"label": "显示文本", "type": "callback" | "link", "data": "回调数据或跳转地址"}`，
另允许平台特有可选字段（适配器按能力映射或忽略）。

> **结构定义权威**：完整的消息段 JSON、字段表与字段语义见
> [事件转换标准 §4.1.1 keyboard 按钮/内联键盘段](event-conversion.md#411-keyboard-按钮内联键盘段跨平台通用)，
> 本节不重复。

#### 各平台映射对照

| 平台 | 标准段 → 原生结构 | 原生结构参考 |
|------|------------------|-------------|
| Telegram | `reply_markup.inline_keyboard`：`[{text, callback_data \| url}]` | callback→`callback_data`（≤64字节），link→`url` |
| 云湖 | `content.buttons`：`[{label, action_type}]` | callback→`action_type:2` + `action` + `value`，link→`action_type:1` + `url` |
| QQBot | `keyboard.content.rows`：`[{label, type, data}]` | callback→`type:2` + `data`，link→`type:0` + `data`（消息须为 markdown 类型） |
| Kook | 卡片 `action-group` 模块：`[{type, text, value, click}]` | callback→`click:return` + `value`，link→`click:link` + `url` |
| Discord | `components[].components`：`[{label, style, custom_id \| url}]` | callback→`style:1` + `custom_id`，link→`style:5` + `url` |

#### Send 修饰器（各适配器 Send 类实现）

通用修饰器由**各适配器在自己的 Send 类中实现**（不修改框架基类）：

- `.Keyboard(rows)`：标准命名，接受 §5.2 通用 rows 结构，内部生成标准 `keyboard`
  消息段（或直接转换为平台原生结构），由 `Raw_ob12` 统一处理
- `.Buttons(rows)`：可选语义别名，行为一致
- **向后兼容**：检测到平台原生结构时直接透传（不报错、不转换）
- 平台原生扩展段（如 `telegram_inline_keyboard`）继续透传，不受影响

```python
# 同一份代码，任意平台（各适配器提供修饰器与转换）
rows = [[{"label": "赞", "type": "callback", "data": "like:1"},
         {"label": "主页", "type": "link", "data": "https://example.com"}]]
await adapter.Send.To("group", gid).Keyboard(rows).Text("请选择")
```

> 适配器兼容清单：QQBot / Telegram / 云湖 已实现（修饰器 + 标准段转换）；
> 新适配器按本文档实现即可（见 §7 Checklist）。

### 5.3 交互回调事件（点击按钮之后）

用户点击按钮后，平台推送的事件**必须**提供以下标准字段（detail_type 可保留平台命名）：

| 标准字段 | 类型 | 必填 | 说明 |
|---------|------|------|------|
| `interaction_id` | str | 是 | 本次交互的ID（可用于回应，如转圈/提示） |
| `button_data` | str | 是 | 按钮回传数据（即 §5.2 的 `data`） |
| `button_label` | str | 否 | 按钮显示文本 |
| `user_id` | str | 是 | 点击者 |
| `message_id` | str | 否 | 按钮所在消息 |
| `group_id` / `channel_id` | str | 否 | 来源会话 |

**detail_type 约定**：保留各平台现有命名（`qqbot_interaction` / `telegram_callback_query` /
`yunhu_a2ui_button` 等），但**标准字段必须齐备**——模块用 `event.get("button_data")` 即可跨平台取值。

**Event 扩展方法建议**（适配器 EventMixin 提供）：

```python
def get_button_data(self) -> str: ...     # button_data
def get_interaction_id(self) -> str: ...  # interaction_id
```

**回应交互**（按平台能力）：`adapter.reply_interaction(interaction_id, code=0)`（QQBot）/
`answerCallbackQuery`（Telegram）等，命名跟随平台方法族，不强制统一。

#### 各平台回调事件映射

| 平台 | 原生事件 | detail_type | interaction_id 来源 | button_data 来源 |
|------|---------|-------------|--------------------|-----------------|
| Telegram | `callback_query` | `telegram_callback_query`（notice） | `callback_query.id` | `callback_query.data` |
| 云湖 | 按钮点击事件 | `yunhu_button_click` / `yunhu_a2ui_button` | `buttonId` / `sourceComponentId` | `value` / `actionName` |
| QQBot | `INTERACTION_CREATE` | `qqbot_interaction` | `interaction.id` | `data.resolved.button_data` |
| Kook | 按钮 点击事件 | `kook_button_click` | `msg_id`+`value` | `value` |
| Discord | `INTERACTION_CREATE` | `discord_interaction` | `interaction.id` | `data.custom_id` |

### 5.4 select 下拉选择（预留）

```json
{
  "type": "select",
  "data": {
    "placeholder": "请选择",
    "options": [
      {"label": "选项A", "data": "opt:A"},
      {"label": "选项B", "data": "opt:B"}
    ],
    "min_values": 1,
    "max_values": 1
  }
}
```

回调事件复用 §5.3 字段（`button_data` = 所选 `data`，多选时为 JSON 数组）。
首批实现平台：Discord（select menu）、Telegram（keyboard 切换）。未实现平台收到该段
应在 `alt_message` 中降级为文本列表。

### 5.5 card 卡片（预留，暂缓标准化）

卡片结构差异极大（Kook 全功能卡片模块 vs 云湖 html vs QQ markdown+keyboard），
暂不做强标准。建议：

- 富文本卡片用 `text` + `keyboard` 组合表达（多数场景足够）
- 平台全功能卡片继续用 `{platform}_card` 扩展段（如 `kook_card`）
- 待出现 ≥2 个平台的同构卡片能力再评审提升

---

## 6. 未来候选（Roadmap）

以下能力已在 ≥2 平台出现或预期出现，按优先级推进标准化：

| 候选 | 涉及平台 | 优先级 | 备注 |
|------|---------|--------|------|
| select 下拉选择 | Discord / Telegram | 高 | 结构草案见 §5.4 |
| 表态/表情回应（reactions） | QQBot / Telegram / Discord / Kook | 高 | 动作 + 事件两侧标准化 |
| 群管理动作（禁言/踢人/审批） | QQBot / 云湖 / OB11 | 高 | 多数已实现为平台动作，待抽取标准签名 |
| 公告/看板 | 云湖 / Telegram / Discord | 中 | `set_announcement` 类动作 |
| 文件资源模型（file_id 两段式） | 各平台 | 低（暂缓） | 发送直传 `SendDSL.File(file, filename)` 已是标准路径（URL/路径/bytes 直传，见[发送方法规范 §2.1](send-method-spec.md)）；file_id 模型仅当后端天然具备时透传，见 [API 动作标准 §3.5](api-action-spec.md) |
| 卡片 card | Kook / 云湖 | 低 | 结构差异大，见 §5.5 |
| 表单 form | 云湖 | 低 | 平台特有，保持 `{platform}_` 前缀 |
| 媒体转码/大小探测 | 各平台 | 低 | 适配器内部实现，不对外标准化 |

## 7. 新适配器开发者的标准 Checklist

开发新适配器时，按此清单对照实现（★ 为必须，其余推荐）：

- [ ] ★ 事件转换为 OneBot12 标准结构，继承 `BaseConverter`
- [ ] ★ 标准消息段收发支持（text/image/mention/reply/keyboard…；媒体段按
      [发送方法规范 §2.1](send-method-spec.md) 的形态分级与降级阶梯处理）
- [ ] ★ 实现 `Raw_ob12`（含标准段 → 平台结构转换；标准 `keyboard` 段必做）
- [ ] ★ 返回标准响应结构（`make_response`/`make_error`）
- [ ] ★ 多账户：`AccountConfigClass(BotAccountConfig)` + `_resolve_account`
- [ ] ★ Send 类继承 `BaseAdapter.Send`，用 `_apply_modifiers`/`send_context`
- [ ] ☆ Api DSL：标准动作映射到平台API（见 API 动作标准）
- [ ] ☆ Request DSL：请求事件含 `request_id` + `accept/reject`
- [ ] ☆ 交互组件：`keyboard` 段转换 + 交互回调标准字段 + `.Keyboard()`/`.Buttons()` 修饰器（适配器 Send 类实现）
- [ ] ☆ EventMixin：`get_raw_event()` / `get_button_data()` 等平台扩展方法
- [ ] ☆ 生命周期任务用 `runtime.spawn_background`
- [ ] ☆ 配置读取用 `self.cfg`
- [ ] ☆ 框架软依赖：不声明 ErisPulse 硬依赖 + 运行时版本检测
- [ ] ☆ i18n：配置字段与日志多语言
- [ ] ☆ platform-guide 平台文档 + 适配器仓库 platform-features.md

## 8. 相关文档

- 各领域标准见 §2 标准地图
- 框架内置适配器可作参考实现：QQBot（v5 范式全量）、OneBot11（Api DSL 映射）、云湖（BaseConverter + Web API 扩展）

## 会话类型

> 来源: `docs/zh-CN/standards/session-types.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-CN/standards/session-types.md）

# ErisPulse 会话类型标准

> [!TIP]
> **什么时候需要读这篇**：当你在适配器中把平台原生会话映射到标准类型（private/group/channel/guild/thread），或在模块中不确定 `Send.To()` 该传什么目标类型、想搞清 `event.reply()` 的自动转换时对照本文。不需要则跳过。

本文档定义了 ErisPulse 支持的会话类型标准，包括接收事件类型和发送目标类型。

## 1. 核心概念

### 1.1 接收类型 && 发送类型

ErisPulse 区分两种会话类型：

- **接收类型（Receive Type）**：用于接收的事件的 `detail_type` 字段
- **发送类型（Send Type）**：用于发送消息时 `Send.To()` 方法的目标类型

### 1.2 类型映射关系

```
接收类型 (detail_type)     发送类型 (Send.To)
─────────────────        ────────────────
private                 →        user
group                   →        group
channel                 →        channel
guild                   →        guild
thread                  →        thread
user                    →        user
```

**关键点**：
- `private` 是接收时的类型，发送时的标准类型是 `user`
- `group`、`channel`、`guild`、`thread` 在接收和发送时类型相同
- **推荐路径**：直接使用 `event.reply()`——自动完成类型转换与目标推断，无需手动处理（`private` → `user` 的自动转换即在此发生）
- **手动发送时**：请直接传发送类型（如 `Send.To("user", ...)`）；手动 `Send.To("private", ...)` 传接收类型虽也能被自动转换，但不推荐（见 §6.1）

## 2. 标准会话类型

### 2.1 OneBot12 标准类型

#### private
- **接收类型**：`private`
- **发送类型**：`user`
- **说明**：一对一私聊消息
- **ID 字段**：`user_id`
- **适用平台**：所有支持私聊的平台

#### group
- **接收类型**：`group`
- **发送类型**：`group`
- **说明**：群聊消息，包括各种形式的群组（如 Telegram supergroup）
- **ID 字段**：`group_id`
- **适用平台**：所有支持群聊的平台

#### user
- **接收类型**：`user`
- **发送类型**：`user`
- **说明**：用户类型，某些平台（如 Telegram）将私聊表示为 user 而非 private
- **ID 字段**：`user_id`
- **适用平台**：Telegram 等平台

### 2.2 ErisPulse 扩展类型

#### channel
- **接收类型**：`channel`
- **发送类型**：`channel`
- **说明**：频道消息，支持多个用户的广播式消息
- **ID 字段**：`channel_id`
- **适用平台**：Discord, Telegram, Line 等

#### guild
- **接收类型**：`guild`
- **发送类型**：`guild`
- **说明**：服务器/社区消息，通常用于 Discord Guild 级别的事件
- **ID 字段**：`guild_id`
- **适用平台**：Discord 等

#### thread
- **接收类型**：`thread`
- **发送类型**：`thread`
- **说明**：话题/子频道消息，用于社区中的子讨论区
- **ID 字段**：`thread_id`
- **适用平台**：Discord Threads, Telegram Topics 等

## 3. 平台类型映射

### 3.1 映射原则

适配器负责将平台的原生类型映射到 ErisPulse 标准类型：

```
平台原生类型 → ErisPulse 标准类型 → 发送类型
```

### 3.2 常见平台映射示例

#### Telegram
```
Telegram 类型          ErisPulse 接收类型    发送类型
─────────────────      ────────────────       ───────────
private                private                 user
group                  group                   group
supergroup             group                   group  # 映射到 group
channel                channel                 channel
```

#### Discord
```
Discord 类型          ErisPulse 接收类型    发送类型
─────────────────      ────────────────       ───────────
Direct Message         private                user
Text Channel           channel                channel
Guild                  guild                  guild
Thread                 thread                 thread
```

#### OneBot11
```
OneBot11 类型        ErisPulse 接收类型    发送类型
─────────────────      ────────────────       ───────────
private                private                user
group                  group                  group
discuss                group                  group  # 映射到 group
```

## 4. 自定义类型扩展

### 4.1 注册自定义类型

适配器可以注册自定义会话类型：

```python
from ErisPulse.Core.Event import register_custom_type

# 注册自定义类型
register_custom_type(
    receive_type="my_custom_type",
    send_type="custom",
    id_field="custom_id",
    platform="MyPlatform"
)
```

### 4.2 使用自定义类型

注册后，系统会自动处理该类型的转换和推断：

```python
# 自动推断
receive_type = infer_receive_type(event, platform="MyPlatform")
# 返回: "my_custom_type"

# 转换为发送类型
send_type = convert_to_send_type(receive_type, platform="MyPlatform")
# 返回: "custom"

# 获取对应ID
target_id = get_target_id(event, platform="MyPlatform")
# 返回: event["custom_id"]
```

### 4.3 注销自定义类型

```python
from ErisPulse.Core.Event import unregister_custom_type

unregister_custom_type("my_custom_type", platform="MyPlatform")
```

## 5. 自动类型推断

当事件没有明确的 `detail_type` 字段时，系统会根据存在的 ID 字段自动推断类型：

> [!NOTE]
> **2.7.0+ 行为变更**：`detail_type` 只有在是**已知会话类型**（标准或自定义）时才直接采用。notice/request 事件的 `detail_type`（如 `group_member_increase`、`friend_increase`）是**语义子类型**而非会话类型，会转而根据 ID 字段推断正确的会话类型。

### 5.1 推断优先级

```
优先级（从高到低）：
1. group_id     → group
2. channel_id   → channel
3. guild_id     → guild
4. thread_id    → thread
5. user_id      → private
```

### 5.2 使用示例

```python
# 事件只有 group_id
event = {"group_id": "123", "user_id": "456"}
receive_type = infer_receive_type(event)
# 返回: "group"（优先使用 group_id）

# 事件只有 user_id
event = {"user_id": "123"}
receive_type = infer_receive_type(event)
# 返回: "private"

# notice 事件的 detail_type 是语义子类型，2.7.0+ 会从 ID 字段推断
event = {"type": "notice", "detail_type": "group_member_increase", "group_id": "123"}
receive_type = infer_receive_type(event)
# 返回: "group"（而非 "group_member_increase"）
```

## 6. API 使用示例

### 6.1 发送消息

```python
from ErisPulse import adapter

# 发送给用户
await adapter.myplatform.Send.To("user", "123").Text("Hello")

# 发送给群组
await adapter.myplatform.Send.To("group", "456").Text("Hello")

# 自动转换 private → user：手动传接收类型属不推荐写法（可能有兼容性问题）
await adapter.myplatform.Send.To("private", "789").Text("Hello")
# 内部自动转换为: Send.To("user", "789")
# 推荐做法：手动发送时直接用发送类型 user，或用 event.reply() 自动完成转换（见 6.2）
```

### 6.2 事件回复

```python
from ErisPulse.Core.Event import Event

# Event.reply() 自动处理类型转换（推荐路径）
await event.reply("回复内容")
# 内部自动使用正确的发送类型（private → user 等转换在此自动完成）
```

### 6.3 命令处理

```python
from ErisPulse.Core.Event import command

@command(name="test")
async def handle_test(event):
    # 系统自动处理会话类型
    # 无需手动判断 group_id 还是 user_id
    await event.reply("命令执行成功")
```

## 7. 核心 API 参考

### 7.1 类型转换

```python
from ErisPulse.Core.Event import convert_to_send_type, convert_to_receive_type

# 接收类型 → 发送类型
convert_to_send_type("private")  # → "user"
convert_to_send_type("group")    # → "group"

# 发送类型 → 接收类型
convert_to_receive_type("user")   # → "private"
convert_to_receive_type("group")  # → "group"
```

### 7.2 ID 字段查询

```python
from ErisPulse.Core.Event import get_id_field, get_receive_type

get_id_field("group")    # → "group_id"
get_id_field("private")  # → "user_id"

get_receive_type("group_id")  # → "group"
get_receive_type("user_id")   # → "private"
```

### 7.3 一步获取发送信息

```python
from ErisPulse.Core.Event import get_send_type_and_target_id

event = {"detail_type": "private", "user_id": "123"}
send_type, target_id = get_send_type_and_target_id(event)
# send_type = "user", target_id = "123"

# 直接用于 Send.To()
await adapter.Send.To(send_type, target_id).Text("Hello")
```

### 7.4 获取目标 ID

```python
from ErisPulse.Core.Event import get_target_id

event = {"detail_type": "group", "group_id": "456"}
get_target_id(event)  # → "456"
```

## 8. 工具方法

```python
from ErisPulse.Core.Event import (
    is_standard_type,
    is_valid_send_type,
    get_standard_types,
    get_send_types,
    clear_custom_types,
)

is_standard_type("private")     # True
is_standard_type("custom_type") # False

is_valid_send_type("user")      # True
is_valid_send_type("invalid")   # False

get_standard_types()  # {"private", "group", "channel", "guild", "thread", "user"}
get_send_types()      # {"user", "group", "channel", "guild", "thread"}

clear_custom_types()                # 清除所有
clear_custom_types(platform="discord")  # 只清除指定平台的
```

## 9. 最佳实践

### 7.1 适配器开发者

1. **使用标准映射**：尽可能映射到标准类型，而非创建新类型
2. **正确转换**：确保接收类型和发送类型的映射关系正确
3. **保留原始数据**：在 `{platform}_raw` 中保留原始事件类型
4. **文档说明**：在适配器文档中说明类型映射关系

### 7.2 模块开发者

1. **使用工具方法**：使用 `get_send_type_and_target_id()` 等工具方法
2. **避免硬编码**：不要写 `if group_id else "private"` 这样的代码
3. **考虑所有类型**：代码要支持所有标准类型，不仅是 private/group
4. **灵活设计**：使用事件包装器的方法，而非直接访问字段

### 7.3 类型推断

- **优先使用 detail_type**：如果有明确字段，不进行推断
- **合理使用推断**：只在没有明确类型时使用
- **注意优先级**：了解推断优先级，避免意外结果

## 10. 常见问题

### Q1: 为什么发送时 private 要转换为 user？

A: 这是 OneBot12 标准的要求。`private` 是接收时的概念，发送时使用 `user` 更符合语义。

### Q2: 如何支持新的会话类型？

A: 通过 `register_custom_type()` 注册自定义类型，或直接使用标准类型中的 `channel`、`guild` 等。

### Q3: 事件没有 detail_type 怎么办？

A: 系统会根据存在的 ID 字段自动推断。优先级为：group > channel > guild > thread > user。

### Q4: 适配器如何映射 Telegram supergroup？

A: 在适配器的转换逻辑中，将 `supergroup` 映射为标准的 `group` 类型。

### Q5: 邮箱等特殊平台如何处理？

A: 对于不通用或平台特有的类型，使用 `{platform}_raw` 和 `{platform}_raw_type` 保留原始数据，适配器自行处理。

## 11. 相关文档

**适配器侧（映射与转换）**：
- [事件转换标准](event-conversion.md) - 完整的事件转换规范
- [发送方法规范](send-method-spec.md) - Send 类的方法命名和参数规范
- [适配器开发指南](../developer-guide/adapters/) - 适配器开发完整指南

**模块侧（不想手动处理类型转换）**：
- 用 `event.reply()` 即可自动完成类型转换与目标推断，详见 [Event 包装类详解](../developer-guide/modules/event-wrapper.md)

## 事件转换

> 来源: `docs/zh-CN/standards/event-conversion.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-CN/standards/event-conversion.md）

# 适配器标准化转换规范

> [!TIP]
> **什么时候需要读这篇**：当你在适配器中把平台原生事件转换为 OneBot12 标准事件——确认必须字段、消息段结构、扩展字段命名（`{platform}_` 前缀）、会话类型推断时对照本文。不需要则跳过。

## 1. 核心原则
1. 严格兼容：所有标准字段必须完全遵循OneBot12规范
2. 明确扩展：平台特有功能必须添加 {platform}_ 前缀（如 yunhu_form）
3. 数据完整：原始事件数据必须保留在 {platform}_raw 字段中，原始事件类型必须保留在 {platform}_raw_type 字段中
4. 时间统一：所有时间戳必须转换为10位Unix时间戳（秒级）
5. 平台统一：platform项命名必须与你在ErisPulse中注册的名称/别称一致

## 2. 标准字段要求

### 2.1 必须字段
| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 事件唯一标识符 |
| time | integer | Unix时间戳（秒级） |
| type | string | 事件类型 |
| detail_type | string | 事件详细类型（详见[会话类型标准](session-types.md)） |
| platform | string | 平台名称 |
| self | object | 机器人自身信息 |
| self.platform | string | 平台名称 |
| self.user_id | string | 机器人用户ID |

**detail_type 规范**：
- 必须使用 ErisPulse 标准会话类型（详见 [会话类型标准](session-types.md)）
- 支持的类型：`private`, `group`, `user`, `channel`, `guild`, `thread`
- 适配器负责将平台原生类型映射到标准类型

### 2.2 消息事件字段
| 字段 | 类型 | 说明 |
|------|------|------|
| message | array | 消息段数组 |
| alt_message | string | 消息段备用文本 |
| user_id | string | 用户ID |
| user_nickname | string | 用户昵称（可选） |

### 2.3 通知事件字段
| 字段 | 类型 | 说明 |
|------|------|------|
| user_id | string | 用户ID |
| user_nickname | string | 用户昵称（可选） |
| operator_id | string | 操作者ID（可选） |

### 2.4 请求事件字段
| 字段 | 类型 | 说明 |
|------|------|------|
| user_id | string | 用户ID |
| user_nickname | string | 用户昵称（可选） |
| comment | string | 请求附言（可选） |
| request_id | string | 请求标识符（**强烈推荐**，用于同意/拒绝请求操作） |

**`request_id` 字段说明**：
- `request_id` 是请求事件的唯一操作标识符，用于通过 `HandleRequest` DSL 执行同意/拒绝操作
- 适配器在转换请求事件时，应将平台原生的请求标识映射到此字段
- 如果平台本身没有请求ID，适配器应生成一个唯一标识（如基于时间戳+用户ID的哈希）
- 当 `request_id` 缺失时，`event.approve()` / `event.reject()` 将抛出 `ValueError`

## 3. 事件格式示例

### 3.1 消息事件 (message)
```json
{
  "id": "1234567890",
  "time": 1752241223,
  "type": "message",
  "detail_type": "group",
  "platform": "yunhu",
  "self": {
    "platform": "yunhu",
    "user_id": "bot_123"
  },
  "message": [
    {
      "type": "text",
      "data": {
        "text": "抽奖 超级大奖"
      }
    }
  ],
  "alt_message": "抽奖 超级大奖",
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "group_id": "group_789",
  "yunhu_raw": {...},
  "yunhu_raw_type": "message.receive.normal",
  "yunhu_command": {
    "name": "抽奖",
    "args": "超级大奖"
  }
}
```

### 3.2 通知事件 (notice)
```json
{
  "id": "1234567891",
  "time": 1752241224,
  "type": "notice",
  "detail_type": "group_member_increase",
  "platform": "yunhu",
  "self": {
    "platform": "yunhu",
    "user_id": "bot_123"
  },
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "group_id": "group_789",
  "operator_id": "",
  "yunhu_raw": {...},
  "yunhu_raw_type": "bot.followed"
}
```

### 3.3 请求事件 (request)
```json
{
  "id": "1234567892",
  "time": 1752241225,
  "type": "request",
  "detail_type": "friend",
  "platform": "onebot11",
  "self": {
    "platform": "onebot11",
    "user_id": "bot_123"
  },
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "comment": "请加好友",
  "request_id": "req_abc123",
  "onebot11_raw": {...},
  "onebot11_raw_type": "request"
}
```

## 4. 消息段标准

### 4.1 标准消息段

标准消息段**不需要**平台前缀。

| 类型 | 说明 | data 字段 |
|------|------|----------|
| `text` | 纯文本 | `text: str` |
| `image` | 图片 | `file`, `url: str` |
| `audio` | 音频 | `file`, `url: str` |
| `video` | 视频 | `file`, `url: str` |
| `file` | 文件 | `file`, `url: str`, `filename: str` |
| `mention` | @用户 | `user_id: str`, `user_name: str` |
| `reply` | 回复 | `message_id: str` |
| `face` | 表情 | `id: str` |
| `location` | 位置 | `latitude: float`, `longitude: float` |
| `keyboard` | 按钮/内联键盘 | `rows: list[list[button]]`（见 4.1.1） |

**媒体段 `file` 字段格式**（发送方向，`image` / `audio` / `video` / `file` 通用）：

| 形态 | 示例 | 适配器要求 |
|------|------|-----------|
| HTTP(S) URL | `https://example.com/a.png` | **必须**接受 |
| 本地文件路径 | `/tmp/a.png`、`C:\tmp\a.png` | **必须**接受 |
| 二进制数据 | `bytes` | **必须**接受 |
| `file://` URI / Base64 / Data URI | `file:///tmp/a.png`、`data:image/png;base64,...` | **应当**接受 |

> 完整的媒体发送协议（形态判定顺序、文件名推导、能力降级阶梯）见
> [发送方法规范 §2.1](send-method-spec.md#21-媒体消息发送协议image--voice--video--file)。

**字段方向语义**：

- `file`：**发送方向**的内容来源（上述形态）；**接收方向**由适配器填平台可取回的形态
  （通常为可下载 URL，或 `get_file` 类动作可用的资源标识）
- `url`：接收方向的平台回链（适配器转换平台事件时尽可能填入，供模块直接取用）；发送方向可不填
- `filename`：`file` 段的文件名（发送方向可选，缺省时适配器按
  [发送方法规范 §2.1.3](send-method-spec.md) 的推导顺序生成；接收方向**应当**填平台原始文件名）

```json
{
  "type": "text",
  "data": {
    "text": "Hello World"
  }
}
```

### 4.1.1 keyboard 按钮/内联键盘段（跨平台通用）

按钮/内联键盘在多个平台（Telegram / 云湖 / QQBot / Kook / Discord 等）均有对应能力，
属于**跨平台通用概念**，因此作为标准消息段（无平台前缀）。适配器应将标准段转换为
平台原生结构；平台原生扩展段（如 `telegram_inline_keyboard`）继续保留透传。

```json
{
  "type": "keyboard",
  "data": {
    "rows": [
      [
        {"label": "选项A", "type": "callback", "data": "vote:A"},
        {"label": "官网",   "type": "link",     "data": "https://example.com"}
      ]
    ]
  }
}
```

**字段说明：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `rows` | 二维数组 | 是 | 每个子数组为一行按钮 |
| `rows[][].label` | str | 是 | 按钮显示文本 |
| `rows[][].type` | str | 是 | `callback`（点击回传数据）/ `link`（跳转URL） |
| `rows[][].data` | str | 是 | 回调数据（type=callback）或跳转地址（type=link） |
| `rows[][].*` | Any | 否 | 平台特有可选字段（如 `web_app`、`menus`），适配器按能力映射或忽略 |

**适配器转换参考**（完整映射与交互回调事件标准见 [跨平台交互组件标准](standardization-guide.md)）：

| 平台 | 标准段 → 平台原生 |
|------|------------------|
| Telegram | `inline_keyboard`：`[{text, callback_data \| url}]` |
| 云湖 | `buttons`：`[{label, action_type: 2=回调 \| 1=跳转, ...}]` |
| QQBot | `keyboard.content.rows`：`[{label, type: 2=回调 \| 0=跳转, data}]`（需 markdown 类型消息） |
| Kook | 卡片 action-group 模块 |
| Discord | components：`action_row` + `buttons`（custom_id/url） |

### 4.2 平台扩展消息段

平台特有的消息段需要添加平台前缀：

```json
// 云湖 - 表单
{"type": "yunhu_form", "data": {"form_id": "123456", "form_name": "报名表"}}

// Telegram - 贴纸
{"type": "telegram_sticker", "data": {"file_id": "CAACAgIAAxkBAA...", "emoji": "😂"}}
```

**扩展消息段要求**：
1. **data 内部字段不加前缀**：`{"type": "yunhu_form", "data": {"form_id": "..."}}` 而非 `{"type": "yunhu_form", "data": {"yunhu_form_id": "..."}}`
2. **提供降级方案**：模块可能不识别扩展消息段，适配器应在 `alt_message` 中提供文本替代
3. **文档完备**：每个扩展消息段必须在适配器文档中说明 `type`、`data` 结构和使用场景

## 5. 未知事件处理

对于无法识别的事件类型，应生成警告事件：
```json
{
  "id": "1234567893",
  "time": 1752241223,
  "type": "unknown",
  "platform": "yunhu",
  "yunhu_raw": {...},
  "yunhu_raw_type": "unknown",
  "warning": "Unsupported event type: special_event",
  "alt_message": "This event type is not supported by this system."
}
```

---

## 6. 扩展命名规范

### 6.1 字段命名

**规则**：`{platform}_{field_name}`

```
平台前缀    字段名            完整字段名
────────    ───────          ──────────
yunhu       command           yunhu_command
telegram    sticker_file_id   telegram_sticker_file_id
onebot11    anonymous         onebot11_anonymous
email       subject           email_subject
```

**要求**：
- `platform` 必须与适配器注册时的平台名完全一致（大小写敏感）
- `field_name` 使用 `snake_case` 命名
- 禁止使用双下划线 `__` 开头（Python 保留）
- 禁止与标准字段同名（如 `type`、`time`、`message` 等）

### 6.2 消息段类型命名

**规则**：`{platform}_{segment_type}`

标准消息段类型（`text`、`image`、`audio`、`video`、`mention`、`reply` 等）**不得**添加平台前缀。只有平台特有的消息段类型才需要添加前缀。

### 6.3 原始数据字段命名

以下字段名是**保留字段**，所有适配器必须遵循：

| 保留字段 | 类型 | 说明 |
|---------|------|------|
| `{platform}_raw` | `any` | 平台原始事件数据的完整副本 |
| `{platform}_raw_type` | `string` | 平台原始事件类型标识 |

**要求**：
- `{platform}_raw` 必须是原始数据的深拷贝，而非引用
- `{platform}_raw_type` 必须是字符串，即使平台使用数字类型也要转换为字符串
- 这两个字段在所有事件中**必须存在**（无法获取时为 `null` 和空字符串 `""`）

### 6.4 平台特有字段示例

```json
{
  "yunhu_command": {
    "name": "抽奖",
    "args": "超级大奖"
  },
  "yunhu_form": {
    "form_id": "123456"
  },
  "telegram_sticker": {
    "file_id": "CAACAgIAAxkBAA..."
  }
}
```

### 6.5 嵌套扩展字段

扩展字段可以是简单值，也可以是嵌套对象：

```json
{
  "telegram_chat": {
    "id": 123456,
    "type": "supergroup",
    "title": "My Group"
  },
  "telegram_forward_from": {
    "user_id": "789",
    "user_name": "ForwardUser"
  }
}
```

**嵌套字段要求**：
- 顶层键必须带平台前缀
- 嵌套内部字段**不添加**平台前缀
- 嵌套深度建议不超过 3 层

### 6.6 `self` 字段扩展

`self` 对象的标准必选字段（`platform`、`user_id`）见 §2.1，以下是 ErisPulse 扩展的可选字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `self.user_name` | `string` | 机器人昵称 |
| `self.avatar` | `string` | 机器人头像 URL |
| `self.account_id` | `string` | 多账户模式下的账户标识 |

> **Bot 状态追踪**：适配器通过发送 `type: "meta"` 事件告知框架 Bot 的连接状态。支持的 `detail_type`：`connect`（上线）、`heartbeat`（心跳）、`disconnect`（离线）。系统自动从中提取 `self` 字段的 Bot 元信息进行状态追踪。此外，普通事件中的 `self` 字段也会自动发现 Bot。详见 [适配器系统 API - Bot 状态管理](../api-reference/adapter-system.md)。

---

## 7. 会话类型扩展

ErisPulse 在 OneBot12 标准的 `private`、`group` 基础上扩展了以下会话类型：

| 类型 | OneBot12 标准 | ErisPulse 扩展 | 说明 |
|------|:-----------:|:------------:|------|
| `private` | ✅ | — | 一对一私聊 |
| `group` | ✅ | — | 群聊 |
| `user` | — | ✅ | 用户类型（Telegram 等） |
| `channel` | — | ✅ | 频道（广播式） |
| `guild` | — | ✅ | 服务器/社区 |
| `thread` | — | ✅ | 话题/子频道 |

**适配器自定义类型扩展**：

```python
from ErisPulse.Core.Event.session_type import register_custom_type

# 在适配器启动时注册
register_custom_type(
    receive_type="email",      # 接收事件中的 detail_type
    send_type="email",         # 发送时的目标类型
    id_field="email_id",       # 对应的 ID 字段名
    platform="email"           # 平台标识
)
```

**自定义类型要求**：
- 必须在适配器 `start()` 时注册，在 `shutdown()` 时注销
- `receive_type` 不应与标准类型重名
- `id_field` 应遵循 `{目标}_id` 的命名模式

> 完整的会话类型定义和映射关系参见 [会话类型标准](session-types.md)。

---

## 8. 模块开发者指南

### 8.1 访问扩展字段

```python
from ErisPulse.Core.Event import message

@message()
async def handle_message(event):
    # 访问标准字段
    text = event.get_text()
    user_id = event.get_user_id()

    # 访问平台扩展字段 - 方式1：直接 get
    yunhu_command = event.get("yunhu_command")

    # 访问平台扩展字段 - 方式2：点式访问（Event 包装类）
    # event.yunhu_command

    # 访问原始数据
    raw_data = event.get("yunhu_raw")
    raw_type = event.get_raw_type()

    # 判断平台
    platform = event.get_platform()
    if platform == "yunhu":
        pass
    elif platform == "telegram":
        pass
```

### 8.2 处理扩展消息段

```python
@message()
async def handle_message(event):
    message_segments = event.get("message", [])

    for segment in message_segments:
        seg_type = segment.get("type")
        seg_data = segment.get("data", {})

        if seg_type == "text":
            text = seg_data["text"]
        elif seg_type.startswith("yunhu_"):
            if seg_type == "yunhu_form":
                form_id = seg_data["form_id"]
        elif seg_type.startswith("telegram_"):
            if seg_type == "telegram_sticker":
                file_id = seg_data["file_id"]
```

### 8.3 最佳实践

1. **优先使用标准字段**：不要假设扩展字段一定存在
2. **平台判断**：通过 `event.get_platform()` 判断平台，而非通过扩展字段是否存在来推断
3. **优雅降级**：无法处理扩展消息段时，使用 `alt_message` 作为兜底
4. **不要硬编码前缀**：使用 `platform` 变量动态拼接

```python
# ✅ 推荐
platform = event.get_platform()
raw_data = event.get(f"{platform}_raw")

# ❌ 不推荐
raw_data = event.get("yunhu_raw")
```

### 8.4 请求事件处理

模块开发者可以通过 `event.approve()` 和 `event.reject()` 对请求事件进行操作：

```python
from ErisPulse.Core.Event import request

# 好友请求：自动同意
@request.on_friend_request()
async def handle_friend_request(event):
    user_name = event.get_user_nickname() or event.get_user_id()
    comment = event.get_comment()
    
    # 同意请求
    result = await event.approve()
    if result.get("status") == "ok":
        print(f"已同意 {user_name} 的好友请求")
    else:
        print(f"同意好友请求失败: {result.get('message')}")

# 群邀请：根据条件决定
@request.on_group_request()
async def handle_group_request(event):
    comment = event.get_comment()
    
    # 拒绝请求
    result = await event.reject(comment="暂不加入新群")
```

**通过适配器直接操作**（适用于非事件处理器场景）：

```python
from ErisPulse import adapter

# 通过 request_id 直接操作
await adapter.myplatform.Request("req_abc123").accept()
await adapter.myplatform.Request("req_abc123").reject()

# 指定 Bot 账号操作
await adapter.myplatform.Request("req_abc123").Using("bot1").accept()

# 附带备注
await adapter.myplatform.Request("req_abc123").accept(comment="欢迎")
```

---

## 9. notice / request 事件的会话类型推断

### 9.1 问题背景

notice 事件和 request 事件的 `detail_type` 是**语义子类型**（如 `group_member_increase`、`friend_increase`），不是会话类型（如 `group`、`private`）。

```
type        detail_type                  含义            会话类型
────        ───────────                  ────            ────────
message     group                        群聊消息         group（detail_type 即会话类型）
message     private                      私聊消息         private（detail_type 即会话类型）
notice      group_member_increase        群成员增加       group（需从 group_id 推断）
notice      friend_increase              好友增加         private（需从 user_id 推断）
request     friend                       好友请求         private（需从 user_id 推断）
request     group                        群请求           group（detail_type 即会话类型）
```

### 9.2 推断规则

`infer_receive_type()` 的推断顺序：

1. 如果 `detail_type` 是已知会话类型（`private`/`group`/`channel`/`guild`/`thread`/`user`），直接使用
2. 如果 `detail_type` 是自定义会话类型，直接使用
3. 否则（notice/request 的语义子类型），根据 ID 字段推断：
   - 有 `group_id` → `"group"`
   - 有 `channel_id` → `"channel"`
   - 有 `guild_id` → `"guild"`
   - 有 `thread_id` → `"thread"`
   - 有 `user_id` → `"private"`

### 9.3 `event.reply()` 目标推断

notice/request 事件中 `event.reply()` 的发送目标由会话类型推断决定：

- 群通知事件（含 `group_id`）→ 回复到**群**
- 好友通知事件（仅含 `user_id`）→ 回复到**用户私聊**

```python
from ErisPulse.Core.Event import notice

@notice.on_group_increase()
async def handle_welcome(event):
    group_id = event.get("group_id")    # "group_789"
    user_id = event.get("user_id")      # "user_456"

    # event.reply() 发送到群（group/group_789）
    await event.reply("欢迎入群！")

    # 如需通知管理员（私聊），显式指定目标：
    await adapter.Send.To("user", "admin_id").Text(f"新成员 {user_id} 加入了 {group_id}")
```

### 9.4 适配器开发建议

确保 notice/request 事件中包含正确的 ID 字段：

| detail_type | 必须包含的 ID 字段 | 推断的会话类型 |
|-------------|-------------------|---------------|
| `group_member_increase` | `group_id` + `user_id` | `group` |
| `group_member_decrease` | `group_id` + `user_id` | `group` |
| `friend_increase` | `user_id` | `private` |
| `friend_decrease` | `user_id` | `private` |
| `friend`（请求） | `user_id` | `private` |
| `group`（请求） | `group_id` | `group` |

---

## 10. 相关文档

**实现转换器时配套对照**：
- [会话类型标准](session-types.md) - 会话类型定义和映射关系
- [API 响应标准](api-response.md) - 适配器 API 响应格式标准

**同一适配器的发送侧**：
- [发送方法规范](send-method-spec.md) - Send 类的方法命名、参数规范及反向转换要求
- [API 动作标准](api-action-spec.md) - OneBot12 标准 API 动作的统一接口

**查各平台已知的扩展事件与消息段**：
- [各平台特性文档](../platform-guide/README.md) - 你可以访问此文档来了解各个平台特性以及已知的扩展事件和消息段等。

## 发送方法规范

> 来源: `docs/zh-CN/standards/send-method-spec.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-CN/standards/send-method-spec.md）

# ErisPulse 发送方法规范

> [!TIP]
> **什么时候需要读这篇**：当你在适配器中实现 Send 类——方法命名、媒体参数（URL/路径/bytes）的形态支持、`Raw_ob12` 反向转换、合并转发能力时对照本文。不需要则跳过。

本文档定义了 ErisPulse 适配器中 Send 类发送方法的命名规范、参数规范和反向转换要求。

## 0. 关键词约定

本文档中的 **必须（MUST）**、**应当（SHOULD）**、**可以（MAY）** 按以下语义解释（参照 RFC 2119）：

| 关键词 | 语义 | 违反后果 |
|--------|------|---------|
| **必须** | 强制要求，框架行为/跨平台一致性依赖它 | 适配器视为不符合标准，模块代码可能无法工作 |
| **应当** | 强烈推荐；除非有充分理由，否则遵循 | 偏离时须在适配器文档中说明原因与替代行为 |
| **可以** | 可选项，按平台能力自行决定 | 无 |

## 1. 标准方法命名

所有发送方法使用 **大驼峰命名法（PascalCase）**，首字母大写。

### 1.1 标准发送方法

| 方法名 | 说明 | 参数类型 | 实现要求 |
|-------|------|---------|---------|
| `Text` | 发送文本消息 | `str` | 必须 |
| `Image` | 发送图片 | `str` \| `bytes` | 必须（基类已内置，见 §6.4） |
| `Voice` | 发送语音 | `str` \| `bytes` | 必须（基类已内置；平台不支持语音时按 §2.1.5 降级） |
| `Video` | 发送视频 | `str` \| `bytes` | 必须（基类已内置；平台不支持视频时按 §2.1.5 降级） |
| `File` | 发送文件 | `str` \| `bytes`，`filename: str \| None = None` | 必须（基类已内置） |
| `At` | @用户/群组 | `str` (user_id) | 修饰方法，按需 |
| `Face` | 发送表情 | `str` (emoji) | 可以 |
| `Reply` | 回复消息 | `str` (message_id) | 修饰方法，按需 |
| `Forward` | 转发消息 | `str` (message_id) | 可以 |
| `Markdown` | 发送 Markdown 消息 | `str` | 可以 |
| `HTML` | 发送 HTML 消息 | `str` | 可以 |
| `Card` | 发送卡片消息 | `dict` | 可以 |

> 标准方法（`Text`/`Image`/`Voice`/`Video`/`File`）由基类 `SendDSL` 内置并默认委托 `Raw_ob12`，适配器**无需重复实现**即可获得类型签名；仅当平台需要特殊逻辑时才覆盖单个方法（见 §6.4）。

### 1.2 链式修饰方法

| 方法名 | 说明 | 参数类型 |
|-------|------|---------|
| `At` | @用户（可多次调用） | `str` (user_id) |
| `AtAll` | @全体成员 | 无 |
| `Reply` | 回复消息 | `str` (message_id) |

### 1.3 协议方法

| 方法名 | 说明 | 是否必须 |
|-------|------|---------|
| `Raw_ob12` | 发送 OneBot12 格式消息段 | 必须 |

**`Raw_ob12` 是必须实现的方法**。这是适配器的核心职责之一：接收 OneBot12 标准消息段并将其转换为平台原生 API 调用。`Raw_ob12` 是反向转换（OneBot12 → 平台）的统一入口，确保模块可以不依赖平台特有方法，直接使用标准消息段发送消息。

**未重写 `Raw_ob12` 时的行为**：基类默认实现会记录 **error 级别**日志并返回标准错误响应格式（`status: "failed"`, `retcode: 10002`），提示适配器开发者必须实现此方法。

### 1.4 推荐的扩展命名约定

适配器如需支持发送非 OneBot12 格式的原始数据（如平台特定 JSON、XML 等），推荐使用以下命名约定：

| 推荐方法名 | 说明 |
|-----------|------|
| `Raw_json` | 发送任意 JSON 数据 |
| `Raw_xml` | 发送任意 XML 数据 |

**注意**：这些方法**不是**基类提供的默认方法，也不强制要求实现。它们仅作为命名约定，适配器可根据需要自行定义。如果适配器不支持这些格式，则无需定义。

**消息构建器（MessageBuilder）**：ErisPulse 提供了 `MessageBuilder` 工具类，用于方便地构建 OneBot12 消息段列表，配合 `Raw_ob12` 使用。详见 [MessageBuilder 详解](../advanced/message-builder.md)。

## 2. 参数规范详解

### 2.1 媒体消息发送协议（`Image` / `Voice` / `Video` / `File`）

本节是媒体发送的**统一协议标准**：模块以同一份代码调用四个媒体方法，适配器负责把
`file` 参数的各种形态转换为平台原生上传/发送行为。

#### 2.1.1 `file` 参数的合法形态

| 形态 | 示例 | 适配器要求 |
|------|------|-----------|
| HTTP(S) URL | `https://example.com/image.jpg` | **必须**接受 |
| 本地文件路径 | `/path/to/file.jpg`、`C:\path\to\file.jpg` | **必须**接受 |
| 二进制数据 | `b"\x89PNG..."` | **必须**接受 |
| `file://` URI | `file:///path/to/file.jpg` | **应当**接受（可转发为本地路径处理） |
| Base64 字符串 / Data URI | `iVBORw0KGgo=...`、`data:image/png;base64,...` | **应当**接受（与 OneBot12 生态惯例兼容） |

> 适配器**必须**在三种必须形态上行为一致——模块无论传 URL、路径还是 bytes，
> 收到的都是同一条消息。平台无法直接使用某形态时（如平台 API 不支持引用外部 URL），
> 由适配器自行下载/读取后上传，**不得**要求模块换形态重试。

#### 2.1.2 形态判定顺序

适配器实现媒体参数处理时，**应当**按以下顺序判定形态：

1. `bytes` 类型 → 直接上传
2. 字符串以 `http://` / `https://` 开头 → 按 URL 处理（直接引用或下载后上传，按平台能力）
3. 字符串以 `file://` 开头 → 剥离前缀按本地路径处理
4. 其余字符串 → 按本地路径处理（存在则读取上传；不存在则返回标准错误响应）

```python
def _resolve_media(self, file: "str | bytes") -> bytes:
    """形态判定与归一化（示例）"""
    if isinstance(file, (bytes, bytearray)):
        return bytes(file)
    if file.startswith(("http://", "https://")):
        return self._download(file)          # 平台不能引用 URL 时下载
    if file.startswith("file://"):
        file = file[len("file://"):]
    with open(file, "rb") as f:              # 本地路径
        return f.read()
```

#### 2.1.3 `File` 的文件名语义

`File` 方法签名：`File(file, filename=None)`（`filename` 为可选参数，基类已内置）。

文件名**推导顺序**（适配器在未显式提供 `filename` 时按此生成）：

1. 显式 `filename` 参数（最高优先）
2. URL 的 basename（如 `https://host/a/b/report.pdf` → `report.pdf`，须剥离 query string）
3. 本地路径的 basename（如 `/tmp/data/backup.zip` → `backup.zip`）
4. 平台默认生成（如 `file_{timestamp}`；**应当**保留真实扩展名——扩展名影响平台侧的
   类型识别与预览行为）

> `Image` / `Voice` / `Video` 同样**可以**接受 `filename`（经消息段 `data.filename` 传递），
> 但仅 `File` 的文件名有跨平台语义保证。

#### 2.1.4 平台限制的声明义务

各平台对媒体的大小上限、格式（MIME）、时长（音视频）等约束不同。适配器**应当**：

- 在适配器文档中声明支持的媒体类型与限制范围
- 超限或不支持的输入返回**标准错误响应**（`status: "failed"`；`retcode` 使用
  `10002` 或平台语义化错误码，`message` 说明原因），**不得**抛出异常中断模块逻辑

#### 2.1.5 能力降级阶梯

平台不支持某个媒体**类型**时，按以下阶梯降级（遵循总纲"能力降级不报错"原则）：

| 场景 | 降级行为 |
|------|---------|
| `Voice` 不支持语音消息 | **应当**按 `File`（或平台近缘形态）发送；无法表达时返回 `retcode=10002` |
| `Video` 不支持视频消息 | 同上 |
| 媒体类型完全不支持（无文件能力） | 返回 `retcode=10002`，`message` 注明不支持的数据类型 |
| 形态不支持（如无法处理 base64） | 返回 `retcode=10002`，**可以**在 `message` 中提示模块改用 URL/bytes |

**禁止**的行为：静默丢弃（无返回）、抛出异常、要求模块编写平台分支处理。

### 2.2 @用户参数规范

**方法：** `At`（修饰方法）

**参数：** `user_id` (`str`)

**要求：**
- `user_id` 应为字符串类型的用户标识符
- 不同平台的 `user_id` 格式可能不同（数字、UUID、字符串等）
- 适配器负责将 `user_id` 转换为平台特定的格式
- 注意需要把真正的发送方法调用放在最后的位置

**示例：**
```python
# 单个 @ 用户
Send.To("group", "g123").At("123456").Text("你好")

# 多个 @ 用户（链式调用）
send.To("group", "g123").At("123456").At("789012").Text("大家好")
```

### 2.3 回复消息参数规范

**方法：** `Reply`（修饰方法）

**参数：** `message_id` (`str`)

**要求：**
- `message_id` 应为字符串类型的消息标识符
- 应为之前收到的消息的 ID
- 某些平台可能不支持回复功能，适配器应优雅降级

**示例：**
```python
send.To("group", "g123").Reply("msg_123456").Text("收到")
```

### 2.4 合并转发能力（`MergeForward`，可选）

`MergeForward(nodes)` 是**可选的能力方法**：把多段内容打包为「合并转发 / 富文本折叠」形式发送，
由适配器按平台能力决定最佳呈现。与 §1.1 的 `Forward(from_chat_id, message_id)`（转发**已有**消息）
语义不同，二者并存。

> **标准背景**：OneBot12 核心标准没有 node 消息段，也没有合并转发 API——"消息结点"是 OneBot v11
> 生态（go-cqhttp 扩展）的实现层概念，v12 把这类平台特有能力下放给扩展机制。ErisPulse 的落地方式
> 即扩展机制等价物：**不新增标准消息段，而是可选能力方法 + `list_sends` 运行时探测**——实现了
> `MergeForward` 的适配器自动获得能力，未实现的调用方自动回退普通文本，模块零改动。

**方法签名：**

```python
def MergeForward(self, nodes: List[Dict]) -> asyncio.Task:
    """
    发送合并转发 / 富文本折叠消息

    :param nodes: 合并转发节点数组（go-cqhttp 扩展的 OneBot v11 节点格式）：
        [
            {
                "type": "node",
                "data": {
                    "user_id": "10000",     # 展示用发送者 id
                    "nickname": "MyBot",     # 展示用发送者昵称
                    "content": [            # 消息段数组，当前为 text 段
                        {"type": "text", "data": {"text": "【1/3】标题\n正文…"}}
                    ],
                },
            },
        ]
    :return: asyncio.Task，await 后返回标准响应格式
    """
```

**实现要求：**

1. **平台有原生合并转发**（OneBot11 系）：**必须**调用协议端专用端点
   （`send_group_forward_msg` / `send_private_forward_msg`）——NapCat 等实现会拒绝
   `send_msg` 携带的 node 段（retcode 1400）；专用端点失败时**可以**回退 `send_msg` 直发 node 段
2. **平台无原生转发但有富文本**（云湖 / Telegram / Kook / Discord / Matrix 等）：
   **应当**将节点渲染为平台的富文本折叠形态（HTML 折叠卡 / Card / Embed / blockquote 列表），
   参考样式与逐适配器任务清单见 `SDK/Adapter/ADAPTER_FORWARD_GUIDE.md`
3. **两者皆无**：**不得**实现本方法（更不得返回成功却把 node 字典当纯文本发出）——
   不实现时 `list_sends` 不含 `MergeForward`，调用方自动回退普通文本
4. **失败语义**：返回标准错误响应（`status: "failed"`）或抛出异常均可，调用方会回退纯文本发送，内容不丢失
5. **不得**在 `MergeForward` 内部再调用 `Raw_ob12` 发送同样的 nodes（OneBot11 的 `Raw_ob12`
   已内置纯 node 段自动路由，会成环）
6. **出站 node 段解析**（全适配器约定）：各适配器的 `Raw_ob12` 段分发应注册 `node` 段——
   纯 node 列表自动路由到本适配器的合并转发呈现（有 `MergeForward` 的平台等价于直接调用；
   无该方法的平台提取各节点文本以「昵称: 正文」逐行**原文输出**）；混合列表中 node 段的文本并入正文。
   任何适配器收到 node 段都不得静默丢弃。

**平台实现形态（详见 `SDK/Adapter/ADAPTER_FORWARD_GUIDE.md`）：**

- 原生端点：OneBot11、SnowLuma（三级回退：`send_group/private_forward_msg` 专用端点 → `upload_forward_msg`
  取 resid 发 forward 段 → 直发 node 段；SnowLuma API 全面向 NapCat 对齐，适配器可直接连接 NapCat 后端）
- 折叠 HTML `<details>` 卡：云湖（bot/用户协议）、Email、Sandbox、Allons(Ideaura)
- 白名单 HTML / 引用块：Telegram（`<b>`+`<blockquote>`）、Matrix（blockquote 变体，白名单剥离 details/内联样式）
- 平台卡片：Kook（Card header+section）、Discord（Embed fields）
- 官方 Markdown 引用列表：QQBot（官方 md 无折叠语法，服务端校验拒绝无效标签 40034011）
- 不实现（node 段原文输出降级）：OneBot12（标准无 node 段）、WeCom、Terminal、Webhook、WechatMp

**调用方探测示例：**

```python
sends = adapter.list_sends(platform)
if "MergeForward" in sends:
    await adapter.Send.To("group", "123").MergeForward(nodes)
else:
    await adapter.Send.To("group", "123").Text(plain_text)
```

> 参考实现：`ErisPulse-OneBot11Adapter`（专用端点 → `send_msg` 回退）；渲染模板与各适配器任务清单见
> `SDK/Adapter/ADAPTER_FORWARD_GUIDE.md`。

## 3. 平台特有方法命名

**不推荐**在 Send 类中直接添加平台前缀方法。建议使用通用方法名或 `Raw_{协议}` 方法。

**不推荐：**
```python
def YunhuForm(self, form_id: str):  # ❌ 不推荐
    pass

def TelegramSticker(self, sticker_id: str):  # ❌ 不推荐
    pass
```

**推荐：**
```python
def Form(self, form_id: str):  # ✅ 通用方法名
    pass

def Sticker(self, sticker_id: str):  # ✅ 通用方法名
    pass

def Raw_ob12(self, message):  # ✅ 发送 OneBot12 格式
    pass
```

**扩展方法要求**：
- 方法名使用 PascalCase，不加平台前缀
- 必须返回 `asyncio.Task` 对象
- 必须提供完整的类型注解和文档字符串
- 参数设计应尽量与标准方法风格一致

## 4. 参数命名规范

| 参数名 | 说明 | 类型 |
|-------|------|------|
| `text` | 文本内容 | `str` |
| `file` | 媒体内容（URL / 路径 / 二进制，见 §2.1.1） | `str` / `bytes` |
| `filename` | 文件名（`File` 可选，见 §2.1.3） | `str` / `None` |
| `user_id` | 用户 ID | `str` / `int` |
| `group_id` | 群组 ID | `str` / `int` |
| `message_id` | 消息 ID | `str` |
| `data` | 数据对象（如卡片数据） | `dict` |

## 5. 返回值规范

- **发送方法**（如 `Text`, `Image`）：必须返回 `asyncio.Task` 对象
- **修饰方法**（如 `At`, `Reply`, `AtAll`）：必须返回 `self` 以支持链式调用

---

## 6. 反向转换规范（OneBot12 → 平台）

适配器不仅需要将平台原生事件转换为 OneBot12 格式（正向转换），还**必须**提供将 OneBot12 消息段转换回平台原生 API 调用的能力（反向转换）。反向转换的统一入口是 `Raw_ob12` 方法。

### 6.1 转换模型

```
正向转换（接收方向）                反向转换（发送方向）
─────────────────                ─────────────────
平台原生事件                       OneBot12 消息段列表
    │                                  │
    ▼                                  ▼
Converter.convert()               Send.Raw_ob12()
    │                                  │
    ▼                                  ▼
OneBot12 标准事件                  平台原生 API 调用
（含 {platform}_raw）             （返回标准响应格式）
```

**核心对称性**：正向转换保留原始数据在 `{platform}_raw` 中，反向转换接受 OneBot12 标准格式并还原为平台调用。

### 6.2 `Raw_ob12` 实现规范

`Raw_ob12` 接收 OneBot12 标准消息段列表，必须将其转换为平台原生 API 调用。

**方法签名**：

```python
def Raw_ob12(self, message_segments: List[Dict]) -> asyncio.Task:
    """
    发送 OneBot12 标准消息段

    :param message_segments: OneBot12 消息段列表
        [
            {"type": "text", "data": {"text": "Hello"}},
            {"type": "image", "data": {"file": "https://..."}},
            {"type": "mention", "data": {"user_id": "123"}},
        ]
    :return: asyncio.Task，await 后返回标准响应格式
    """
```

**实现要求**：

1. **必须处理所有标准消息段类型**：至少支持 `text`、`image`、`audio`、`video`、`file`、`mention`、`reply`
2. **必须处理平台扩展消息段**：对于 `{platform}_xxx` 类型的消息段，转换为平台对应的原生调用
3. **必须返回标准响应格式**：遵循 [API 响应标准](api-response.md)
4. **不支持的消息段应跳过并记录警告**，不应抛出异常导致整条消息发送失败

### 6.3 消息段转换规则

#### 6.3.1 标准消息段转换

适配器必须实现以下标准消息段的转换：

| OneBot12 消息段 | 转换要求 |
|----------------|---------|
| `text` | 直接使用 `data.text` |
| `image` | `data.file` 按 §2.1 媒体协议处理（三必须形态 + 判定顺序） |
| `audio` | 同 image 处理逻辑 |
| `video` | 同 image 处理逻辑 |
| `file` | 同 image 处理逻辑；文件名按 §2.1.3 推导顺序处理 `data.filename` |
| `mention` | 转换为平台的 @用户 机制（如 Telegram 的 `entities`，云湖的 `at_uid`） |
| `reply` | 转换为平台的回复引用机制 |
| `face` | 转换为平台的表情发送机制，不支持则跳过 |
| `location` | 转换为平台的位置发送机制，不支持则跳过 |

#### 6.3.2 平台扩展消息段转换

对于带平台前缀的消息段，适配器应识别并转换：

```python
def _convert_ob12_segments(self, segments: List[Dict]) -> Any:
    """将 OneBot12 消息段转换为平台原生格式"""
    platform_prefix = f"{self._platform_name}_"
    
    for segment in segments:
        seg_type = segment["type"]
        seg_data = segment["data"]
        
        if seg_type.startswith(platform_prefix):
            # 平台扩展消息段 → 平台原生调用
            self._handle_platform_segment(seg_type, seg_data)
        elif seg_type in self._standard_segment_handlers:
            # 标准消息段 → 平台等价操作
            self._standard_segment_handlers[seg_type](seg_data)
        else:
            # 未知消息段 → 记录警告并跳过
            logger.warning(f"不支持的消息段类型: {seg_type}")
```

#### 6.3.3 复合消息段处理

一条消息可能包含多个消息段，适配器需要正确处理复合消息：

```python
# 模块发送包含文本+图片+@用户 的消息
await send.Raw_ob12([
    {"type": "mention", "data": {"user_id": "123"}},
    {"type": "text", "data": {"text": "你好"}},
    {"type": "image", "data": {"file": "https://example.com/img.jpg"}}
])
```

**处理策略**：
- **优先合并**：如果平台支持在一条消息中同时包含文本、图片、@等，应合并发送
- **退而拆分**：如果平台不支持合并，按顺序拆分为多条消息发送
- **保持顺序**：消息段的发送顺序应与列表顺序一致

### 6.4 `Raw_ob12` 与标准方法的关系

适配器的标准发送方法（`Text`、`Image` 等）**已由 `SendDSL` 基类内置实现并默认委托给 `Raw_ob12`**，适配器子类无需重复实现：

```python
class Send(SendDSL):
    def Raw_ob12(self, message_segments: List[Dict]) -> asyncio.Task:
        """核心实现：OneBot12 消息段 → 平台 API（必须实现）"""
        return asyncio.create_task(self._send_ob12(message_segments))

    # Text/Image/Voice/Video/File 已从基类继承，自动委托 Raw_ob12
    # 如需平台特定逻辑，可覆盖单个方法：
    # def Text(self, text: str) -> asyncio.Task:
    #     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

**好处**：
- 转换逻辑集中在 `Raw_ob12` 一处，减少重复代码
- 标准方法和 `Raw_ob12` 行为完全一致
- 模块无论使用 `Text()` 还是 `Raw_ob12()` 都能得到相同结果
- 基类提供类型签名，IDE 能补全标准方法

### 6.5 实现示例

```python
class YunhuSend(SendDSL):
    """云湖平台 Send 实现"""
    
    def Raw_ob12(self, message_segments: list) -> asyncio.Task:
        """OneBot12 消息段 → 云湖 API 调用"""
        return asyncio.create_task(self._do_send(message_segments))
    
    async def _do_send(self, segments: list) -> dict:
        """实际发送逻辑"""
        # 1. 解析修饰器状态
        at_users = self._at_users or []
        reply_to = self._reply_to
        at_all = self._at_all
        
        # 2. 转换消息段
        yunhu_elements = []
        for seg in segments:
            seg_type = seg["type"]
            seg_data = seg["data"]
            
            if seg_type == "text":
                yunhu_elements.append({"type": "text", "content": seg_data["text"]})
            elif seg_type == "image":
                yunhu_elements.append({"type": "image", "url": seg_data["file"]})
            elif seg_type == "mention":
                at_users.append(seg_data["user_id"])
            elif seg_type == "reply":
                reply_to = seg_data["message_id"]
            elif seg_type == "yunhu_form":
                # 平台扩展消息段
                yunhu_elements.append({"type": "form", "form_id": seg_data["form_id"]})
            else:
                logger.warning(f"云湖不支持的消息段: {seg_type}")
        
        # 3. 调用云湖 API
        response = await self._call_yunhu_api(yunhu_elements, at_users, reply_to, at_all)
        
        # 4. 返回标准响应格式
        return {
            "status": "ok" if response["code"] == 0 else "failed",
            "retcode": response["code"],
            "data": {"message_id": response.get("msg_id", ""), "time": int(time.time())},
            "message_id": response.get("msg_id", ""),
            "message": "",
            "yunhu_raw": response
        }
```

---

## 7. 方法发现

模块开发者可以通过 API 查询适配器支持的发送方法（**不要**在模块中硬编码某平台的方法
清单——各适配器的扩展方法随版本演进，以运行时发现为准）：

```python
from ErisPulse import adapter

# 列出所有发送方法
methods = adapter.list_sends("myplatform")
# ["Batch", "Form", "Image", "Recall", "Sticker", "Text", ...]

# 查看方法详情
info = adapter.send_info("myplatform", "Form")
# {
#     "name": "Form",
#     "parameters": [{"name": "form_id", "type": "str", ...}],
#     "return_type": "Awaitable[Any]",
#     "docstring": "发送云湖表单"
# }
```

---

## 9. 适配器开发注意事项

关于如何正确重写 `BaseAdapter`、`Send`、`Request` 的 `__init__`，详见 [适配器开发入门 - `__init__` 注意事项](../developer-guide/adapters/getting-started.md#init-注意事项)。

---

---

## 10. 适配器实现检查清单

### 发送方法
- [ ] 标准方法（`Text`, `Image` 等）已实现
- [ ] 返回值均为 `asyncio.Task`
- [ ] 修饰方法（`At`, `Reply`, `AtAll`）返回 `self`
- [ ] 平台扩展方法使用 PascalCase，无平台前缀
- [ ] 所有方法有完整的类型注解和文档字符串

### 媒体发送协议
- [ ] `file` 参数**必须形态**全部支持：HTTP(S) URL / 本地路径 / `bytes`（见 §2.1.1）
- [ ] 形态判定顺序符合 §2.1.2（bytes → URL → `file://` → 路径）
- [ ] `File` 的文件名推导顺序符合 §2.1.3（显式 `filename` > URL basename > 路径 basename > 平台默认）
- [ ] 平台的媒体限制（大小 / MIME / 时长）已在适配器文档声明（§2.1.4）
- [ ] 不支持的媒体类型按 §2.1.5 降级阶梯处理：近缘类型降级或返回 `retcode=10002`，不抛异常、不静默丢弃

### 合并转发（可选，见 §2.4）
- [ ] 平台有原生合并转发时，`MergeForward` 走协议专用端点，失败回退 `send_msg`（OneBot11 系）
- [ ] 平台无原生转发但有富文本时，`MergeForward` 渲染为平台折叠形态（HTML 卡 / Card / Embed / blockquote）
- [ ] 两者皆无时**不实现** `MergeForward`，不返回成功却发出 node 字典纯文本
- [ ] `MergeForward` 内部不再调 `Raw_ob12` 转发同样 nodes

### 反向转换
- [ ] `Raw_ob12` **已实现**（必须，不可跳过）
- [ ] `Raw_ob12` 能处理所有标准消息段（`text`, `image`, `audio`, `video`, `file`, `mention`, `reply`）
- [ ] `Raw_ob12` 能处理平台扩展消息段（`{platform}_xxx` 类型）
- [ ] 标准发送方法（`Text`, `Image` 等）内部委托给 `Raw_ob12`，而非独立实现转换逻辑
- [ ] 不支持的消息段跳过并记录警告，不抛出异常
- [ ] 复合消息段正确处理（合并或按序拆分）

---

## 11. 消息构建器（MessageBuilder）——适配器侧须知

`MessageBuilder` 是 ErisPulse 提供的 OneBot12 消息段构建工具，供**模块侧**构建消息：
链式调用（或静态快速构建）最终产出标准消息段列表 `[{"type": ..., "data": ...}]`，
由调用方直接传给 `Raw_ob12`。

**适配器侧只需知道这一点**：`Raw_ob12` 接收到的就是这份产物——与手写的消息段列表
完全同构，按 §6.2 的段分发逻辑处理即可，无需感知它来自 MessageBuilder 还是字面量。

> 完整用法（双模式机制、全部消息段方法、`copy()` / `clear()` 工具方法与示例）见
> [MessageBuilder 详解](../advanced/message-builder.md)，本篇不再重复。

---

## 12. 相关文档

**实现发送返回值时配套对照**：
- [API 响应标准](api-response.md) - 适配器 API 响应格式标准

**同一适配器的其它侧**：
- [事件转换标准](event-conversion.md) - 完整的事件转换规范、扩展命名和消息段标准
- [会话类型标准](session-types.md) - 会话类型定义和映射关系
- [请求操作规范](request-action-spec.md) - 请求事件字段要求、HandleRequest DSL 及适配器实现要求

## API 动作规范

> 来源: `docs/zh-CN/standards/api-action-spec.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-CN/standards/api-action-spec.md）

# ErisPulse API 动作标准

> [!TIP]
> **什么时候需要读这篇**：当你在适配器中实现 Api DSL 标准动作（get_user_info / delete_message 等），或在模块中跨平台调用这些标准动作、需要确认参数与 data 字段时对照本文。不需要则跳过。

本文档定义 ErisPulse 适配器中 **OneBot12 标准 API 动作**的统一接口规范，使模块开发者可以面向标准接口编程，由适配器负责映射到平台原生 API。

> **覆盖范围**：OneBot12 标准动作中，`ApiDSL` 提供用户 / 群组 / 频道（Guild）/
> 消息管理 / 元（Meta）常规接口的强类型方法（`send_message` 由
> `SendDSL.Raw_ob12` 承担）。文件资源动作（`upload_file` / `get_file` / 分片）仅作
> 降级透传保留，见 §3.5 说明。平台扩展动作经 `Api.call("prefix.action", ...)`
> 逃生舱调用。动作参数与返回结构以 OneBot12 规范（仓库内 `onebot/specs/interface/`）为准。

## 1. 设计背景

在 ErisPulse 中，消息段（消息收发）和事件格式已经完全遵循 OneBot12 标准，但 **API 动作调用**（如获取用户信息、获取群列表、撤回消息等）此前未统一——模块开发者必须为每个平台写不同的 `call_api` 调用。

`ApiDSL` 通过提供强类型的标准动作方法，解决这一问题：

```
模块代码（跨平台统一）             适配器实现（平台特定）
─────────────────              ──────────────────
adapter.Api.get_user_info("123")  →  适配器 call_api / 覆盖
adapter.Api.get_group_list()      →  适配器 call_api / 覆盖
adapter.Api.delete_message("id")  →  适配器 call_api / 覆盖
```

## 2. 三层 DSL 并行结构

ErisPulse 适配器有三个并行的 DSL 内部类，各司其职：

```
BaseAdapter
├── Send(SendDSL)       ← 消息发送（Text/Image/Raw_ob12）
├── Request(RequestDSL)  ← 请求操作（accept/reject）
└── Api(ApiDSL)          ← 标准 API 动作（用户/群组/频道/消息管理/文件/元）★
```

| DSL | 职责 | 方法风格 | 返回值 |
|-----|------|---------|--------|
| `Send` | 发送消息 | 链式 + `asyncio.Task` | 标准响应 |
| `Request` | 处理请求事件 | `asyncio.Task` | 标准响应 |
| `Api` | 查询/管理操作 | `async` 方法 | 标准响应 |

## 3. 标准动作列表

### 3.1 用户相关

| 方法 | OB12 动作 | 参数 | data 返回 |
|------|----------|------|----------|
| `get_self_info()` | `get_self_info` | 无 | `user_id`, `user_name`, `user_displayname` |
| `get_user_info(user_id)` | `get_user_info` | `user_id: str` | `user_id`, `user_name`, `user_displayname`, `user_remark` |
| `get_friend_list()` | `get_friend_list` | 无 | `list[get_user_info 响应]` |

### 3.2 群组相关

| 方法 | OB12 动作 | 参数 | data 返回 |
|------|----------|------|----------|
| `get_group_info(group_id)` | `get_group_info` | `group_id: str` | `group_id`, `group_name` |
| `get_group_list()` | `get_group_list` | 无 | `list[get_group_info 响应]` |
| `get_group_member_info(group_id, user_id)` | `get_group_member_info` | `group_id: str`, `user_id: str` | `user_id`, `user_name`, `user_displayname` |
| `get_group_member_list(group_id)` | `get_group_member_list` | `group_id: str` | `list[get_group_member_info 响应]` |
| `set_group_name(group_id, group_name)` | `set_group_name` | `group_id: str`, `group_name: str` | 无 |
| `leave_group(group_id)` | `leave_group` | `group_id: str` | 无 |

### 3.3 消息管理

| 方法 | OB12 动作 | 参数 | 说明 |
|------|----------|------|------|
| `delete_message(message_id)` | `delete_message` | `message_id: str` | 撤回/删除消息 |

> **发送消息**（`send_message`）由 `SendDSL` 的 `Raw_ob12` 处理，不在 `ApiDSL` 中重复。

### 3.4 频道（Guild）相关

OneBot12 频道体系分两级：**频道（guild）** 与 **子频道（channel）**。

| 方法 | OB12 动作 | 参数 | data 返回 |
|------|----------|------|----------|
| `get_guild_info(guild_id)` | `get_guild_info` | `guild_id: str` | `guild_id`, `guild_name` |
| `get_guild_list()` | `get_guild_list` | 无 | `list[get_guild_info 响应]` |
| `set_guild_name(guild_id, guild_name)` | `set_guild_name` | `guild_id: str`, `guild_name: str` | 无 |
| `get_guild_member_info(guild_id, user_id)` | `get_guild_member_info` | `guild_id: str`, `user_id: str` | `user_id`, `user_name`, `user_displayname` |
| `get_guild_member_list(guild_id)` | `get_guild_member_list` | `guild_id: str` | `list[get_guild_member_info 响应]` |
| `leave_guild(guild_id)` | `leave_guild` | `guild_id: str` | 无 |
| `get_channel_info(guild_id, channel_id)` | `get_channel_info` | `guild_id: str`, `channel_id: str` | `channel_id`, `channel_name` |
| `get_channel_list(guild_id, *, joined_only)` | `get_channel_list` | `guild_id: str`, `joined_only: bool=false` | `list[get_channel_info 响应]` |
| `set_channel_name(guild_id, channel_id, channel_name)` | `set_channel_name` | `guild_id`, `channel_id`, `channel_name` | 无 |
| `get_channel_member_info(guild_id, channel_id, user_id)` | `get_channel_member_info` | `guild_id`, `channel_id`, `user_id` | `user_id`, `user_name`, `user_displayname` |
| `get_channel_member_list(guild_id, channel_id)` | `get_channel_member_list` | `guild_id`, `channel_id` | `list[get_channel_member_info 响应]` |
| `leave_channel(guild_id, channel_id)` | `leave_channel` | `guild_id`, `channel_id` | 无 |

> 频道体系与群组（group）彼此独立：Discord / QQ 频道 / Kook 等平台实现频道接口，
> 传统 QQ / 微信实现群组接口，两者可同时存在或仅其一。

### 3.5 文件资源操作

> [!WARNING]
> **文件资源模型（file_id 两段式）在 ErisPulse 属"降级可用"**：
> ErisPulse 的文件收发不走"先上传拿 file_id 再引用"模型——模块发文件用
> `SendDSL.File(file, filename)`（URL / 路径 / 字节**发送时直传**，见
> [发送方法规范](send-method-spec.md)）。
> 本节 `upload_file` / `get_file` / 分片动作依赖平台特有的 `file_id` 文件资源
> 能力，**通用性不足**；仅当适配器后端天然具备该能力时才可透传，框架内置
> 适配器**不实现也不建议实现**，调用时通常返回 `retcode=10002`。
> 模块需要跨平台传文件时，请使用 `SendDSL.File`，勿依赖 file_id。
>
> **展望**：`file_id` 资源模型标准化到框架层是未来的方向，当前版本不提供。

整包传输（小文件）：

| 方法 | OB12 动作 | 参数 | data 返回 |
|------|----------|------|----------|
| `upload_file(*, type, name, ...)` | `upload_file` | `type`, `name`, `url`/`path`/`data`, `headers?`, `sha256?` | `file_id` |
| `get_file(file_id, type)` | `get_file` | `file_id: str`, `type: str` | `name`, `url`/`path`/`data` |

`upload_file` 的 `type` 参数：
- `"url"`：通过 URL 上传（需提供 `url`）
- `"path"`：通过本地路径上传（需提供 `path`）
- `"data"`：通过二进制数据上传（需提供 `data`）

#### 3.5.1 分片传输（大文件，属上述降级范围）

OneBot12 分片动作按 `stage` 区分阶段。`ApiDSL` 将同一动作的三/两阶段拆分为独立方法
（`offset` 为字节偏移，`data` 在 JSON 中为 Base64）；下表仅为查阅保留，
适配器无需也不应强制实现：

**分片上传三步**：`prepare` → `transfer`（循环逐片）→ `finish`

| 方法 | 对应 stage | 参数 | data 返回 |
|------|-----------|------|----------|
| `upload_file_fragmented_prepare(name, total_size)` | `prepare` | `name: str`, `total_size: int` | `file_id`（传输期用） |
| `upload_file_fragmented_transfer(file_id, offset, data)` | `transfer` | `file_id`, `offset: int`, `data: bytes` | 无 |
| `upload_file_fragmented_finish(file_id, sha256)` | `finish` | `file_id`, `sha256: str`（整文件校验） | `file_id` |

```python
total = os.path.getsize(path)
r = await adapter.Api.upload_file_fragmented_prepare(os.path.basename(path), total)
fid = r["data"]["file_id"]
offset = 0
with open(path, "rb") as f:
    while chunk := f.read(65536):
        await adapter.Api.upload_file_fragmented_transfer(fid, offset, chunk)
        offset += len(chunk)
sha256 = hashlib.sha256(open(path, "rb").read()).hexdigest()
await adapter.Api.upload_file_fragmented_finish(fid, sha256)
```

**分片下载两步**：`prepare` → `transfer`（循环取片）

| 方法 | 对应 stage | 参数 | data 返回 |
|------|-----------|------|----------|
| `get_file_fragmented_prepare(file_id)` | `prepare` | `file_id` | `name`, `total_size`, `sha256` |
| `get_file_fragmented_transfer(file_id, offset, size)` | `transfer` | `file_id`, `offset: int`, `size: int` | `data`（本次分片字节） |

### 3.6 元（Meta）动作

元动作不针对具体账号，无需 `Using()` 指定 Bot。

| 方法 | OB12 动作 | 参数 | data 返回 |
|------|----------|------|----------|
| `get_latest_events(limit, timeout)` | `get_latest_events` | `limit: int=0`, `timeout: int=0` | 事件对象数组（不含元事件） |
| `get_supported_actions()` | `get_supported_actions` | 无 | `list[str]` 支持的动作名 |
| `get_status()` | `get_status` | 无 | `good: bool`, `bots: list[{self, online, ...}]` |
| `get_version()` | `get_version` | 无 | `impl`, `version`, `onebot_version` |

### 3.7 通用扩展动作

| 方法 | 说明 |
|------|------|
| `call(action, **params)` | 平台扩展动作的逃生舱，遵循 OB12 扩展命名规则 `{prefix}.{action}` |

## 4. 使用方式

### 4.1 基本调用

```python
from ErisPulse import adapter

# 获取用户信息（跨平台统一）
result = await adapter.myplatform.Api.get_user_info("123456")
if result["status"] == "ok":
    user_name = result["data"]["user_name"]
    print(f"用户名: {user_name}")

# 获取群列表
result = await adapter.myplatform.Api.get_group_list()
groups = result["data"]

# 撤回消息
await adapter.myplatform.Api.delete_message("msg_123456")
```

### 4.2 指定 Bot 账号（多账户模式）

```python
# 使用指定 Bot 账号执行操作
info = await adapter.myplatform.Api.Using("bot1").get_self_info()
```

### 4.3 平台扩展动作

```python
# 调用平台特有的扩展动作（建议使用 {prefix}.{action} 命名）
result = await adapter.telegram.Api.call(
    "telegram.send_sticker",
    sticker_id="CAACAgIAAxkBAA...",
)
```

### 4.4 在事件处理器中使用

```python
from ErisPulse.Core.Event import message

@message()
async def handle(event):
    # 获取发送者详细信息
    user_id = event.get_user_id()
    platform = event.get_platform()

    result = await getattr(adapter, platform).Api.get_user_info(user_id)
    if result["status"] == "ok":
        user_name = result["data"]["user_name"]
        await event.reply(f"你好，{user_name}！")
```

## 5. 适配器实现

### 5.1 默认行为（零配置）

`ApiDSL` 的默认实现将标准动作名作为 `endpoint` 直接传递给 `adapter.call_api()`：

```python
# ApiDSL 默认实现等价于：
async def get_user_info(self, user_id: str) -> dict:
    return await self._adapter.call_api("get_user_info", user_id=user_id, account_id=self._account_id)
```

**适用场景**：当适配器的底层后端自身即遵循 OneBot12 标准动作协议时，
`call_api` 天然支持标准动作名（如直接对接遵循该协议的服务端）。

### 5.2 覆盖标准方法（映射到平台原生 API）

适配器可覆盖单个标准方法，将其映射到平台原生 API：

```python
class MyAdapter(BaseAdapter):

    class Api(BaseAdapter.Api):
        """MyPlatform 标准 API 动作实现"""

        async def get_user_info(self, user_id: str) -> dict:
            # 映射到平台原生 API
            raw = await self._adapter._request("GET", f"/users/{user_id}")
            if raw.get("code") != 0:
                # 平台侧错误：用 341xx～345xx 段自定义低三位（346xx 为框架保留，勿占用）
                return self._adapter.make_error(retcode=34400, message="用户不存在")

            user = raw["data"]
            return self._adapter.make_response(
                data={
                    "user_id": str(user["id"]),
                    "user_name": user.get("nick", ""),
                    "user_displayname": user.get("display_name", ""),
                    "user_remark": user.get("remark", ""),
                },
                raw=raw,
            )

        async def get_friend_list(self) -> dict:
            raw = await self._adapter._request("GET", "/friends")
            friends = [
                {
                    "user_id": str(u["id"]),
                    "user_name": u.get("nick", ""),
                    "user_displayname": u.get("display_name", ""),
                    "user_remark": u.get("remark", ""),
                }
                for u in raw.get("data", [])
            ]
            return self._adapter.make_response(data=friends, raw=raw)
```

### 5.3 未支持的动作

适配器未覆盖的标准方法走默认实现（委托给 `call_api`）。如果 `call_api` 也不支持该动作，应返回标准错误响应：

```python
async def call_api(self, endpoint: str, **params):
    if endpoint not in self._supported_endpoints:
        return self.make_error(retcode=10002, message=f"不支持的动作: {endpoint}")
    # ... 平台 API 调用
```

模块开发者可通过返回值的 `retcode` 判断是否支持：

```python
result = await adapter.myplatform.Api.get_friend_list()
if result["retcode"] == 10002:
    print("该平台不支持获取好友列表")
```

## 6. 响应格式

所有 `ApiDSL` 方法返回标准 API 响应格式（详见 [API 响应标准](api-response.md)）：

```json
{
    "status": "ok",
    "retcode": 0,
    "data": { ... },
    "message_id": "",
    "message": "",
    "myplatform_raw": { ... }
}
```

> **注意**：信息查询类动作的 `message_id` 为空字符串（仅消息发送类动作才有 `message_id`）。

## 7. 与 SendDSL / RequestDSL 的关系

| 场景 | 使用 DSL | 示例 |
|------|---------|------|
| 发送消息 | `Send` | `adapter.Send.To("group", "123").Text("hi")` |
| 同意/拒绝请求 | `Request` | `adapter.Request("req_id").accept()` |
| 获取用户/群信息 | `Api` | `adapter.Api.get_user_info("123")` |
| 撤回消息 | `Api` | `adapter.Api.delete_message("msg_id")` |
| 退出群 | `Api` | `adapter.Api.leave_group("group_id")` |

## 8. 适配器实现检查清单

### 标准动作
- [ ] `call_api` 能处理标准动作名（或覆盖对应 `ApiDSL` 方法）
- [ ] 不支持的动作返回 `retcode=10002`
- [ ] 返回值遵循标准 API 响应格式
- [ ] `data` 字段包含 OB12 标准定义的字段
- [ ] 频道平台需实现 `get_guild_*` / `get_channel_*` / `leave_guild` / `leave_channel`
- [ ] 元动作（`get_status` / `get_version` / `get_supported_actions`）建议实现
- [ ] **文件收发用 `SendDSL.File`（直传）**；文件资源动作（upload_file/get_file/分片）**不强制实现**，仅当后端具备 `file_id` 资源能力时才需透传

### 扩展动作
- [ ] 平台扩展动作使用 `{prefix}.{action}` 命名
- [ ] 扩展动作的参数和响应仍遵循 OB12 动作请求/响应结构

## 9. 相关文档

**实现 Api DSL 返回值时配套对照**：
- [API 响应标准](api-response.md) - 适配器 API 响应格式标准

**同一适配器的其它 DSL**：
- [发送方法规范](send-method-spec.md) - Send 类的方法命名和参数规范
- [请求操作规范](request-action-spec.md) - Request DSL 的使用方式

**事件侧配套**：
- [事件转换标准](event-conversion.md) - 事件格式和消息段标准

## API 响应规范

> 来源: `docs/zh-CN/standards/api-response.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-CN/standards/api-response.md）

# ErisPulse 适配器标准化返回规范

> [!TIP]
> **什么时候需要读这篇**：当你在适配器中实现 `call_api` / Send / Request 的返回值，需要确认响应结构与返回码是否符合 ErisPulse 标准，或排查某个 `retcode` 的含义时对照本文。不需要则跳过。

## 1. 说明
为什么会有这个规范？

为了确保各平台发送接口返回统一性与OneBot12兼容性，ErisPulse适配器在API响应格式上采用了OneBot12定义的消息发送返回结构标准。

但ErisPulse的协议有一些特殊性定义:
- 1. 基础字段中，message_id是必须的，但OneBot12标准中无此字段
- 2. 返回内容中需要添加 {platform_name}_raw 字段，用于存放原始响应数据

## 2. 基础返回结构
所有动作响应必须包含以下基础字段：

| 字段名 | 数据类型 | 必选 | 说明 |
|-------|---------|------|------|
| status | string | 是 | 执行状态，必须是"ok"或"failed" |
| retcode | int64 | 是 | 返回码，遵循OneBot12返回码规则 |
| data | any | 是 | 响应数据，成功时包含请求结果，失败时为null |
| message_id | string | 是 | 消息ID，用于标识消息, 没有则为空字符串 |
| message | string | 是 | 错误信息，成功时为空字符串 |
| {platform_name}_raw | any | 否 | 原始响应数据 |

可选字段：
| 字段名 | 数据类型 | 必选 | 说明 |
|-------|---------|------|------|
| echo | string | 否 | 当请求中包含echo字段时，原样返回 |

## 3. 完整字段规范

### 3.1 通用字段

#### 成功响应示例
```json
{
    "status": "ok",
    "retcode": 0,
    "data": {
        "message_id": "1234",
        "time": 1632847927.599013
    },
    "message_id": "1234",
    "message": "",
    "echo": "1234",
    "telegram_raw": {...}
}
```

#### 失败响应示例
```json
{
    "status": "failed",
    "retcode": 10003,
    "data": null,
    "message_id": "",
    "message": "缺少必要参数: user_id",
    "echo": "1234",
    "telegram_raw": {...}
}
```

### 3.2 返回码规范

#### 0 成功（OK）
- 0: 成功（OK）

#### 1xxxx 动作请求错误（Request Error）
| 错误码 | 错误名 | 说明 |
|-------|-------|------|
| 10001 | Bad Request | 无效的动作请求 |
| 10002 | Unsupported Action | 不支持的动作请求 |
| 10003 | Bad Param | 无效的动作请求参数 |
| 10004 | Unsupported Param | 不支持的动作请求参数 |
| 10005 | Unsupported Segment | 不支持的消息段类型 |
| 10006 | Bad Segment Data | 无效的消息段参数 |
| 10007 | Unsupported Segment Data | 不支持的消息段参数 |
| 10101 | Who Am I | 未指定机器人账号 |
| 10102 | Unknown Self | 未知的机器人账号 |

#### 2xxxx 动作处理器错误（Handler Error）
| 错误码 | 错误名 | 说明 |
|-------|-------|------|
| 20001 | Bad Handler | 动作处理器实现错误 |
| 20002 | Internal Handler Error | 动作处理器运行时抛出异常 |

#### 3xxxx 动作执行错误（Execution Error）
| 错误码范围 | 错误类型 | 说明 |
|-----------|---------|------|
| 31xxx | Database Error | 数据库错误 |
| 32xxx | Filesystem Error | 文件系统错误 |
| 33xxx | Network Error | 网络错误 |
| 34xxx | Platform Error | 机器人平台错误 |
| 35xxx | Logic Error | 动作逻辑错误 |
| 36xxx | I Am Tired | 实现决定罢工 |

#### 保留错误段
- 4xxxx、5xxxx: 保留段，不应使用
- 6xxxx～9xxxx: 其他错误段，供实现自定义使用

## 4. 实现要求
1. 所有响应必须包含status、retcode、data和message字段
2. 当请求中包含非空echo字段时，响应必须包含相同值的echo字段
3. 返回码必须严格遵循OneBot12规范
4. 错误信息(message)应当是人类可读的描述

## 5. 扩展规范

ErisPulse 在 OneBot12 标准返回结构之上做了以下扩展：

### 5.1 `message_id` 必选字段

OneBot12 标准中 `message_id` 位于 `data` 对象内部且非强制。ErisPulse 将其提升为顶层**必选**字段：

- 无法获取 `message_id` 时应设为空字符串 `""`
- 确保 `message_id` 始终存在，模块无需做 null 检查

### 5.2 `{platform}_raw` 原始响应字段

返回值中应包含 `{platform}_raw` 字段，存放平台原始响应数据的完整副本：

```json
{
    "status": "ok",
    "retcode": 0,
    "data": {"message_id": "1234", "time": 1632847927},
    "message_id": "1234",
    "message": "",
    "telegram_raw": {
        "ok": true,
        "result": {"message_id": 1234, "date": 1632847927, ...}
    }
}
```

**要求**：
- `{platform}_raw` 必须是原始响应的深拷贝，而非引用
- `platform` 必须与适配器注册时的平台名完全一致（大小写敏感）
- 原始响应中的错误信息也应保留，便于调试

### 5.3 框架扩展返回码（34xxx 平台错误段的低三位自定义）

OneBot12 规范允许实现自定义 `3xxxx` 的低三位。`34xxx` 语义为 **Platform Error**
（机器人平台错误，如平台限制导致失败）。`34xxx` 内部按职责分层使用：

| 低三位段 | 归属 | 用途 |
|---------|------|------|
| `340xx` | 适配器实现 | 请求操作族（Request Not Found / Already Handled / Not Supported / Permission Denied，见 request-action-spec §7） |
| `341xx`～`345xx` | 适配器实现 | 平台侧权限 / 风控 / 账号限制等错误（实现自定低三位，原始错误放 `{platform}_raw`） |
| `346xx` | **ErisPulse 框架（保留）** | 框架自身拦截与通用失败，适配器/模块请勿占用 |
| `347xx`～`349xx` | 适配器实现 | 其它平台执行错误 |

ErisPulse 框架当前使用的 `346xx` 码：

| 错误码 | 错误名 | 说明 |
|-------|-------|------|
| 34600 | SDK Failure | 框架通用失败（`make_error()` 默认返回码） |
| 34601 | Action Denied | 出站动作被作用域禁用（`scope.actions`），调用未发起，直接返回该响应 |

> 职责区分：`34601` 是**框架在调用前拦截**（模块根本没资格发起动作）；
> `34004` / `34xxx` 平台码是**动作已发出但平台拒绝**（如 Bot 无权限、被风控）。
> 模块判断权限问题时同时检查这两种：先看 `34601`（自己模块被 scope 禁），
> 再看 `34xxx`（平台侧限制）。

返回结构为 §2 标准失败响应：

```json
{
    "status": "failed",
    "retcode": 34601,
    "data": null,
    "message_id": "",
    "message": "action 'send' denied by scope.actions"
}
```

### 5.4 适配器实现检查清单

- [ ] 包含 `status`, `retcode`, `data`, `message_id`, `message` 字段
- [ ] 返回码遵循 OneBot12 规范（详见 §3.2）
- [ ] `message_id` 始终存在（无法获取时为空字符串）
- [ ] `{platform}_raw` 包含平台原始响应数据

## 6. 注意事项
- 对于3xxxx错误码，低三位可由实现自行定义
- 避免使用保留错误段(4xxxx、5xxxx)
- **`34600` / `34601` 为 ErisPulse 框架保留码**（见 §5.3），适配器/模块避免使用
- 错误信息应当简洁明了，便于调试

---

## 请求动作规范

> 来源: `docs/zh-CN/standards/request-action-spec.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-CN/standards/request-action-spec.md）

# ErisPulse 请求操作规范

> [!TIP]
> **什么时候需要读这篇**：当你的适配器需要处理好友请求/群邀请（转换请求事件、实现 `accept`/`reject`），或模块中要用 `event.approve()` / `event.reject()` 审批请求时对照本文。不需要则跳过。

本文档定义了 ErisPulse 适配器中请求事件操作的标准化规范，包括请求事件的字段要求、Request DSL 的使用方式和适配器实现要求。

## 1. 概述

请求事件（`type: "request"`）是 OneBot12 标准中定义的特殊事件类型，代表需要 Bot 做出决策的请求（如好友请求、群邀请等）。

与消息事件不同，请求事件需要**双向交互**：
1. **接收**：适配器将平台原生请求转换为标准请求事件
2. **响应**：模块通过 `Request` DSL 或 `Event.approve()`/`Event.reject()` 执行操作

```
平台原生请求事件
    │
    ▼
Converter.convert()        ← 适配器实现（正向转换）
    │
    ▼
标准请求事件 (含 request_id)
    │
    ├─→ 模块处理器 @request.on_friend_request()
    │       │
    │       ├─→ event.approve()     ← 同意请求
    │       └─→ event.reject()      ← 拒绝请求
    │               │
    │               ▼
    │       adapter.Request(request_id).accept()
    │               │
    │               ▼
    │       BaseAdapter.Request.accept()  ← 适配器重写
    │               │
    │               ▼
    │       平台 API 调用
    │
    └─→ 或直接通过适配器操作
            await adapter.Request("req_id").accept()
```

## 2. 请求事件字段要求

### 2.1 标准字段

请求事件除必须包含 OneBot12 标准字段外，还需包含以下字段：

| 字段 | 类型 | 必选 | 说明 |
|------|------|------|------|
| `request_id` | string | **强烈推荐** | 请求标识符，用于同意/拒绝操作 |
| `user_id` | string | 是 | 请求发起者ID |
| `user_nickname` | string | 否 | 请求发起者昵称 |
| `comment` | string | 否 | 请求附言 |

### 2.2 `request_id` 字段

`request_id` 是请求操作的核心标识符：

- **用途**：标识一个可操作的请求，供 `Request` DSL 使用
- **生成规则**：
  - 优先使用平台原生的请求标识（如 OneBot11 的 `flag` 字段、Telegram 的 `chat_invite_link` 等）
  - 如果平台没有原生请求ID，适配器应生成一个唯一标识（建议格式：`{platform}_{timestamp}_{user_id}`）
- **唯一性**：在同一平台范围内应保持唯一
- **缺失行为**：当 `request_id` 缺失时，`event.approve()` / `event.reject()` 将抛出 `ValueError`

### 2.3 请求事件示例

```json
{
  "id": "evt_123456",
  "time": 1752241225,
  "type": "request",
  "detail_type": "friend",
  "platform": "onebot11",
  "self": {
    "platform": "onebot11",
    "user_id": "bot_123"
  },
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "comment": "请加好友",
  "request_id": "flag_abc123",
  "onebot11_raw": {...},
  "onebot11_raw_type": "request"
}
```

## 3. Request DSL

### 3.1 链式调用

`Request` 提供与 `Send` 风格一致的链式调用接口：

```python
# 基本用法
await adapter.Request("req_id").accept()
await adapter.Request("req_id").reject()

# 指定 Bot 账号
await adapter.Request("req_id").Using("bot1").accept()

# 附带备注（通过 kwargs）
await adapter.Request("req_id").accept(comment="欢迎")
await adapter.Request("req_id").reject(comment="暂不添加")

# 组合使用
await adapter.Request("req_id").Using("bot1").accept(comment="欢迎")
```

### 3.2 方法列表

| 方法 | 说明 | 返回值 |
|------|------|--------|
| `Using(account_id)` | 指定执行操作的 Bot 账号 | `RequestDSL`（支持链式调用） |
| `accept(**kwargs)` | 同意请求 | `asyncio.Task`（await 后返回标准响应） |
| `reject(**kwargs)` | 拒绝请求 | `asyncio.Task`（await 后返回标准响应） |

### 3.3 返回值格式

操作返回标准 API 响应格式：

**成功**：
```json
{
    "status": "ok",
    "retcode": 0,
    "data": null,
    "message_id": "",
    "message": ""
}
```

**失败**：
```json
{
    "status": "failed",
    "retcode": 34001,
    "data": null,
    "message_id": "",
    "message": "请求已过期或不存在"
}
```

**未实现**（适配器未重写 `accept`/`reject`）：
```json
{
    "status": "failed",
    "retcode": 10002,
    "data": null,
    "message_id": "",
    "message": "平台 MyAdapter 未实现请求操作 (accept)"
}
```

## 4. Event 便捷方法

`Event` 包装类提供了便捷方法，适合在请求事件处理器中使用：

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    # 检查请求ID
    request_id = event.get_request_id()
    if not request_id:
        print("警告：请求事件缺少 request_id")
        return
    
    # 同意请求
    result = await event.approve()
    
    # 或拒绝请求
    # result = await event.reject(comment="暂不添加好友")
    
    # 检查结果
    if result.get("status") == "ok":
        print("操作成功")
    else:
        print(f"操作失败: {result.get('message')}")
```

### 4.1 Event 方法列表

| 方法 | 说明 | 返回值 |
|------|------|--------|
| `get_request_id()` | 获取请求ID | `str` |
| `approve(comment=None)` | 同意当前请求事件 | 标准响应格式 |
| `reject(comment=None)` | 拒绝当前请求事件 | 标准响应格式 |

## 5. 适配器实现要求

### 5.1 转换器要求

适配器的转换器在转换请求事件时，**必须**正确设置 `request_id` 字段：

```python
def convert_request_event(self, raw_event: dict) -> dict:
    """转换平台原生请求事件"""
    return {
        "id": self._generate_event_id(raw_event),
        "time": int(time.time()),
        "type": "request",
        "detail_type": self._map_request_type(raw_event),  # "friend" 或 "group"
        "platform": self._platform_name,
        "self": {
            "platform": self._platform_name,
            "user_id": str(self._bot_id),
        },
        "user_id": str(raw_event.get("user_id", "")),
        "user_nickname": raw_event.get("nickname", ""),
        "comment": raw_event.get("message", ""),
        "request_id": self._extract_request_id(raw_event),  # ← 关键字段
        f"{self._platform_name}_raw": raw_event,
        f"{self._platform_name}_raw_type": raw_event.get("type", ""),
    }

def _extract_request_id(self, raw_event: dict) -> str:
    """
    从平台原生事件提取请求ID
    
    优先使用平台原生的请求标识，若无则生成唯一ID
    """
    # 优先使用平台原生ID
    if flag := raw_event.get("flag"):
        return str(flag)
    if request_key := raw_event.get("request_key"):
        return str(request_key)
    
    # 兜底：生成唯一ID
    import hashlib
    raw = f"{self._platform_name}_{raw_event.get('user_id')}_{raw_event.get('timestamp')}"
    return hashlib.md5(raw.encode()).hexdigest()
```

### 5.2 Request 内部类实现

适配器在 `Request` 内部类中重写 `accept` 和 `reject` 即可：

```python
from ErisPulse.Core import BaseAdapter, RequestDSL

class MyAdapter(BaseAdapter):
    
    class Request(RequestDSL):
        """MyPlatform 请求操作实现"""
        
        def accept(self, **kwargs):
            """
            同意请求
            
            :param kwargs: 扩展参数，如 comment="备注"
            :return: asyncio.Task
            """
            async def _do():
                try:
                    result = await self._adapter.call_api(
                        endpoint="/set_request",
                        request_id=self._request_id,
                        approve=True,
                        **kwargs,
                    )
                    return {
                        "status": "ok" if result.get("code") == 0 else "failed",
                        "retcode": result.get("code", 0),
                        "data": None,
                        "message_id": "",
                        "message": result.get("message", ""),
                    }
                except Exception as e:
                    return {
                        "status": "failed",
                        "retcode": 34001,
                        "data": None,
                        "message_id": "",
                        "message": f"请求操作失败: {e}",
                    }
            
            return self._create_task(_do())
        
        def reject(self, **kwargs):
            """拒绝请求"""
            async def _do():
                try:
                    result = await self._adapter.call_api(
                        endpoint="/set_request",
                        request_id=self._request_id,
                        approve=False,
                        **kwargs,
                    )
                    return {
                        "status": "ok" if result.get("code") == 0 else "failed",
                        "retcode": result.get("code", 0),
                        "data": None,
                        "message_id": "",
                        "message": result.get("message", ""),
                    }
                except Exception as e:
                    return {
                        "status": "failed",
                        "retcode": 34001,
                        "data": None,
                        "message_id": "",
                        "message": f"请求操作失败: {e}",
                    }
            
            return self._create_task(_do())
```

### 5.3 平台不支持请求操作

如果平台本身不支持好友请求/群邀请操作（如某些平台自动处理请求），适配器可以：

1. **不重写 `Request` 内部类**：使用基类默认实现，调用 `accept()`/`reject()` 时返回 `retcode=10002`
2. **在转换时跳过 `request_id`**：不生成 `request_id`，让 `event.approve()` 抛出 `ValueError`
3. **记录日志**：在 `accept`/`reject` 中记录警告并返回适当错误码

### 5.4 总结：Send 与 Request 并行

适配器有两个并行的 DSL 内部类，各司其职：

```
BaseAdapter
├── Send(SendDSL)     ← 消息发送
│   ├── Raw_ob12()    ← 必须实现
│   ├── Text()        ← 推荐实现
│   └── Image()       ← 按需实现
│
└── Request(RequestDSL) ← 请求操作
    ├── accept()        ← 按需实现
    └── reject()        ← 按需实现
```

### 5.5 适配器 `__init__` 注意事项

重写 `Request` 内部类的 `__init__` 时，必须透传参数并调用 `super().__init__()`，详见 [适配器开发入门 - `__init__` 注意事项](../developer-guide/adapters/getting-started.md#init-注意事项)（`Request` 同理，参数为 `adapter, request_id, account_id`）。

## 6. 适配器实现检查清单

### 基础要求
- [ ] 若重写了 `__init__`，已调用 `super().__init__()`（确保 Send / Request 工厂初始化）

### 请求事件转换
- [ ] 请求事件包含 `request_id` 字段（强烈推荐）
- [ ] `detail_type` 正确映射为 `"friend"` 或 `"group"`
- [ ] 保留平台原始数据在 `{platform}_raw` 字段中
- [ ] `request_id` 生成规则有文档说明

### 请求操作
- [ ] `Request` 内部类已实现（如平台支持请求操作）
- [ ] `accept()` 方法已实现
- [ ] `reject()` 方法已实现
- [ ] 操作返回标准 API 响应格式
- [ ] 不支持的操作返回 `retcode=10002`
- [ ] 网络错误返回 `retcode=33xxx`（遵循 API 响应标准）

## 7. 错误码扩展

请求操作相关的**适配器实现层**推荐错误码（遵循 [API 响应标准](api-response.md) §3.2，
落在 `34xxx` 平台错误段的低三位自定义）：

| 错误码 | 错误名 | 说明 |
|-------|-------|------|
| 34001 | Request Not Found | 请求不存在或已过期 |
| 34002 | Request Already Handled | 请求已被处理 |
| 34003 | Request Not Supported | 平台不支持该类型的请求操作 |
| 34004 | Permission Denied | Bot 无权处理此请求（平台返回） |

> **与框架码的边界**：以上 `340xx` 是**平台/适配器**返回的请求处理失败；
> ErisPulse 框架在 `scope.actions` 禁用某模块的 request 动作时，**在调用适配器之前**
> 直接返回 `34601`（Action Denied，见 [API 响应标准 §5.3](api-response.md#53-框架扩展返回码34xxx-平台错误段的低三位自定义)），
> 两者互不替代：先过 `34601` 框架闸口，再落到平台层 `340xx` 错误。

## 8. 相关文档

**实现请求操作时配套对照**：
- [事件转换标准](event-conversion.md) - 完整的事件转换规范（含 `request_id` 字段要求）
- [API 响应标准](api-response.md) - 适配器 API 响应格式标准（操作返回值与错误码）

**同一适配器的其它 DSL**：
- [发送方法规范](send-method-spec.md) - Send 类的方法命名和参数规范
- [会话类型标准](session-types.md) - 会话类型定义和映射关系
