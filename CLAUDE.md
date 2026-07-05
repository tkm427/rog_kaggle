# CLAUDE.md

Kaggle コンペティションに Claude Code で取り組むためのプロジェクト規約。

- コンペ概要: `docs/{competition}/competition_overview.md`
- 戦略・時間配分: `docs/{competition}/strategy.md`
- 過去類似コンペ・公開資料の調査: `docs/{competition}/research/`

`{competition}` は実際のコンペ名（例: `birdclef2026`）に置き換える。

---

## Kaggleで勝つための原則

コードを書く前に必ず確認する。

### 1. リサーチ・ファースト
コードを書く前に、過去の類似コンペ TOP 解法・公開 Notebook・Discussion を徹底的に調べる。
コンペ開始 3 日以内に `research/past_solutions.md` に上位 5 解法を要約することを目標にする。

### 2. 仮説駆動
全ての実験は仮説検証である。「とりあえずやってみる」実験は立てない。
事前に「予測される結果」を書き、実際の結果との差から学びを抽出する。

### 3. データに基づく判断
推測ではなく実際のデータに基づく根拠を示す。
クラス別 AUC・サンプル数・分布など、具体的な数値を必ず引用する。

### 4. 失敗から学ぶ
うまく行かなかった実験こそ深掘りする。
重要な失敗は `postmortems/` に分析を残し、次のコンペに引き継ぐ。

---

## コンペ進行フェーズ別ガイド

### Phase 1: リサーチ
- `competition_overview.md` を完成させる
- `research/past_solutions.md` に過去類似コンペ TOP 5 解法を要約
- `research/discussions.md` に重要 Discussion の要点を記録
- `research/public_notebooks.md` に公開 Notebook の手法とスコアを記録
- データを眺めて `eda/` に 3-5 本の発見を書く
- `strategy.md` を書く（時間配分・仮説リスト）

### Phase 2
- 公開 Notebook を fork してもよい。とにかく `submission.csv` を出す
- ローカル val ↔ LB の相関を 1 回測定

### Phase 3: 仮説検証ループ
- 1 実験 = 1 仮説 = 1 `expXXX.md`
- 効かなかった実験は重要度に応じて `postmortems/` に深掘り
- 週末に `strategy.md` の「週次ふりかえり」を更新

### Phase 4: 終盤
- 新規アーキテクチャ実験は原則停止
- アンサンブル・seed averaging・推論最適化に集中
- 提出枠の使い方を `strategy.md` に明記

---

## ディレクトリ構成

```
kaggle_project/
├── conf/
│   ├── config.yaml
│   ├── model/
│   ├── data/
│   └── train/
├── src/
│   ├── dataset.py
│   ├── model.py
│   ├── train.py
│   └── utils/wandb_utils.py  # W&Bヘルパー
├── scripts/
│   ├── train.py               # 学習エントリポイント（Hydra）
│   ├── make_submission.py     # 推論 + submission.csv 生成
│   └── analyze_*.py           # 分析スクリプト（再利用可能）
├── notebooks/                 # EDA・可視化のみ（本番コード禁止）
├── wandb/                  # W&B実験ログ（Git管理外）
├── data/
│   ├── raw/                   # Kaggle 生データ（Git 管理外）
│   └── processed/             # 前処理済みデータ（Git 管理外）
├── docs/
│   └── {competition}/
│       ├── competition_overview.md   # コンペ仕様（静的）
│       ├── strategy.md               # 戦略・時間配分・週次ふりかえり
│       ├── experiments.md            # 実験インデックス・現在のフォーカス
│       ├── experiments/              # 1 実験 1 ファイル
│       │   └── exp001_baseline.md
│       ├── eda/                      # データ理解の発見
|       |   ├── fig/                  # EDAの可視化
│       │   └── class_distribution.md
│       ├── research/                 # 競合・先行研究の調査
│       │   ├── past_solutions.md
│       │   ├── discussions.md
│       │   ├── public_notebooks.md
│       │   └── papers.md
│       └── postmortems/              # 重要な失敗の深掘り
│           └── pm001_aug_failed.md
└── outputs/                   # チェックポイント・submission（Git 管理外）
```

---

## ドキュメント管理

### 役割別ドキュメント一覧

