[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | [Русский](README.ru.md)

# ErisPulse ドキュメント配布ブランチ

CI が自動生成し、ドキュメントパイプラインの実行ごとに強制プッシュで上書きします。このブランチは常に最新ビルドの単一コミットのみを保持し、閲覧可能な履歴はありません。

## 内容

- `docs/<lang>/` — `zh-CN / en / zh-TW / ja / ru` 各言語の完全なドキュメントツリー
- `docs/<lang>/ai-support/prompts/` — 統合型 AI 素材（`ErisPulse-ModuleDev.md`、`ErisPulse-AdapterDev.md`、`ErisPulse-Full.md`）
- `docs/<lang>/ai-support/skills.zip` — ドキュメントパック：全ドキュメントの原文 + README 索引（各文書に「いつ読むべきか」付き）

## ファイルの取得

- 公式サイトのダウンロードカード：<https://www.erisdev.com>
- 直接リンク：`https://raw.githubusercontent.com/ErisPulse/ErisPulse/docs-generated/docs/<lang>/ai-support/...`

## 注意

- このブランチへの PR は不可。ソースは `Develop/v2` にあります
- `python -m scripts.tools gen ...` で構築、コミッターは `erispulse[bot]`
