# 最初の貢献実践

> PR を初めて提出する時は、迷うのは当然のことです。このチュートリアルではプロセスをいくつかの小さなステップに分解しています。それに従えば大丈夫です。中で何か問題があったら Issue や Discussions で質問してください——誰も「基本的すぎる」とか言って怒ったりはしません。みんなはあなたが進歩していくことの方が大切に思っています。

この記事では「i18n 翻訳キーを追加する」を例にします。変更が最小で、最もやりやすいからです。同じ流れは他の種類の貢献でも適用できます。

## 準備

始める前に、以下を用意する必要があります：

- GitHub アカウント
- [uv](https://docs.astral.sh/uv/) のインストール（ErisPulse のパッケージマネージャー）
- Python 3.10+

## 1. リポジトリをフォークしてクローンする

[ErisPulse リポジトリ](https://github.com/ErisPulse/ErisPulse)に移動し、右上の **Fork** をクリックしてあなたのアカウントにコピーします。その後、ローカルにクローンします（「あなたのユーザー名」を実際のユーザー名に置き換えてください）：

```bash
git clone -b Develop/v2 https://github.com/あなたのユーザー名/ErisPulse.git
cd ErisPulse
```

upstream（メインリポジトリ）のアドレスを追加しておくと、後で更新を同期する際便利です：

```bash
git remote add upstream https://github.com/ErisPulse/ErisPulse.git
```

## 2. 開発環境をインストールする

```bash
uv sync                       # 依存関係をインストールし、.venv を作成します
```

環境が正常か確認します：

```bash
uv run pytest -m unit -q      # テストはすべて通過しているはずです
```

## 3. ブランチを作成する

常に `Develop/v2` からブランチを切ります：

```bash
git checkout Develop/v2
git pull upstream Develop/v2   # まず最新のコードを同期します
git checkout -b docs/add-hello-translation
```

ブランチ名は適当で、何をするのかわかれば問題ありません。

## 4. 修正を行う

翻訳キーを追加する例として、`mymodule.hello` という新しいキーを追加すると仮定します。

ルールは一つだけです：**新しい翻訳キーを追加する場合、5種類の言語（zh-CN / en / zh-TW / ja / ru）をすべて一緒に追加する**。さもないと他言語のユーザーに情報が欠落してしまうからです。

`src/ErisPulse/Core/i18n/locales/` の下にある 5つのファイルを開き、それぞれに1行ずつ追加します：

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

> この変更に関わる新しいパブリックメソッドがある場合は、ドキュメントコメントを追加するのを忘れないでください。詳細は[ドキュメントコメントの規定](../styleguide/docstring.md)をご覧ください。

## 5. ローカルでの検証

```bash
uv run ruff check .            # コードスタイルチェック
uv run basedpyright src/ErisPulse   # 型チェック（ソースコードを変更した場合のみ必要） - 数百のwarningに遭遇するかもしれませんが、無視して大丈夫です...ふふ..ふふ
uv run pytest -m unit -q       # テストを実行
```

3つのいずれも通ればOKです。型チェックでの `reportAny` / `Unknown*` などの警告は「型定義がまだ完全にできていない」という段階的なもので、マージを止めるものではありません。

> コアモジュール（Bases / runtime / config / loaders）を変更した場合は、将来的なメンテナンスを容易にするため、対応するテストケースを追加することをお勧めします。

## 6. CHANGELOG を更新する

`CHANGELOG.md` を開き、一番上にある開発中のバージョンを見つけ、適切なカテゴリにエントリを追加します：

```markdown
### 优化

- `Core/i18n/locales` に `mymodule.hello` 翻訳キーを追加しました（zh-CN / en / zh-TW / ja / ru）
```

## 7. コミットしてプッシュする

```bash
git add .
git commit -m "i18n: add mymodule.hello translation"
git push origin docs/add-hello-translation
```

## 8. Pull Request を送信する

プッシュした後、GitHub で **Compare & pull request** という提示があるはずですので、クリックします：

1. ターゲットブランチが **`Develop/v2`** であることを確認してください（`main` を選ばないでください）
2. 変更の種類にチェックを入れて、何を変更したか簡単に説明してください
3. チェックして、メンテナンス担当者がレビューするのを待ちます

レビューでフィードバックをもらうのは普通のことです。あなたが下手だということではありません。提案された内容を修正して再度 push するだけです。承認されれば、あなたの変更は正式に `Develop/v2` に入り、次のバージョンで利用できるようになります。

---

## モジュールやアダプターを貢献する

モジュールやアダプターは完全な構造を持つ小さなパッケージであり、スキャフォールドツールを使うのが一番手っ取り早いです：

```bash
epsdk create    # module または adapter を選択します
```

生成後は、以下のドキュメントに従って進めてください：

- [モジュール開発入門](../developer-guide/modules/getting-started.md)
- [アダプター開発入門](../developer-guide/adapters/getting-started.md)
- [PyPI とモジュールストアへの公開](../developer-guide/publishing.md)

> 開発前に、Issues で「新しいアダプターやモジュール」というテンプレートを使って計画を共有しておくことをお勧めします。メンテナンス担当者は標準への接続やよくある落とし穴を避けるために協力してくれます。

モジュールやアダプターは通常は独立したリポジトリであり、メインリポジトリに入れる必要はありません。`examples/example-module/` と `examples/example-adapter/` は参考用のサンプルです。

---

## 頻繁に遭遇する可能性のある問題

**PR を送ってから、いつチェックされますか？**
通常は数日以内です。メンテナンス担当者がレビューのコメントを残し、必要に応じて調整して再度 push すれば大丈夫です。

**コードチェックでエラーが出ましたか？**
まず `uv run ruff check . --fix` を試してください。これで半分以上は自動修復できます。

**メインリポジトリとの競合が発生しましたか？**
`git pull upstream Develop/v2` を実行し、競合を解消してから push してください。

**直接 `main` にマージできますか？**
できません。すべての変更は `Develop/v2` を経由し、メンテナンス担当者がまとめて `main` に公開します。