| ファイル | 役割 | 更新タイミング |
|---|---|---|
| `competition_overview.md` | コンペ仕様（静的） | コンペ開始時に 1 回 |
| `strategy.md` | 戦略・時間配分・週次ふりかえり | 週次 + 戦略変更時 |
| `experiments.md` | 全実験のインデックス・現在のフォーカス | 各実験完了時 |
| `experiments/expXXX.md` | 1 実験の詳細 | 該当実験中・完了時 |
| `eda/XXX.md` | データ理解の発見 | EDA 時 |
| `research/*.md` | 競合解法・論文・公開資料の調査 | リサーチ時 |
| `postmortems/pmXXX.md` | 重要な失敗の深掘り | 大きな失敗時 |

### `strategy.md` テンプレ

```markdown
## コンペ期間と時間配分
- 開始: YYYY-MM-DD / 終了: YYYY-MM-DD
- Week 1: リサーチ + 最小 E2E 提出
- Week 2-3: ベースライン強化
- Week 4-N: 改善実験
- 終盤 2 週間: アンサンブル・最終調整

## 現在の仮説リスト（優先度順）
1. [H1] 〇〇のaugは稀少クラスに効くはず → exp005 で検証予定
2. [H2] △△の pretrain は…
...

## 週次ふりかえり
### Week 1 (YYYY-MM-DD 〜)
- やったこと:
- 学んだこと:
- 戦略変更点:
```

### `experiments/expXXX.md` テンプレ（仮説駆動を必須化）

```markdown
# expXXX: <短いタイトル>

## 仮説
SpecAugment で稀少クラスの AUC が上がるはず。

## 事前予測
- 全体 AUC: +0.005 程度
- 稀少クラス AUC: +0.02 程度
- 頻出クラス AUC: ±0 〜 微減

## 設定
- 親 config: `conf/config.yaml`
- 変更: `train.augment.spec_mask=true train.augment.mask_width=20`
- W&B Run: `20260513_effnet_b0_specaug20`

## 実際の結果
- 全体: -0.003 / 稀少: -0.01 / 頻出: -0.005

## 考察
事前予測と逆。原因仮説:
(a) マスク幅が広すぎた → exp012 で検証
(b) 稀少クラスは元々データが少なくマスクで情報消失 → 別アプローチ要

## 次のアクション
- exp012: マスク幅を半分にして再検証
- 別途、稀少クラス専用の up-sampling 案を strategy.md に追加
```

### `research/` の中身

- `past_solutions.md`: 過去類似コンペ TOP 5 解法。「モデル」「データ処理」「工夫」「学び」を表形式で
- `discussions.md`: 重要 Discussion の要点と URL
- `public_notebooks.md`: 公開 Notebook の手法・スコア・参考になる点
- `papers.md`: 関連論文のメモ

`past_solutions.md` の項目例:

```markdown
## {過去コンペ名} 1st place
- URL: ...
- モデル: EfficientNet-B3 + SED head
- データ処理: 5sec 窓 → 30sec 推論
- 工夫: secondary_labels 活用、mixup α=0.5
- 学び: secondary_labels を無視するのは間違い
```

### `postmortems/` を書く判断基準

以下に該当する失敗は postmortem を書く。

- 期待スコアと実測スコアの差が大きい（例: 期待 +0.02、実測 -0.01）
- 同じパターンの失敗が 2 回続いた
- 1 週間以上を費やしたが成果が出なかった
- LB 提出で予想外の挙動（ローカル val と LB の乖離など）

postmortem の必須項目: 「何を期待していたか」「何が起きたか」「なぜ起きたか（5 Why）」「次回どうするか」

---

## Claude Code 運用ルール

### セッション開始時の必読
1. `CLAUDE.md`（このファイル）
2. `docs/{competition}/strategy.md` — 今週の方針
3. `docs/{competition}/experiments.md` — 直近の結果と現在のフォーカス
4. （詰まったら）`docs/{competition}/research/` および直近の `postmortems/`

### Plan mode を使う場面（Shift+Tab で起動）
- 新モデル・新パイプライン導入時
- 「次に何の実験をすべきか」を相談したいとき
- 失敗の原因分析を構造化したいとき
→ **実装前に必ず plan mode で設計を確定し、ユーザーの承認を得てから実装に入る**

### TodoWrite の使用
3 ステップ以上のタスクは必ず TodoWrite で分解する。1 タスク完了ごとに即更新。

