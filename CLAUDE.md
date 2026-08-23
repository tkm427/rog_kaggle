# CLAUDE.md 

このファイルは**コンペ非依存**。コンペ固有の情報は `docs/{competition}/` に、環境構築手順は
`README.md` に置く（ここに重複させない）。

**このファイルは「原則集」ではなく「ゲート集」として読む。** ゲートは満たすまで次に進まない。
セッション開始時は `/kaggle-start` を実行すること。

---

## 1. チーム構成と役割分担

人間（ntteast）+ Claude Code の 2 人チーム。

| 領域 | 人間 | Claude Code |
|---|---|---|
| 方針決定・打ち切り判断・提出枠の選択 | ◎ 最終決定 | 選択肢を 3 つ以内 + 推薦 1 つで提示 |
| 学習の実行（GPU / 長時間） | ◎ 実行 | コマンドを出力するのみ |
| Kaggle への提出 | ◎ 実行 | notebook / submission の準備と検証 |
| リサーチ（Discussion / 論文 / 公開 NB） | レビュー | ◎ 実行 |
| 実装・分析スクリプト・EDA | レビュー | ◎ 実行 |
| ドキュメント更新 | — | ◎ 実行 |

### Claude の振る舞い規約

- **選択肢は 3 つまで。必ず推薦を 1 つ添える。** 全列挙・アイデアの洪水は禁止
  （上位解法の著者も「エージェントの提案は質がランダムで処理しきれない」と指摘している）
- **1 セッション 1 目的。** 並行して複数実験を進めない
- **ゲート違反を検知したら作業を止め、状況と選択肢を提示して人間の判断を待つ。** 承認されれば続行してよい
- 推測でコードを書かない（データを見てから書く）／ 悪化した結果はそのまま報告する
- **存在しないファイルをドキュメントに書かない。** パスを書いたら `ls` で実在を確認する

### 人間に読ませるものの規約

**md ファイルは Claude と git のための正本であり、人間が読む前提にしない。**
人間の認知負荷を上げる出力は、それ自体が失敗とみなす。

- **判断を求めるときは AskUserQuestion を使う。** 散文で選択肢を並べて読ませない
- **md の中身をチャットに貼らない。** ダッシュボードを再生成し、パスと「前回からの差分」だけ述べる
- **状況報告は `/kaggle-start` の固定フォーマットに従う。** 毎回違う形で書かない
- 長い調査結果・比較・ふりかえりは md に書き、チャットには結論と次の一手だけ出す

---

## 2. 勝つための 5 原則

1. **リサーチ・ファースト** — 他人が公開済みの中核アイデアを、読まずに自分で再発明しようとしない
2. **定式化 > 特徴量** — 同じ定式化の枝を掘るより、別の定式化を 1 つ試す方が期待値が高い
3. **仮説駆動** — 事前予測とゲート基準を書いてから実験する
4. **データに基づく判断** — 数値を引用する。「投資対効果が低い」は **1 回動かしてから** 言う
5. **失敗から学ぶ** — 失敗の「層」（実装 / ハイパラ / 定式化）を特定する

---

## 3. フェーズとゲート

### Phase 0: セットアップ（Day 0-1）
`/kaggle-new {competition}` を実行 → 環境起動 → データ DL。

### Phase 1: リサーチ（〜Day 7）

| ID | 完了条件 |
|---|---|
| **R1** | `competition_overview.md` 完成（評価指標 / データ / 提出形式 / Code Comp 制約 / リーク境界の表） |
| **R2** | `research/discussions.md`: **upvote 上位 10 スレッド + host 投稿の全件**について、**本文とコメント欄を読んだ**要約。「未読」項目が 1 つでも残っていれば不合格 |
| **R3** | `research/past_solutions.md`: 類似コンペ TOP5 の要約 |
| **R4** | `research/public_notebooks.md`: 公開上位帯の NB を 3 本、**実コードを読んで**手法とリークの有無を記録 |
| **R5** | `formulations.md`: **問題の定式化候補を 3 案以上**。各案に「想定上限 / 実装コスト / 必要資源 / 出典」。1 案しか出せないなら R2/R3 の調査が足りていない |
| **R6** | `eda/` に 3〜5 本の発見 |

