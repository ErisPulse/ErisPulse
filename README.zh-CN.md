[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | [Русский](README.ru.md)

# ErisPulse 文档产物分支

由 CI 自动生成，每次文档管线运行后强推覆盖。分支始终只有一个提交，保存最新构建结果，没有可浏览的历史。

## 内容

- `docs/<lang>/` — `zh-CN / en / zh-TW / ja / ru` 五语言的完整文档树
- `docs/<lang>/ai-support/prompts/` — 合并式 AI 物料（`ErisPulse-ModuleDev.md`、`ErisPulse-AdapterDev.md`、`ErisPulse-Full.md`）
- `docs/<lang>/ai-support/skills.zip` — 文档全集包：全部文档原文 + README 索引（逐篇标注「什么时候需要读这篇」）

## 获取文件

- 官网下载卡：<https://www.erisdev.com>
- 直链：`https://raw.githubusercontent.com/ErisPulse/ErisPulse/docs-generated/docs/<lang>/ai-support/...`

## 说明

- 请勿向此分支提 PR；源文档在 `Develop/v2`
- 由 `python -m scripts.tools gen ...` 构建，提交者为 `erispulse[bot]`
