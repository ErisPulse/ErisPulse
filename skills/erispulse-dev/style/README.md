# ErisPulse 透感视觉风格（教学实现 + 真身指引）

ErisPulse 官方 Web 界面的统一视觉语言：玻璃拟态透感。本目录是一个**可跑的
最小活标本**，写 Dashboard / Web 界面时从这里取风格。

## 文件

| 文件 | 说明 |
|------|------|
| `glass.css` | 样式实现（与 Dashboard 架构同构的简化版，约 120 行） |
| `index.html` | 单页活标本：展示空间型布局（hero + 错落玻璃卡）+ 档位/主题切换 |
| `bg.png` | 演示背景插画（EP 娘平铺） |
| `ErisPulseLogo.png` | logo（源：主仓 `.github/assets/`） |

本地预览：直接双击 `index.html`，或 `python -m http.server` 后打开。

## 架构：为什么不能只给 AI 几个色值

Dashboard 的最终效果是**分层覆盖**的产物，单独抽 token 复现不了那股味：

```
:root 实底 token            # --bg-p/s/t 三层表面、--tx-*、--accent、状态五色组
  ↓ 组件模式层              # .card/.badge/.btn——只认 token
.bg-image 覆盖层            # 同名 token 重定义为 color-mix 透明混合（透感核心）
  + [data-bg-level]         # soft 45/78/92 · standard 30/62/82（默认） · strong 20/50/72
  + backdrop-filter          # 全链统一 blur(14px) saturate(1.15)；浮层恒多一档
```

关键模式（glass.css 里逐段有注释）：

- **同名 token 重定义作用域**：组件永远只消费 `--bg-p/s/t`，`.bg-image` 根作用域把
  三个变量重定义为透明混合——组件不感知背景存在，关掉 `.bg-image` 自动变回实底主题
- **层级语义**：p=内容面板最透（背景透出来）、s=次级收一档、t=输入/浮层最实（保可读性）
- **浮层恒多一档**：modal blur 12px（强档 16px），永远比页面面板清晰
- **玻璃必须有东西可模糊**：背景层（插画/渐变）是透感的必要条件，缺失即退化

## AI 产出 ErisPulse 风格界面的姿势

1. 引入 `glass.css`，根元素挂 `class="bg-image"`（可选 `data-bg-level` /
   `data-theme`）；提供背景层（插画/渐变）
2. 组件只用既有词汇：`.card` / `.badge-ok` / `.badge-er` / `.btn-accent` /
   `.modal-box`——不发明新设计语言
3. 需要新组件时按同一 token 词汇扩展；改色只动 `--accent` 与状态五色组
4. 布局对照 `index.html` 的骨架（品牌行 + hero 大标题留白 + 错落玻璃卡），
   给背景留出可见空间——透感是空间感设计，不是把面板铺满

## 真身与同步

上游唯一真相源：`ErisPulse-Dashboard` 仓库（`demo/` 完整跑真身；
`ErisPulse_Dashboard/static/css/` 24 文件全链——base / layout / components /
ep-components / overrides 等）。本目录是**教学蒸馏版**：Dashboard 样式演进后
对照真身同步本 kit，不要反向把 demo 改动带进 Dashboard。
