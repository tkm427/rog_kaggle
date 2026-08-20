# ゲート宣言（rogii2026）— 事後記入

> **コンペ中には存在しなかったファイル。** 終了後に、実際の到達状況を正直に記入したもの。
> `scripts/build_dashboard.py` のテストデータ兼、次コンペでの見本。
> チェックを入れてよいのは根拠欄に実物を書けるときだけ。

## Phase 1: リサーチ

| 済 | ID | 完了条件 | 根拠（ファイル・件数・実測値） |
|:-:|---|---|---|
| [x] | R1 | `competition_overview.md` 完成 | リーク管理・Column Role Map まで記載済み |
| [ ] | R2 | Discussion upvote 上位10 + host 投稿全件の本文とコメントを読んだ（未読0件） | **未達**。`research/discussions.md` はテンプレのまま。上位2解法の中核が載っていた 62 upvote スレッドを未読のまま終えた |
| [x] | R3 | 類似コンペ TOP5 を要約 | `research/past_solutions.md`（FORCE 2020 TOP3 + SEG 2016） |
| [x] | R4 | 公開 NB 3本を実コードで読み、リーク判定した | `research/public_notebooks.md`。boristown の same-well shortcut を実コードで特定 |
| [ ] | R5 | `formulations.md` に定式化候補 3案以上 | **未達**。当時 F1 しか視野に無かった（`formulations.md` は事後記入） |
| [x] | R6 | `eda/` に発見 3〜5本 | 6本（data_structure / gr_calibration / null_model_baseline / train_test_overlap / tvt_regime / typewell_structure） |

## Phase 2: E2E 提出

| 済 | ID | 完了条件 | 根拠 |
|:-:|---|---|---|
| [x] | S1 | submission が LB にスコアを出した | exp001 → public 12.959 / private 12.693 |
| [x] | S2 | OOF と LB の対応を1点記録 | OOF 14.28 ↔ LB 12.959（1点のみ、相関は未確定のまま終了） |
| [ ] | S3 | 2系統目（NN系）の依存を `uv add` 済み | **未達**。`pyproject.toml` に torch/timm 無し |

## Phase 3: 二系統並走

| 済 | ID | 完了条件 | 根拠 |
|:-:|---|---|---|
| [ ] | T1 | 異なるアーキテクチャ族を2系統、いずれも提出可能な状態 | **未達**。`conf/model/` は lgbm のみ |

## Phase 4: 終盤

| 済 | ID | 完了条件 | 根拠 |
|:-:|---|---|---|
| [ ] | F1 | 新規アーキテクチャ実験を停止 | **未達**。終盤3週間の活動記録なし |
| [ ] | F2 | 提出枠の使い方を `strategy.md` に明記 | **未達** |
| [ ] | F3 | 実データ規模で推論を通し、時間・メモリを実測 | **未達** |
