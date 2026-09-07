# 初めての貢献実践

> 初めて Pull Request を出すのは、少し不安に感じるかもしれませんが、それは当然のことです。このチュートリアルでは、プロセス全体をいくつかの小さなステップに分解しています。順番に進んでください。途中で何か問題が発生した場合は、Issue または Discussions で質問してください。誰もあなたの質問が「初歩的すぎる」からといって何か言うことはありません。皆が気にしているのは、あなたが前に進んでいるかどうかです。

本文では、「i18n 翻訳キーを追加する」ことを例に挙げています。なぜなら、この変更が最も小さく、実行が最も簡単だからです。ただし、同じような手順は、他の種類の貢献にも適用できます。

## 準備作業

開始する前に、以下の準備が必要です：

- GitHub アカウント
- 本地に [uv](https://docs.astral.sh/uv/) をインストール済み（ErisPulse のパッケージマネージャ）
- Python 3.10+

## 1. リポジトリをフォークしてローカルにクローン

[ErisPulse リポジトリ](https://github.com/ErisPulse/ErisPulse) にアクセスし、右上隅の **Fork** をクリックして自分のアカウントにコピーし、次にローカルにクローンします（「あなたのユーザー名」を実際のユーザー名に置き換えてください）：

```bash
git clone -b Develop/v2 https://github.com/あなたのユーザー名/ErisPulse.git
cd ErisPulse
```

主リポジトリの更新を後で同期できるように、アップストリームのアドレスを追加します：

```bash
git remote add upstream https://github.com/ErisPulse/ErisPulse.git
```

## 2. 開発環境のインストール

```bash
uv sync                       # 依存関係をインストールして .venv を作成
```

環境が正常に動作しているかを確認します：

```bash
uv run pytest -m unit -q      # テストがすべて通過する必要があります
```

## 3. 機能用ブランチの作成

常に `Develop/v2` からブランチを作成してください：

```bash
git checkout Develop/v2
git pull upstream Develop/v2   # 最新のコードを先に同期
git checkout -b docs/add-hello-translation
```

ブランチ名は、何をするつもりかがわかるように自由に付けてください。

## 4. 変更を行う

翻訳キーを追加する例として、`mymodule.hello` という文を追加するとします。

ルールはただ1つです：**翻訳キーを追加する際は、5つの言語（zh-CN / en / zh-TW / ja / ru）すべてに同時に追加する必要があります**。そうしないと、他の言語のユーザーは翻訳が欠落した状態で表示されてしまいます。

`src/ErisPulse/Core/i18n/locales/` フォルダ内の5つのファイルを開き、それぞれに1行を追加します：

```python
# zh_cn.py
"mymodule.hello": "你好",
# en.py
"mymodule.hello": "Hello",
# zh_tw.py
"mymodule.hello": "你好",
# ja.py
"mymodule.hello": "こんにちは",
# ru.py
"mymodule.hello": "Привет",
```

> この変更が新しい公開メソッドに関連している場合、ドキュメント注釈を追加することを忘れないでください。詳しくは[ドキュメント注釈の規則](../styleguide/docstring.md)をご覧ください。

## 5. ローカルでの検証

```bash
uv run ruff check .            # コードスタイルのチェック
uv run basedpyright src/ErisPulse   # タイプチェック（ソースコードを変更した場合のみ必要） - 何百もの警告が表示される可能性がありますが、無視して構いません... へへへ
uv run pytest -m unit -q       # テストの実行
```

上記3つがすべて通過すれば問題ありません。タイプチェックで表示される `reportAny` / `Unknown*` 警告は「タイプ情報がまだ完全に整っていない」状態によるものであり、マージを妨げることはありません。

> コアモジュール（Bases / runtime / config / loaders）を変更した場合は、対応するテストケースを追加しておくと、今後のメンテナンスがしやすくなります。

## 6. CHANGELOG の更新

`CHANGELOG.md` を開き、最上部にある開発中のバージョンを見つけ、適切なカテゴリに以下の内容を追加します。

```markdown
### 优化

- `Core/i18n/locales` に `mymodule.hello` の翻訳キーを追加（zh-CN / en / zh-TW / ja / ru）
```

## 7. 提出とプッシュ

```bash
git add .
git commit -m "i18n: mymodule.hello の翻訳を追加"
git push origin docs/add-hello-translation
```

## 8. Pull Request の提出

プッシュ後、GitHub で **Compare & pull request** が表示されます。それをクリックしてください：

1. 目的のブランチが **`Develop/v2`** であることを確認してください（`main` に選ばないように注意）
2. 変更の種類をチェックし、何を変更したか簡単に記述してください
3. 提出し、メンテナのレビューを待ちます

レビューでフィードバックをもらうのは普通のことです。それは必ずしもあなたの作業が不十分だという意味ではありません。提案に従って修正し、再度 push するだけです。レビューが通れば、あなたの変更は正式に `Develop/v2` に取り込まれ、次のバージョンで使用できるようになります。

## コントリビューションモジュールまたはアダプター

モジュールとアダプターは、完全な構造を持つ小さなパッケージであり、脚手架ツールを使用して始めると最も簡単です：

```bash
epsdk create    # module または adapter を選択
```

生成後は、以下のドキュメントに従って作業を進めることができます：

- [モジュール開発入門](../developer-guide/modules/getting-started.md)
- [アダプター開発入門](../developer-guide/adapters/getting-started.md)
- [PyPI およびモジュールストアへの公開](../developer-guide/publishing.md)

> 開発前に [Issues](https://github.com/ErisPulse/ErisPulse/issues) で「新規アダプターまたはモジュール」テンプレートを使用して、あなたの計画を事前に報告することを推奨します。メンテナは、標準との対応や一般的な落とし穴を避けるためにサポートします。

モジュールやアダプターは通常、独立したリポジトリとして扱われ、メインリポジトリに含まれる必要はありません。`examples/example-module/` および `examples/example-adapter/` は、参考用のテンプレートです。

## 可能会遇到的问题

**PR 提交后多久会有人查看？**  
通常几天内。维护者会留下审查意见，根据需要调整后再次推送即可。

**代码检查报错了？**  
先尝试 `uv run ruff check . --fix`，可以自动修复大部分问题。

**与主仓库发生冲突了？**  
执行 `git pull upstream Develop/v2`，解决冲突后再推送。

**可以直接提交到 `main` 吗？**  
不可以，所有改动都必须通过 `Develop/v2`，再由维护者统一发布到 `main`。