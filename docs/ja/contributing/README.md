# ErisPulse への貢献

> **初めて貢献するあなたへ**
> オープンソースプロジェクトは、決して一二人のコア開発者の「大規模なアクション」だけで支えられているわけではありません。多くの場合、無数の小さな変更が積み重なっているのです——1つの誤字、1つの翻訳、小さなバグの修正、どれも ErisPulse を少しずつ前進させています。だから、自分の貢献が「十分な量」かどうかを測る必要はありません。PR を提出する意思さえあれば、あなたはすでにこのプロジェクトの一部です。

## 参加できる方法

貢献は、本体コードを書くだけではありません。以下の事柄も、ErisPulse をより良くする助けになります：

- **ドキュメントの充実** —— 誤字の修正、わかりにくい記述の整理、自分が経験した問題の追加。参加のハードルが最も低く、いつでも始められます。
- **翻訳の補完** —— フレームワークは 5 種類の言語（zh-CN / en / zh-TW / ja / ru）をサポートしており、翻訳が漏れている部分や不正確な部分があれば、ぜひ補完してください。
- **バグの修正** —— [Issues](https://github.com/ErisPulse/ErisPulse/issues) から、自分が理解している問題を選んで、再現して修正します。
- **サンプルの作成** —— 自分の使用経験を整理して、他の人の参考になるようにサンプルコードを作成します。
- **モジュール / アダプターの開発** —— フレームワークに新しいプラットフォームや機能を追加します。難易度は高めですが、達成感も大きいです。

> どこから始めたらよいかわからない場合は、[Discussions](https://github.com/ErisPulse/ErisPulse/discussions) で相談してください。メンテナが適切な方向性を示します。

## 初めての PR 提出

まだ PR を提出したことがない場合は、[初めての貢献実践](first-contribution.md) を先に読んでおくことをおすすめします。このページでは、リポジトリのフォークから PR のマージまでの全プロセスが網羅されています。問題があれば、Issue や Discussions で質問してください。

## 開発環境

完全な開発規約はルートディレクトリの [CONTRIBUTING.md](../../../CONTRIBUTING.md) を参照してください。簡単に始めるには：

```bash
git clone -b Develop/v2 https://github.com/ErisPulse/ErisPulse.git
cd ErisPulse
uv sync                       # 開発環境の同期
uv run pytest -m unit         # ユニットテストの実行
uv run ruff check .           # コードのチェック
```

## 提出プロセス

簡単に言えば、以下の手順です：リポジトリをフォーク → `Develop/v2` をベースにブランチを作成 → 変更してテストを通過 → `Develop/v2` に PR を提出。

いくつか注意点があります：

- PR は **`Develop/v2`** ブランチに提出してください。`main` または `Pre-Release/v2` に直接変更を加えないでください。
- 提出前に `pytest` / `ruff` / `basedpyright` がすべて通過していることを確認してください（型チェックにおける `reportAny` / `Unknown*` 警告は「型がまだ徐々に整備中」のため、マージを妨げません）。
- 機能を変更した場合は `CHANGELOG.md` に記録を残してください。
- 公共 API にメソッドを追加した場合は、ドキュメントのコメントを追加してください（[規約はこちら](../styleguide/docstring.md)）。

## モジュールまたはアダプターの貢献

新しいモジュールやアダプターを作成する予定がある場合は、まず [Issues](https://github.com/ErisPulse/ErisPulse/issues) で「新アダプターまたはモジュール」テンプレートを使って、自分のアイデアを簡単に説明してください。完璧に書く必要はありません。意図を伝えるだけで、メンテナが開発の方向性や基準を整理し、スムーズに進められるようにします。

スクリプトツールを使って、素早く始めることができます：

```bash
epsdk create    # module または adapter を選択し、完全なプロジェクト構造を生成
```

その後、[モジュール開発の入門](../developer-guide/modules/getting-started.md) または [アダプター開発の入門](../developer-guide/adapters/getting-started.md) を参照してください。完成後は、[PyPI とモジュールストアへの公開](../developer-guide/publishing.md) も可能です。

> モジュールやアダプターは通常、独立したリポジトリになります。メインリポジトリに統合する必要はありません。`examples/` のサンプルプロジェクトを参考にしてください。

## ヘルプの取得

- [GitHub Issues](https://github.com/ErisPulse/ErisPulse/issues) —— 問題の報告、要望の提出
- [GitHub Discussions](https://github.com/ErisPulse/ErisPulse/discussions) —— 考え方の議論、質問の提出
- メール：`erisdev@88.com`