[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | [Русский](README.ru.md)

# ErisPulse 文檔產物分支

由 CI 自動生成，每次文件管線運行後強推覆蓋。分支始終只有一個提交，保存最新構建結果，沒有可瀏覽的歷史。

## 內容

- `docs/<lang>/` — `zh-CN / en / zh-TW / ja / ru` 五語言的完整文檔樹
- `docs/<lang>/ai-support/prompts/` — 合併式 AI 物料（`ErisPulse-ModuleDev.md`、`ErisPulse-AdapterDev.md`、`ErisPulse-Full.md`）
- `docs/<lang>/ai-support/skills.zip` — 文檔全集包：全部文檔原文 + README 索引（逐篇標註「什麼時候需要讀這篇」）

## 取得文件

- 官網下載卡：<https://www.erisdev.com>
- 直鏈：`https://raw.githubusercontent.com/ErisPulse/ErisPulse/docs-generated/docs/<lang>/ai-support/...`

## 說明

- 請勿向此分支提 PR；源文檔在 `Develop/v2`
- 由 `python -m scripts.tools gen ...` 構建，提交者為 `erispulse[bot]`