### コンテキスト管理（`/clear`）
- 1 実験完了 → `strategy.md` / `experiments.md` を更新 → `/clear`
- 長い学習ログを残したまま次の実験に進まない（要約してから `/clear`）
- セッション開始時の必読ファイルは `/clear` 後に毎回読み直す

### Subagent（Task tool）の活用
独立した探索は並列化する。例:
- 過去コンペ 3 つの解法を並列調査
- 公開 Notebook を並列分析
- 複数の analyze スクリプトを並列実行して結果を集約

### 禁止事項
- 推測でコードを書き始めない（データを見てから書く）
- 動作確認済みのベースラインを上書きしない（新ファイル or 新 config で対応）
- 「とりあえず動かしてみる」実験を立てない（仮説と事前予測を書いてから）
- `experiments.md` を更新せずに次の実験に進まない

---

## 実行環境

```bash
docker compose up -d                                          # 起動
docker compose exec workspace bash                            # コンテナに入る
docker compose exec workspace python scripts/train.py         # 直接実行
docker compose down                                           # 停止
docker compose logs -f                                        # ログ確認
```

| サービス | URL |
|---|---|
| JupyterLab | http://localhost:8888 |
| W&B ダッシュボード | https://wandb.ai/\<entity\>/\<project\> |

学習の実行はユーザーが行う。コマンドを出力すること。

---

## 設定管理（Hydra）

すべての実験パラメータは `conf/` 以下の YAML で管理する。ファイルを書き換えず、CLI オーバーライドで変更する。

```bash
python scripts/train.py model=effnet_b2 train.lr=5e-4 wandb.run_name=20260513_effnet_b2_lr5e4
```

`conf/config.yaml` の基本構成:

```yaml
defaults:
  - model: effnet_b0
  - data: default
  - train: default
  - _self_

wandb:
  project: baseline
  run_name: ???  # 実行時に必ず指定
```

新しいモデル・データ処理を追加するときは、既存 config を上書きせず新規 config ファイルを作る。

---

## 実験管理（W&B）

### 命名規則

| 種別 | 形式 | 例 |
|---|---|---|
| Project | `{phase}` | `baseline`, `augmentation`, `model_search`, `cpu_opt` |
| Run | `YYYYMMDD_{model}_{変更点}` | `20260513_effnet_b0_baseline` |

phase の選択肢: `baseline` / `augmentation` / `model_search` / `pseudo_label` / `cpu_opt` / `ensemble` / `final`

### 必須ログ項目

```python
wandb.init(
    project=cfg.wandb.project,
    name=cfg.wandb.run_name,
    config=OmegaConf.to_container(cfg, resolve=True),
)
wandb.log({
    "val_score": val_score,                # 全体
    "val_score_rare": val_score_rare,      # 稀少カテゴリ
    "val_score_common": val_score_common,  # 頻出カテゴリ
    "val_loss": val_loss,
    "train_loss": train_loss,
}, step=epoch)
wandb.save("outputs/best_model.pth")

artifact = wandb.Artifact("submission", type="submission")
artifact.add_file("outputs/submission.csv")
wandb.log_artifact(artifact)
```

`val_score_rare` / `val_score_common` の分け方はコンペごとに定義し、`competition_overview.md` に記録する。

---

## 推論・提出

推論ロジックは **`scripts/make_submission.py` に集約**（`src/inference.py` は作らない）。
ローカル/Docker 上での動作確認・OOF 検証用。

```bash
docker compose exec workspace python scripts/make_submission.py
# → outputs/submission.csv が生成される
```

**Kaggle への実提出は `make_submission.py` を直接使わない**（Hydra・`src/` への import 依存があり、
Code Competition のインターネット OFF 環境にそのまま持ち込めない）。代わりに
**`kaggle_kernel/submission.ipynb`** を正本として維持する（`src/dataset.py` / `src/features.py` の
必要な関数と `make_submission.py::run_inference` 相当のロジックを Hydra 抜きの自己完結コードとして
埋め込んだ Notebook。運用詳細は `kaggle_kernel/README.md` 参照）。

