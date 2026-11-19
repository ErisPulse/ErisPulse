# 文档翻译工作流

本文档介绍 ErisPulse 文档翻译系统的使用方法，包括自动翻译和人工审查反馈机制。

## 快速开始

```bash
# 翻译所有目标语言
python scripts/tools/translate-docs.py

# 只翻译到英语
python scripts/tools/translate-docs.py --lang en

# 强制重新翻译（忽略缓存）
python scripts/tools/translate-docs.py --force
```

## 目录结构

翻译系统的数据存储在 `.github/` 目录下，不会污染文档源码：

```
.github/
├── .translate_cache/              # 翻译缓存（按语言分级）
│   ├── en/                       # 英文翻译缓存
│   │   ├── README.md.cache
│   │   ├── quick-start.md.cache
│   │   └── getting-started/
│   │       └── first-bot.md.cache
│   └── zh-TW/                    # 繁中翻译缓存
│       └── ...
└── .translate_notes/              # 人工审查备注（按语言分级）
    ├── en/                       # 英文审查备注
    │   ├── README.md.notes.json
    │   └── getting-started/
    │       └── first-bot.md.notes.json
    └── zh-TW/                    # 繁中审查备注
        └── ...
```

### 缓存文件 (`.cache`)

每个源文档在每个目标语言下有一个缓存文件，记录源文档的哈希值。当源文档未变化时跳过翻译，变化时自动重新翻译。

> 缓存文件由系统自动管理，一般不需要手动操作。如需强制重新翻译，使用 `--force` 参数。

### 审查备注文件 (`.notes.json`)

每个源文档在每个目标语言下可以有一个审查备注文件，**这是人工审查反馈的核心机制**。

## 人工审查工作流

### 第一步：运行翻译

```bash
python scripts/tools/translate-docs.py --lang en
```

翻译完成后，检查 `docs/en/` 下的翻译结果。

### 第二步：人工审查翻译

对比源文档 `docs/zh-CN/xxx.md` 和翻译结果 `docs/en/xxx.md`，找出问题。

常见问题类型：
- **术语错误**：如 "云湖" 被错误翻译为 "CloudVine" 而非 "Yunhu"
- **不该翻译的内容**: 如硬编码的 1:emoji 等内容
- **路径未替换**：`docs/zh-CN/` 链接没有改为 `docs/en/`
- **用词不一致**：同一个术语在不同文档中翻译不同
- **格式错误**：Markdown 代码块语言标识被改变

### 第三步：手动修正翻译文件

直接编辑 `docs/en/xxx.md` 修正问题。

### 第四步：记录审查备注 ⭐

**这是关键步骤** — 将发现的问题记录到审查备注文件中，确保下次翻译不再犯同样的错误。

在 `.github/.translate_notes/{语言代码}/` 下创建备注文件，文件名与源文档路径对应：

#### 文件命名规则

| 源文档 | 目标语言 | 审查备注文件路径 |
|--------|----------|------------------|
| `README.md` | `en` | `.github/.translate_notes/en/README.md.notes.json` |
| `docs/zh-CN/quick-start.md` | `en` | `.github/.translate_notes/en/quick-start.md.notes.json` |
| `docs/zh-CN/getting-started/first-bot.md` | `zh-TW` | `.github/.translate_notes/zh-TW/getting-started/first-bot.md.notes.json` |

规则：取源文档相对于 `docs/zh-CN/` 的路径，加上 `.notes.json` 后缀。根目录 `README.md` 直接使用 `README.md.notes.json`。

#### 文件格式

```json
[
  "备注内容1",
  "备注内容2",
  "备注内容3"
]
```

就是一个纯字符串数组，每条备注简洁明了地描述问题和正确做法。

#### 示例

`.github/.translate_notes/en/README.md.notes.json`：
```json
[
  "Translate `云湖` platform name as `Yunhu` and do not translate it literally.",
]
```

`.github/.translate_notes/zh-TW/getting-started/first-bot.md.notes.json`：
```json
[
  "懒加载→延遲載入（不要翻譯為「懶載入」）",
  "命令→指令",
  "代码块中的中文不要翻译"
]
```

### 第五步：下次翻译自动生效

当源文档更新需要重新翻译时，翻译器会：
1. 自动加载该文档对应语言的审查备注
2. 将备注以 **⚠️ 人工审查备注（必须严格遵守）** 的形式注入到提示词中
3. 同时加载已有的翻译作为参考，确保术语和风格一致性

输出示例：
```
  [翻译] README.md -> en
    📋 已加载 3 条审查备注
    📖 已加载参考翻译 (2048 字符)
    📝 [推理过程]
    ...AI 推理...
    📄 [翻译结果]
    ...翻译内容...
  [完成] README.md
```

## 备注编写技巧

### ✅ 好的备注

```json
[
  "懒加载→延遲載入（不要翻譯為「懶載入」）",
  "代码块中的中文注释和字符串不要翻译，保持原样",
  "文档内部链接路径 docs/zh-CN/ 必须替换为 docs/zh-TW/"
]
```

- 具体明确，直接给出正确翻译
- 包含反面例子（"不要翻译为xxx"）
- 涵盖具体的转换规则

### ❌ 不好的备注

```json
[
  "注意翻译质量",
  "检查术语",
  "保持一致性"
]
```

- 太笼统，AI 无法理解具体要求
- 没有给出明确的正确做法

## 参考翻译机制

除了审查备注，翻译器还会自动加载 `docs/{目标语言}/` 下已有的翻译文件作为参考。这确保了：

- **术语一致性**：同一术语在不同文档中使用相同翻译
- **风格一致性**：翻译风格保持统一
- **增量更新友好**：源文档部分更新时，未更新部分保持原有翻译风格

> 注意：参考翻译不会强制覆盖，AI 会以源文档为准，但在术语和风格上与参考保持一致。

## 调试模式

设置环境变量 `DEBUG_TRANSLATE` 可以查看详细的加载信息：

```bash
$env:DEBUG_TRANSLATE="1"
python scripts/tools/translate-docs.py --lang en
```

会显示：
- 缓存文件路径和哈希比较
- 审查备注文件的加载情况
- 参考翻译文件的加载情况

## 配置

翻译配置文件：`scripts/tools/translate-config.json`

```json
{
  "source_lang": "zh-CN",
  "target_langs": ["zh-TW", "en"],
  "api_key_env": "OPENAI_API_KEY",
  "base_url": "https://api.openai.com/v1",
  "model": "gpt-4",
  "concurrent": 5,
  "cache_dir": ".github/.translate_cache"
}