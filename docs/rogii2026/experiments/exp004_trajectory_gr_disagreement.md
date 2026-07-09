# exp004: trajectory-GR不一致度特徴量（H10）

## 仮説

exp003でLightGBMはtrajectory系特徴を94%使用し、GR系をほぼ無視（1.9%）していると判明。
worst 10ウェルのうち4/10でtrajectory(-Z)のネット変位とTVTのネット変位の符号が逆転しており、
モデルがこの「trajectoryを信用すると危険な区間」を検出できないことが根本原因。

「trajectoryとGRの不一致度」を特徴量として明示的に与えれば、LightGBMが
「このウェルではtrajectory予測を信用しない」という学習が可能になり、系統誤差が減るはず。

## 事前予測

- 全体 OOF RMSE: 14.28 → **13.5〜13.9** (-0.4〜0.8程度の改善) を期待
- rare RMSE: ほぼ変化なし（符号反転はrare regimeとは別問題）
- common RMSE: -0.3〜0.5程度の改善（tail全体にわたるドリフトが主要ターゲット）
- worst 10ウェルのうち符号反転4ウェル（896d15b9, a8ed028a, c8d9680c, f88ddb26）のRMSE改善を特に期待
- feature importance: `prefix_corr_negz_tvt_diff` が新特徴量の中で最上位に来るはず

## 設定

- 親 config: `conf/config.yaml` + `conf/train/default.yaml`
- 変更: `conf/train/exp004.yaml`（`train.enable_disagreement_features=true`）
- 追加特徴量（9個）:
  - Group 1（prefix相関, ウェルレベル broadcast）: `prefix_corr_negz_tvt`, `prefix_corr_gr_tvt`, `prefix_corr_negz_tvt_diff`, `prefix_corr_gr_tvt_diff`
  - Group 2（rolling GR-negZ gradient 相関, 行レベル）: `gr_negz_roll_corr_10`, `gr_negz_roll_corr_30`, `gr_negz_roll_corr_100`
  - Group 3（typewell GR最近傍, 行レベル）: `gr_nn_tvt_delta`, `gr_nn_cost`
- 実行コマンド:
  ```bash
  docker compose exec workspace python scripts/train.py \
    train=exp004 \
    wandb.run_name=20260705_lgbm_traj_gr_disagreement
  ```
- W&B Run: `20260705_lgbm_traj_gr_disagreement`

## 実際の結果

- 全体 OOF RMSE: **14.3241**（baseline 14.28 より **+0.04 悪化**）
- rare RMSE: **14.3037**（baseline 13.84 より **+0.46 悪化** — 想定外）
- common RMSE: **14.3241**（baseline 14.28 より +0.04 悪化）
- LB RMSE: 未提出（OOFが悪化したため）

**ウェル別の内訳（符号反転4ウェル）:**

| well_id | exp003(baseline) | exp004 | 変化 |
|---|---|---|---|
| 1b1eba53 | 72.35 (max) | 63.74 | -8.6 改善 |
| a8ed028a | top10入り | ~33.8 | top10圏外へ改善 |
| c8d9680c | top10入り | 49.39 | ほぼ変化なし |
| f88ddb26 | top10入り | 43.47 | ほぼ変化なし |

- worst 10全体は max=63.74 / mean p90=20.38（baseline: max=72.35 / p90=20.15）
- **新たに top10に入ったウェル**: 2fd68f7b, ba48188d, 5f4d2a52（regression）

## 考察

事前予測（全体 -0.4〜0.8改善）は**反証**された。全体では僅かに悪化し、rareで大きく悪化。

**部分的には仮説が支持された**:
- 符号反転ウェル（a8ed028a, 1b1eba53）は改善 → 新特徴量が「trajectory非依存ウェル」に対し効いた
- しかし他のウェルで regression が発生し、全体を相殺

**悪化の原因仮説:**

1. **Group 3（gr_nn_tvt_delta）がノイズ**: GR最近傍マッチングは順序制約なしのため、typewell内で同じGR値が複数の深度に存在する場合に予測が不安定。特にrare（境界跨ぎ）行でGRが急変する区間でノイズが大きいと考えられる（rareで-0.46が示唆）
2. **Group 2（gr_negz_roll_corr）の情報量が薄い**: GRとneg_Zはもともと直接の相関が弱く、局所窓での相関はほぼランダム → LightGBMが過学習
3. **Group 1（prefix相関）は一部有効だが単独では効果が限定的**: 符号反転ウェルでは効いたが、full tailでのドリフト問題全体に対しては不十分

**教訓**:
- 「GRと-Zの不一致度」を直接特徴量にする前に、prefix-tail間で相関構造が保たれるかを確認すべきだった
- GR NN（順序制約なし）は beam searchの失敗と類似した問題を抱えている可能性

## exp004b 追加結果（2026-07-06）

prefix相関4特徴のみ（disagreement_groups=[1]）で再検証:
- Overall: 14.2955 / rare: 13.9856 / common: 14.2955
- exp004(14.32)からは改善 → ノイズ源除去仮説は確認
- ただし baseline(14.28)には届かず

**H10アプローチ終了の結論**: 「ウェルレベルのスカラー信頼度フラグ」はLightGBMが
他特徴量を動的に下重みする手段を持たないため、構造的に限界がある。
trajectory-GR不一致度を活かすには、それを直接使う別モデル（アンサンブルのstacking等）が必要。

## 次のアクション

- **H3（後処理スムージング）** または **H9（GR系列アンサンブル）** に移行
- postmortem 不要（差が小さく教訓はここに記載済み）

## 関連

- exp001（baseline, OOF 14.28）
- exp003（残差分析: trajectory-TVTデカップリング発見）
- `docs/rogii2026/strategy.md` H10仮説