### Phase 2: E2E 提出（〜Day 10）

| ID | 完了条件 |
|---|---|
| **S1** | submission が LB にスコアを出した（公開 NB の fork でもよい） |
| **S2** | OOF（正しい分割）と LB の対応を 1 点記録 |
| **S3** | **2 系統目（NN 系）の依存を `uv add` 済み**（torch / timm 等）。ここで入れないと後から入らない |

### Phase 3: 二系統並走 + 仮説検証（本体）

| ID | 完了条件 |
|---|---|
| **T1** | **異なるアーキテクチャ族を 2 系統**、いずれも「提出可能な状態」にする。T1 未達のまま片系統だけの改善実験は **3 本まで** |

以降は第 4 節の実験ループを回す。

### Phase 4: 終盤（残り 2 週間）

| ID | 完了条件 |
|---|---|
| **F1** | 新規アーキテクチャ実験を停止し、アンサンブル / seed averaging / 推論最適化に集中 |
| **F2** | **提出枠の使い方を先に決めて `strategy.md` に明記**（例: 1 枠 CV 最良、1 枠 堅牢側） |
| **F3** | **実データ規模で推論を通す**。リラン時間・メモリの実測値を記録 |

---

## 4. 実験の規律

- 1 実験 = 1 仮説 = 1 `docs/{competition}/experiments/expXXX.md`
- 着手前に「仮説」「事前予測」「**ゲート基準**」「**どの定式化に属するか**」を書く（`/kaggle-exp` が強制）
- **ゲート基準は null model 比ではなく「目標スコアへの残距離を何 % 詰めるか」で置く**
  （前回は flat anchor 12.8ft を延々基準にしたが上位は 5.6。この基準は道筋と無関係だった）
- 結果には **「失敗の層」を必ず分類**: 実装 / ハイパラ / **定式化**
- **2 ストライクルール**: 同一定式化で 2 連続「ゲート不合格 or 改善ゼロ」→ **停止して人間に報告**し、
  次の 1 実験は `formulations.md` の別案に充てる。**3 連続は禁止**
- 悪化した実験を即廃棄しない。層別スコア・per-sample 残差で「どこが悪化したか」を確認してから結論を出す

### postmortem を書く基準
期待と実測の乖離が大きい / 同種の失敗が 2 回続いた / 1 週間以上成果が出ない / LB とローカルの乖離。

必須項目は「何を期待していたか」「何が起きたか」「5 Why」「次回どうするか」。
**5 Why の最下段が実装レベルで終わっていないかを必ず自己チェックする**
（前回は 5 段すべて実装レベルで止まり、定式化の誤りに到達できなかった）。

---

## 5. 時間予算の算術

`strategy.md` の先頭に常に置き、毎週更新する。

```
残り日数: N / 1実験の平均所要: D 日 / 残り実験可能数: N/D 本
現在の best: X / 目標: Y / 残距離: X−Y
計画中の実験段数: M 本   ← M > N/D なら計画を切る
```

1 実験に 3 日以上かかる見込みなら、先に「1 日で終わる縮小版」を設計する。

---

## 6. 提出の規律

- **週 1 回以上提出する（下限）。** CV-LB 相関の測定と、終盤の submission デバッグの両方に必要
- 毎提出を `experiments.md` の CV-LB 表に 1 行追加
- LB が「良すぎる」ときはリークを疑い、train/test の重複を必ず確認する
- **public LB の順位を目標にしない。** 信頼するのは正しく分割した OOF

---

## 7. 情報収集の規律

- **WebFetch が SPA（Kaggle 等）で本文を取れなかったら、即 claude-in-chrome に切り替える。**
  「未読」のまま次セッションに送ることを**禁止**する
