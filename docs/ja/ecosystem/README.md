# エコモジュール

ErisPulseフレームワーク自体はコア機能（イベントシステム、モジュールシステム、設定、ルーター、ログ等）のみを提供し、**GUI、画像レンダリング、可視化などの「重い」機能は組み込み**ではありません。これらの機能はコミュニティが保守する**サードパーティモジュール**によって提供されており、必要に応じてインストールするだけです。

> [!IMPORTANT]
> 本ディレクトリ内のドキュメントは、インストール方法が2種類に分かれています。
>
> - **モジュール**（例: Dashboard / Takumi）は `epsdk install` を使用してインストールします：
>
>   ```bash
>   epsdk install <モジュール名>
>   ```
>
> - **スタンドアロンアプリケーション**（例: ErisPulse-App クライアント）は対応する GitHub Releases から直接ダウンロードしてインストールし、`epsdk` は必要ありません。
>

---

## 推奨モジュールと公式クライアント

| プロジェクト | 種類 | 用途 | ドキュメント |
|------|------|------|------|
| [ErisPulse-App](https://github.com/ErisPulse/ErisPulse-App) | 公式クライアント | 公式クロスプラットフォームクライアント（Android / Windows / Linux / macOS）：ネイティブUIの作成 / 起動 / 複数インスタンスの管理、モジュールストアとイベントビルダーを内蔵；**スマホで直接実行**、デスクトップトレイ常駐 | [ErisPulse-App インストールと使用](docs/ja/app.md) |
| [ErisPulse-Dashboard](https://pypi.org/project/ErisPulse-Dashboard/) | モジュール | Web管理パネル：モジュールの起動・停止、設定編集、ログの確認、イベント監視；他のモジュールがサイドバーにカスタムウィンドウを登録できるようにサポート | [Dashboard の使用とウィンドウ登録](docs/ja/dashboard.md) |
| [ErisPulse-Takumi](https://github.com/ccd2s/ErispulseTakumi)（作者 [@ccd2s](https://github.com/ccd2s)） | モジュール | 画像レンダリング：HTML / ノードツリー / Jinja / SVG / アニメーション、[takumi-py](https://github.com/BalconyJH/takumi-py) ベース；中国語・英語フォントを内蔵し、すぐに使用可能 | [Takumi 画像レンダリング](docs/ja/takumi.md) |

---

## 自分のモジュールもここに掲載されたい？

優良で、広く再利用可能な ErisPulse エコシステムのモジュールをご紹介ください。条件は以下の通りです：

1. [PyPI](https://pypi.org/) に公開済みであり、パッケージ名が `ErisPulse-` で始まっていること
2. 基本的な README と使用例を提供していること
3. 積極的にメンテナンスを行い、Issue に対して反応していること

上記の条件を満たすモジュールの作者は、PR を送信してこのディレクトリに `<モジュール名>.md` のドキュメントを追加し、本表の「推奨モジュール」に一行追加することができます。