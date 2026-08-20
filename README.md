# Kaggle Competition Project

DockerとW&Bを用いたKaggleコンペ用ローカル環境。

## 技術スタック

| ツール | 用途 |
|---|---|
| [gcr.io/kaggle-gpu-images/python](https://github.com/Kaggle/docker-python) | ベースイメージ（GPU・主要ライブラリ同梱） |
| [Docker Compose](https://docs.docker.com/compose/) | コンテナ管理 |
| [uv](https://github.com/astral-sh/uv) | Pythonパッケージ・バージョン管理 |
| [Weights & Biases](https://wandb.ai/) | 実験管理 |
| [Tailscale](https://tailscale.com/) | リモートアクセス（VPN） |

## ディレクトリ構成

```
kaggle_project/
├── conf/
│   ├── config.yaml
│   ├── model/
│   ├── data/
│   └── train/
├── src/
│   ├── dataset.py             # データロード・前処理
│   ├── features.py            # 特徴量生成
│   └── model.py               # モデル定義
├── scripts/
│   ├── train.py               # 学習エントリポイント（Hydra）
│   ├── make_submission.py     # 推論 + submission.csv 生成
│   └── analyze_*.py           # 分析スクリプト（再利用可能）
├── kaggle_kernel/             # Code Competition 提出用 notebook（正本）
├── notebooks/                 # EDA・可視化のみ（本番コード禁止）
├── wandb/                  # W&B実験ログ（Git管理外）
├── data/
│   ├── raw/                   # Kaggle 生データ（Git 管理外）
│   └── processed/             # 前処理済みデータ（Git 管理外）
├── docs/
│   ├── _templates/            # 新コンペ用の雛形（/kaggle-new がコピー）
│   └── {competition}/
│       ├── competition_overview.md   # コンペ仕様（静的）
│       ├── strategy.md               # 時間予算・戦略・週次ふりかえり
│       ├── formulations.md           # 定式化候補ボード
│       ├── experiments.md            # 実験インデックス・CV-LB 表
│       ├── tools.md                  # 分析ツールカタログ
│       ├── experiments/              # 1 実験 1 ファイル
│       ├── eda/                      # データ理解の発見
│       ├── research/                 # Discussion・過去解法・公開NB・論文
│       └── postmortems/              # 重要な失敗の深掘り
└── outputs/                   # チェックポイント・submission（Git 管理外）
```

## ワークフロー

コンペの進め方の規約は **`CLAUDE.md`** に集約されている（フェーズごとのゲート・実験の規律・
提出頻度・情報収集のルール）。Claude Code 用のスラッシュコマンド:

| コマンド | 用途 |
|---|---|
| `/kaggle-start` | セッション開始チェック（フェーズ・未達ゲート・時間予算・警告） |
| `/kaggle-exp` | 新実験の開始（仮説・事前予測・ゲート基準を先に書かせ、2ストライクなら停止） |
| `/kaggle-audit` | 週次セルフ監査（7項目のドリフト検査） |
| `/kaggle-new <slug>` | 新コンペの立ち上げ（`docs/_templates/` から生成） |

## セットアップ

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd kaggle-project
```

### 2. 環境変数の設定

`.env` を作成し、Kaggle APIキーと W&B APIキーを設定する。
Kaggle APIキーは [Kaggle Account Settings](https://www.kaggle.com/settings/account) から、
W&B APIキーは [W&B Authorize](https://wandb.ai/authorize) から取得できる。

```bash
cp .env.example .env
```

```env
KAGGLE_USERNAME=your_username
KAGGLE_KEY=your_api_key
WANDB_API_KEY=your_wandb_api_key
```

### 3. lockfileの生成

```bash
# uvがない場合はインストール
curl -LsSf https://astral.sh/uv/install.sh | sh

uv lock
```

### 4. Dockerコンテナの起動

```bash
docker compose up --build -d
```

### 5. 動作確認

| サービス | URL |
|---|---|
| Jupyter Lab | http://localhost:8888 |
| W&B ダッシュボード | https://wandb.ai/\<entity\>/\<project\> |

## データのダウンロード

```bash
docker compose exec workspace bash

# コンテナ内で実行
kaggle competitions download -c <competition-name> -p data/raw/
unzip data/raw/<competition-name>.zip -d data/raw/
```

## パッケージ管理（uv）

```bash
# パッケージの追加
uv add <package-name>

# 開発用パッケージの追加
uv add --group dev <package-name>

# lockfileの更新後はコミットする
git add uv.lock pyproject.toml
```

コンテナを再ビルドすると新しいパッケージが反映される。

```bash
docker compose up --build -d
```

## 学習の中断・再開

学習には時間がかかるため、任意のタイミングで中断し、あとから続きを再開できる。

### 中断する

学習中に `Ctrl+C` を押すと、その直前のエポックのチェックポイントが保存されて終了する。

```
Epoch 010/030 | train_loss: 0.1234 | val_loss: 0.1100 | val_auc: 0.9500
^C
中断しました。outputs/resume_20260518_effnet_b0_specaugment_fold0.ckpt から再開できます。
```

チェックポイントには以下が保存される:
- モデルの重み
- Optimizer / Scheduler の状態（学習率スケジュールが正確に再現される）
- 完了済みエポック番号
- ベスト val AUC
- W&B の Run ID（同じ Run にメトリクスが続けて記録される）

### 再開する

**同じ `wandb.run_name` で再実行するだけ**。チェックポイントが自動検出されて続きから始まる。

```bash
docker compose exec workspace python scripts/train.py \
  wandb.run_name=20260518_effnet_b0_specaugment fold=0
# → Resume: epoch 10 から再開 (best_auc=0.9500) と表示される
```

### 最初からやり直す

チェックポイントファイルを削除してから実行する。

```bash
rm outputs/resume_20260518_effnet_b0_specaugment_fold0.ckpt
docker compose exec workspace python scripts/train.py \
  wandb.run_name=20260518_effnet_b0_specaugment fold=0
```

> チェックポイントのファイル名形式: `outputs/resume_{run_name}_fold{N}.ckpt`

---

## 実験管理（W&B）

学習エントリポイントは `scripts/train.py`（Hydra）。命名規則と必須ログ項目は
`CLAUDE.md` 第10節に従う。

```python
import wandb
from omegaconf import OmegaConf

wandb.init(
    project=cfg.wandb.project,          # phase 名: baseline / model_search / ensemble / final
    name=cfg.wandb.run_name,            # YYYYMMDD_{model}_{変更点}
    config=OmegaConf.to_container(cfg, resolve=True),
)
wandb.log({
    "val_score": val_score,
    "val_score_rare": val_score_rare,     # 層別スコアは必須
    "val_score_common": val_score_common,
    "val_loss": val_loss,
    "train_loss": train_loss,
}, step=epoch)

artifact = wandb.Artifact("submission", type="submission")
artifact.add_file("outputs/submission.csv")
wandb.log_artifact(artifact)
```

実験結果はW&Bのダッシュボードで確認できる → https://wandb.ai/\<entity\>/\<project\>

## .gitignore の対象

以下はGit管理外とする。

- `data/raw/`, `data/processed/` : データファイル
- `wandb/` : 実験ログ
- `outputs/` : 予測結果
- `.env` : APIキー