**ルール**: `src/dataset.py` / `src/features.py` / `scripts/make_submission.py` の
**有効化されている（config のデフォルトで実際に実行される）推論経路**に変更が入ったら、
**同じ変更を `kaggle_kernel/submission.ipynb` にも反映してから実験を完了とする**
（`experiments.md` を更新する前に確認する）。`enable_xxx: false` のまま無効化されている
実験的機能（ABANDONED 含む）は、有効化するまで Notebook に移植する必要はない
（exp001 の `dtw_align` 同様、未使用ロジックは Notebook に持ち込まない方針）。
学習済みモデルの更新だけなら Notebook の再 push は不要（`kaggle datasets version` でモデル
Dataset のみ更新）。

新しい推論手法（TTA・アンサンブル等）を試すときは `make_submission.py` を直接書き換えず、関数を追加して config で切り替える。Notebook 側も対応する関数を追加する形で同期する。

---

## 分析の原則

**推測ではなく、実際のデータに基づく根拠を示す。**

- 何かを主張・判断するときは、対応するスクリプトを実行し、具体的な数値（スコア・サンプル数・分布等）を引用する
- 実験結果が悪化した場合、即廃棄しない。クラス別スコアで「どこが悪化したか」を確認してから結論を出す
- 新しい分析を行ったら、スクリプトを `scripts/analyze_*.py` または `notebooks/` に保存し、**分析ツールカタログ**に追記する

---

## 分析ツールカタログ

再利用可能な分析スクリプト・ノートブックの一覧。新しいツールを追加したら必ずここに記載する。

| ファイル | 用途 | 主な引数 | 主な出力 |
|---|---|---|---|
| `scripts/analyze_per_class_auc.py` | クラス別スコア分析（稀少 vs 頻出） | `--model`, `--data` | クラス別スコアテーブル |
| `scripts/analyze_cv_lb_corr.py` | ローカル CV と LB の相関分析 | `--exp` | 散布図・相関係数 |
| `scripts/eda_overview.py` | データ全体の俯瞰 EDA | なし | ウェル数・行数・TVT分布・GRシフト・null model RMSE |
| `scripts/analyze_beam_alignment_quality.py` | beam search alignment（exp002）のprefix-holdout sanity check | `--train-dir`, `--n-wells`, `--seed` | flat anchor比較RMSE。holdout長は固定30%のため長horizon検証には不十分（pm001参照） |
| `scripts/visualize_beam_alignment_drift.py` | beam search alignment（pm001）のドリフト・fit品質の可視化 | `--train-dir`, `--n-wells`, `--seed` | `postmortems/fig/pm001_drift_vs_step.png`（ステップ数別RMSE）, `pm001_path_overlay.png`（true vs beam vs flat anchorパス）, `pm001_rmse_distribution.png`（holdout30%/90%のRMSE分布比較） |
| `scripts/analyze_per_well_rmse.py` | ウェル別残差分析（exp003）。tail長・rare行比率とOOF RMSEの相関、外れ値ウェル抽出 | `--oof-path`, `--rare-threshold`, `--top-n` | `eda/fig/exp003_per_well_rmse.csv`, `exp003_rmse_histogram.png`, `exp003_rmse_vs_tail_length.png`, `exp003_rmse_vs_rare_frac.png`, `exp003_worst_wells.png` |

---

## セッション運用フロー

### セッション開始時
1. `CLAUDE.md` を読む
2. `docs/{competition}/strategy.md` で今週の方針を確認
3. `docs/{competition}/experiments.md` で現在のフォーカスを確認
4. 今回のセッションでやることを TodoWrite に書く
5. **実装前に必ず設計を提案し、承認を得てから実装する**

### 実験実行時
1. 仮説と事前予測を `experiments/expXXX.md` に先に書く
2. config を作成（または CLI オーバーライドを決める）
3. 学習を実行（長時間なら別ターミナル）
4. 結果が出たら `expXXX.md` の「実際の結果」「考察」「次のアクション」を埋める
5. `experiments.md` の表に 1 行追加

### セッション終了前
- `experiments.md` の「現在のフォーカス」を次タスクに更新
- `experiments/expXXX.md` を完成させる
- LB 提出した場合は CV-LB 相関メモに記録
- 大きな失敗があれば `postmortems/pmXXX.md` を作成
- 週末なら `strategy.md` の週次ふりかえりを更新

---

## パッケージ管理（uv）

```bash
uv add <package>
git add uv.lock pyproject.toml
docker compose up --build -d    # コンテナ再ビルドが必要
```

---
