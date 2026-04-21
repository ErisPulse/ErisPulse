<div align="center">

[English](README.en.md) | [简体中文](README.md) | [繁體中文](README.zh-TW.md)

</div>

<table>
<tr>
<td width="35%" valign="middle" align="center">
<img src=".github/assets/erispulse_logo_1024.png" width="280" alt="ErisPulse" />
</td>
<td width="65%" valign="middle">

# ErisPulse

**事件驅動的多平台機器人開發框架**

[![PyPI](https://img.shields.io/pypi/v/ErisPulse?style=flat-square)](https://pypi.org/project/ErisPulse/)
[![Python Versions](https://img.shields.io/pypi/pyversions/ErisPulse?style=flat-square)](https://pypi.org/project/ErisPulse/)
[![Docker Pulls](https://img.shields.io/docker/pulls/erispulse/erispulse?style=flat-square&logo=docker&label=pulls)](https://hub.docker.com/r/erispulse/erispulse)
[![Docker Pulls](https://img.shields.io/docker/pulls/wsu2059/erispulse?style=flat-square&logo=docker&label=pulls)](https://hub.docker.com/r/wsu2059/erispulse)
[![Docker Version](https://img.shields.io/docker/v/erispulse/erispulse?style=flat-square&logo=docker&label=docker)](https://hub.docker.com/r/erispulse/erispulse)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

</td>
</tr>
</table>

---

## 簡介

ErisPulse 是一個基於 Python 的事件驅動型多平台機器人開發框架。透過統一的 OneBot12 標準介面，您可以一次編寫代碼，同時在雲湖、Telegram、OneBot 等多個平台部署相同功能的機器人。框架提供靈活的模組(`插件`)系統、熱重載支援和完整的開發者工具鏈，適用於從簡單聊天機器人到複雜自動化系統的各種場景。

## 核心特性

- **事件驅動架構** - 基於 OneBot12 標準的清晰事件模型
- **跨平台相容** - 插件模組編寫一次即可在所有平台使用
- **模組化設計** - 靈活的插件系統，易於擴展和整合
- **熱重載支援** - 開發時無需重啟即可重新載入代碼
- **完整工具鏈** - 提供 CLI 工具、套件管理和自動化腳本

## 快速開始

### 使用 Docker (推薦)

```bash
docker pull erispulse/erispulse:latest
```

<details>
<summary>快速啟動</summary>

```bash
# 下載 docker-compose.yml
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# 設定 Dashboard 登入令牌並啟動
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

> 鏡像內建 ErisPulse 框架和 Dashboard 管理面板，支援 `linux/amd64` 和 `linux/arm64` 架構。

</details>

啟動後訪問 `http