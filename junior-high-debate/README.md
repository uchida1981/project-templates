# 中学受験相談 マルチエージェントAI討論アプリ

AI エージェント（塾講師・教育者・キャリアコンサル・統合役）が中学受験の進路相談について多角的に討論します。

## セットアップ

### 1. API キーの設定

```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

毎回設定するのが手間な場合は `~/.bashrc` または `~/.zshrc` に追記してください。

### 2. 依存パッケージのインストール（uv 推奨）

```bash
# このディレクトリに移動
cd junior-high-debate

# 仮想環境の作成と依存パッケージのインストール
uv sync
```

`uv` がない場合は以下でインストールできます：

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### venv を使う場合

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install anthropic colorama
```

---

## 実行方法

### 基本実行（デフォルト 2 ラウンド）

```bash
uv run python debate.py
```

### ラウンド数を指定する

```bash
uv run python debate.py --rounds 3
```

### 前提テキストを別ファイルで指定する

```bash
uv run python debate.py --premise my_case.txt
```

---

## 前提の差し替え方

| 方法 | 手順 |
|------|------|
| **ファイル編集** | `premise.txt` を直接書き換える（最も簡単） |
| **別ファイル指定** | `python debate.py --premise 別ファイル.txt` で指定 |
| **コード内定数** | `debate.py` の `DEFAULT_PREMISE` 変数を編集（`premise.txt` がない場合のフォールバック） |

`premise.txt` → `DEFAULT_PREMISE` の優先順位でテキストが読み込まれます。

---

## 出力

- **ターミナル**: 各エージェントの発言がリアルタイムでストリーミング表示されます（役割ごとに色分け）
- **ファイル**: 討論終了後、カレントディレクトリに `debate_log.md` が生成されます

---

## エージェント構成

| 役割 | 色 | 視点 | 発言文字数 |
|------|-----|------|-----------|
| 塾講師 | 黄 | 偏差値・競争・算数重視・志望校到達 | 200〜300字 |
| 教育者 | 緑 | 知的好奇心・自走性・長期的健全さ | 200〜300字 |
| キャリアコンサル | 水色 | 20年後の人生・自律性・家族消耗 | 200〜300字 |
| 統合役 | 紫 | 全発言の統合・対立点明示・結論 | 400〜600字 |

討論の流れ：各ラウンドで 塾講師 → 教育者 → キャリアコンサル の順に発言し、全ラウンド終了後に統合役がまとめます。