- Discussion は **upvote 順と新着順の両方**を見る。**コメント欄まで読む**
- host のコメント・公式アナウンスは最優先
- 公開実装（notebook / GitHub）があれば URL と入手方法を必ず記録する
- **コンペ期間中も週次でリサーチを更新する。** Phase 1 で終わりにしない

---

## 8. セッション運用

- **開始時**: `/kaggle-start`（ダッシュボードを再生成して状況を報告する）
- **実験開始時**: `/kaggle-exp`
- **終了時**: `expXXX.md` 完成 → `experiments.md` に 1 行 → 「現在のフォーカス」更新 →
  （提出したら）CV-LB 表 → 週末なら `/kaggle-audit`。**これらを済ませてから `/clear`**
- **Plan mode を使う場面**: 新定式化・新パイプライン導入時 / 次の実験の相談 / 失敗の原因分析
  → 実装前に必ず設計を確定し、承認を得てから実装に入る

---

## 9. ドキュメント体系

テンプレートは `docs/_templates/` にある（`/kaggle-new` がコピーする）。

| ファイル | 役割 | 更新タイミング |
|---|---|---|
| `gates.md` | **ゲートの達成宣言 + 根拠**（ダッシュボードが読む） | ゲート達成時 |
| `competition_overview.md` | コンペ仕様（静的） | 開始時に 1 回 |
| `strategy.md` | 時間予算・戦略・週次ふりかえり | 週次 + 戦略変更時 |
| `formulations.md` | **定式化候補ボード**（案 / 想定上限 / コスト / 状態） | Phase 1 + 定式化を試すたび |
| `experiments.md` | 全実験のインデックス・現在のフォーカス・CV-LB 表 | 各実験完了時 |
| `experiments/expXXX.md` | 1 実験の詳細 | 該当実験中・完了時 |
| `eda/XXX.md` | データ理解の発見 | EDA 時 |
| `research/*.md` | Discussion / 過去解法 / 公開 NB / 論文 | リサーチ時（週次更新） |
| `postmortems/pmXXX.md` | 重要な失敗の深掘り | 大きな失敗時 |
| `tools.md` | 再利用可能な分析スクリプトのカタログ | ツール追加時に必ず |

### ダッシュボード（人間の読む場所）

```bash
python3 scripts/build_dashboard.py --open      # outputs/dashboard.html を生成して開く
```

上記の md 群をパースし、**フェーズ / 未達ゲート / 時間予算 / 警告 / 定式化ボード / OOF 推移**を
1 画面に集約する。**`gates.md` の自己申告と機械計測（未読件数・提出回数・アーキ族数・
同一定式化の連続数）を突き合わせ、食い違いを検出する** — 「やった気になっていた」を潰すのが主目的。
`/kaggle-start` と `/kaggle-audit` が自動で再生成する。

`expXXX.md` の必須欄（雛形は `docs/_templates/experiments/exp000_template.md`）:
**所属する定式化 + 2 ストライク判定 / 仮説 / 事前予測 / ゲート基準 / 設定 / 実際の結果 /
失敗の層 / 考察 / 次のアクション**。

---

## 10. 実装規約

- **Hydra**: 全パラメータは `conf/` の YAML。**ファイルを書き換えず CLI オーバーライドで変更**し、
  新しいモデル・データ処理は既存 config を上書きせず新規ファイルを作る
  → `uv run python scripts/train.py model=lgbm train.lr=5e-4 wandb.run_name=20260513_lgbm_lr5e4`
- **W&B**: Project = phase（`baseline` / `model_search` / `ensemble` / `final` 等）、
  Run = `YYYYMMDD_{model}_{変更点}`。必須ログは `val_score` / **層別スコア** / `val_loss` / `train_loss`。
  best model と submission を artifact 化する
- **推論**: `scripts/make_submission.py` に集約（`src/inference.py` は作らない）。
  新手法（TTA・アンサンブル等）は直接書き換えず、関数を追加して config で切り替える
