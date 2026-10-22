# 初めてのコントリビューション実践ガイド

> [!TIP]
> **このドキュメントを読むべきタイミング**：初めての Pull Request を提出する準備をしているとき——fork からマージまでの各ステップに、そのままコピーして使えるコマンドを記載しています。すでに PR の経験があり、リポジトリの規約だけ確認したい場合は、[CONTRIBUTING.md](../../../CONTRIBUTING.md) を直接ご覧ください。

> 初めて PR を出すときは、多少の不安があるのが当然です。ごく自然なことです。このチュートリアルではプロセス全体をいくつかの小さなステップに分解しているので、手順どおりに進めるだけで大丈夫です。途中で何か問題にぶつかったら、Issue や Discussions で気軽に質問してください——質問が「基本的すぎる」ことをとがめる人はいません。みんなが気にかけているのは、あなたが前へ進んでいるという事実のほうです。

この記事では「i18n 翻訳キーを 1 つ追加する」を例に取り上げます。変更量が最も少なく、いちばん通り抜けやすいからです。ただし、同じ流れは他の種類のコントリビューションにもそのまま当てはまります。

## 事前準備

始める前に、以下を準備してください：

- GitHub アカウント
- ローカル環境に [uv](https://docs.astral.sh/uv/)（ErisPulse のパッケージマネージャー）をインストール済みであること
- Python 3.10+

## 1. Fork してリポジトリをクローン

[ErisPulse リポジトリ](https://github.com/ErisPulse/ErisPulse) にアクセスし、右上の **Fork** をクリックして自分のアカウントにコピーします。その後、ローカルにクローンしてください（「あなたのユーザー名」を実際のユーザー名に置き換えてください）：

```bash
git clone -b Develop/v2 https://github.com/あなたのユーザー名/ErisPulse.git
cd ErisPulse
```

上流（upstream）リモートを追加しておくと、後でメインリポジトリの更新を同期しやすくなります：

```bash
git remote add upstream https://github.com/ErisPulse/ErisPulse.git
```

## 2. 開発環境のセットアップ

```bash
uv sync                       # 依存関係をインストールして .venv を作成
```

環境が正常かどうか確認します：

```bash
uv run pytest -m unit -q      # テストがすべてパスするはず
```

## 3. 機能ブランチを作成

必ず `Develop/v2` からブランチを切ります：

```bash
git checkout Develop/v2
git pull upstream Develop/v2   # 先に最新コードを同期
git checkout -b docs/add-hello-translation
```

ブランチ名は自由です。何をするためのブランチか分かれば十分です。

## 4. 変更を加える

翻訳キーを 1 つ追加する例として、`mymodule.hello` という一文を新しく追加するとします。

ルールは 1 つだけ：**翻訳キーを新規追加する場合は、5 つの言語（zh-CN / en / zh-TW / ja / ru）すべてに同時に追加する**。そうしないと、他の言語のユーザーには欠落が見えてしまいます。

`src/ErisPulse/Core/i18n/locales/` 配下の 5 つのファイルを開き、それぞれ 1 行ずつ追加します：

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

> 今回の変更に新しい公開メソッドが含まれる場合は、忘れずにドキュメントコメントを追加してください。詳細は[ドキュメントコメント規約](../styleguide/docstring.md)をご覧ください。

## 5. ローカルでの検証

```bash
uv run ruff check .            # コードスタイルチェック
uv run basedpyright src/ErisPulse   # 型チェック（ソースコードを変更した場合のみ必要）
uv run pytest -m unit -q       # テストを実行
```

3 つすべてパスすれば OK です。型チェックでは `reportAny` / `Unknown*` 系の warning がいくつか出るかもしれません（型アノテーションはまだ段階的に整備中です）。これらは**マージをブロックしません**ので、一つひとつ潰す必要はありません。ただし、本物の型エラー（たとえば戻り値の型とアノテーションの不一致、引数の型に互換性がない、`None` の可能性がある値の属性へのアクセスなど）は error に格上げされ、CI でブロックされます——この場合は修正が必要です。

> コアモジュール（Bases / runtime / config / loaders）に手を入れた場合は、ついでに対応するテストケースを補っておくと、今後のメンテナンスが楽になります。

## 6. CHANGELOG を更新

`CHANGELOG.md` を開き、一番上にある開発中のバージョンを見つけて、適切なカテゴリの下に 1 件のエントリを追加します：

```markdown
### 最適化

- `Core/i18n/locales` に `mymodule.hello` 翻訳キーを追加（zh-CN / en / zh-TW / ja / ru）
```

## 7. コミットしてプッシュ

```bash
git add .
git commit -m "i18n: add mymodule.hello translation"
git push origin docs/add-hello-translation
```

## 8. Pull Request を提出

プッシュすると、GitHub に **Compare & pull request** という案内が表示されるので、クリックして開きます：

1. ターゲットブランチが **`Develop/v2`** になっていることを確認する（`main` を選ばないこと）
2. 変更の種類にチェックを入れ、何を変更したのかを簡単に書く
3. 送信して、メンテナーのレビューを待つ

レビューでいくつか指摘が出るのはごく普通のことで、できが悪いという意味ではありません——提案どおり修正したら、もう一度 push すれば OK です。承認されれば、あなたの変更は正式に `Develop/v2` に入り、次のバージョンで使えるようになります。

---

## モジュールやアダプターへのコントリビュート

モジュールとアダプターは、完全な構造を持つ小さなパッケージです。スキャフォールドツール（ひな形ツール）でスタートするのが一番手軽です：

```bash
epsdk create    # module または adapter を選択
```

生成が終わったら、以下のドキュメントに沿って進めていけば大丈夫です：

- [モジュール開発入門](../developer-guide/modules/getting-started.md)
- [アダプター開発入門](../developer-guide/adapters/getting-started.md)
- [PyPI とモジュールストアへの公開](../developer-guide/publishing.md)

> 開発を始める前に、[Issues](https://github.com/ErisPulse/ErisPulse/issues) で「新規アダプターまたはモジュール」テンプレートを使って計画をひとこと伝えておくことをおすすめします。メンテナーが標準への準拠を支援し、よくある落とし穴を避ける手助けをしてくれます。

モジュールとアダプターは通常、独立したリポジトリとして管理するもので、メインリポジトリに無理に詰め込む必要はありません。`examples/example-module/` と `examples/example-adapter/` が参考にできるサンプルです。

---

## よくある質問

**PR を提出してから、どのくらいで見てもらえますか？**
通常は数日以内です。メンテナーがレビューコメントを残すので、必要に応じて修正してからもう一度 push すれば大丈夫です。

**コードチェックでエラーが出ましたか？**
まず `uv run ruff check . --fix` を試してみてください。大半は自動で修正できます。

**メインリポジトリとコンフリクトしましたか？**
`git pull upstream Develop/v2` を実行し、コンフリクトを解決してから push してください。

**`main` に直接提出できますか？**
できません。すべての変更は `Develop/v2` に提出し、その後メンテナーがまとめて `main` にリリースします。

## 次のステップ

### 継続的に参加したい場合

- [ErisPulse へのコントリビュート](README.md) - ドキュメント / 翻訳 / Bug / モジュール / アダプターなど、すべてのコントリビューション方法

### モジュールやアダプターを開発したい場合

- [モジュール開発入門](../developer-guide/modules/getting-started.md)
- [アダプター開発入門](../developer-guide/adapters/getting-started.md)
- [公開とモジュールストアガイド](../developer-guide/publishing.md)