- **パッケージ**: `uv add <pkg> && git add uv.lock pyproject.toml && docker compose up --build -d`
- **分析ツール**: `scripts/analyze_*.py` を作ったら**必ず `docs/{competition}/tools.md` に追記**する
  （`scripts/build_dashboard.py` はコンペ非依存なので tools.md には書かない）

### Code Competition の同期ルール

Kaggle への実提出は `kaggle_kernel/` の**自己完結 notebook を正本**とする
（Hydra や `src/` への import 依存を持ち込めないため）。

> `src/` や `scripts/make_submission.py` の**有効化されている推論経路**に変更が入ったら、
> 同じ変更を notebook に反映してから実験を完了とする（`experiments.md` を更新する前に確認）。
> `enable_*: false` のまま無効化されている機能は、有効化するまで移植不要。
> 学習済みモデルの更新だけなら notebook の再 push は不要（モデル Dataset のみ version 更新）。

---

## 11. 禁止事項

- 推測でコードを書き始める（データを見てから書く）
- 動作確認済みのベースラインを上書きする（新ファイル or 新 config で対応）
- 「とりあえず動かしてみる」実験を立てる（仮説と事前予測を書いてから）
- `experiments.md` を更新せずに次の実験に進む
- **同一定式化を 3 連続で掘る**
- **「未読」の調査 TODO を次セッションに送る**
- **根拠データ無しに手法の優先度を下げる**
- **提出 0 回の週を作る**
- **md の中身をチャットに貼って人間に読ませる**（ダッシュボードを再生成して差分だけ述べる）

---

## 12. 新コンペの立ち上げ

**コンペごとに新しいリポジトリを作る。** このリポジトリから「汎用の仕組み」だけをコピーする。

```bash
bash scripts/new_repo.sh ~/Documents/code/<new>_kaggle <前コンペ名>
cd ~/Documents/code/<new>_kaggle && git init && git add -A && git commit -m 'init from template'
```

コピーされるもの: `CLAUDE.md` / `.claude/`（commands + settings）/ `docs/_templates/` /
`scripts/build_dashboard.py` / `scripts/new_repo.sh` / Docker まわり / `pyproject.toml` /
`conf/config.yaml` + `conf/model/lgbm.yaml` / `README.md` / `.gitignore`。

コピーされないもの: `src/` / `scripts/{train,make_submission,analyze_*,visualize_*}.py` /
`kaggle_kernel/` / `conf/{data,train}/` / `notebooks/` / `data/` / `outputs/`。
**前コンペの実装は持ち込まない。** 参照したくなったら旧リポジトリの git 履歴から引く。

第2引数以降に渡した過去コンペは `docs/_archive/{名前}/` として**知識だけ**（postmortems /
formulations.md / gates.md / research）が入る。`_` 始まりなのでダッシュボードの
コンペ自動判定からは除外される。

### コピー後にやること

1. `.env` を作る（`KAGGLE_USERNAME` / `KAGGLE_KEY` / `WANDB_API_KEY`）
2. `pyproject.toml` の依存を見直して `uv lock` — **Gate S3 の NN 系（torch / timm 等）を忘れない**
3. `docker compose up --build -d`
4. Claude Code を起動して **`/kaggle-new <competition-slug>`**
5. データを `data/raw/` に置く

---

## 13. 過去コンペの資産

そのコンペを戦ったリポジトリでは `docs/{コンペ名}/`、`new_repo.sh` でコピーした先では
`docs/_archive/{コンペ名}/`（`_` 始まりなのでダッシュボードの自動判定から外れる）。

| コンペ | 結果 | 主な学び（上記ディレクトリ内の相対パス） |
|---|---|---|
| rogii2026 | 4365位 / 6125（private 12.693、提出 1 回） | `postmortems/pm002_competition_retrospective.md` — **本ファイルの全ルールの由来**。`research/top_solutions.md` に上位解法、`formulations.md` に「定式化ボードがあれば何が並んだか」の事後再構成 |

**新しいコンペを始める前に、直前コンペの postmortem を必ず読み直す。**
