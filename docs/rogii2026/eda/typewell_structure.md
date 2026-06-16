# EDA: Typewell の構造と DTW マッチングへの含意

実行日: 2026-06-16  
スクリプト: `scripts/eda_overview.py`

## Typewell の基本構造

- カラム: `TVT`, `GR`, `Geology`（X/Y/Z なし）
- 結合キー: `well_id`（横坑井と 1:1 対応）
- TVT ステップ: **0.500 ft（完全等間隔）**
- 典型行数: 695〜4437 行（中央値 ≈ 1782 行）

## GR の特性

| 項目 | 値（000d7d20 例） |
|---|---|
| GR range (typewell) | 28.7 〜 158.2 API |
| Corr(typewell GR, TVT) | -0.511 |
| Corr(horizontal GR, TVT) | **0.001**（ほぼ無相関） |

→ 横坑井の GR は TVT と直接相関しない。タイプウェルの GR パターンとのマッチングが必要。

## Geology 列

- 地層形成名のラベル（ANCC, ASTNU, ASTNL, EGFDU, EGFDL, BUDA, LTHL, LTGT, LBHL, MNSS）。
- non-null 行は全体の 77%（サンプル: 997 / 1296）。
- 形成名は `horizontal_well.csv` の train-only サーフェス列名と一致
  → Typewell の Geology ラベルを ground truth として空間 imputer に使う道がある（`competition_overview.md` の Safe pattern 参照）。

## Typewell カバレッジ

- 横坑井の TVT 範囲が Typewell の TVT 範囲に**完全に包含されるケース**: 97 / 100（サンプル）。
- → DTW マッチングの前提（「横坑井が typewell のどの深度にいるか」を推定）が 97% のウェルで成立。

## DTW マッチングへの示唆

- 横坑井の GR（MD 軸）とタイプウェルの GR（TVT 軸）を DTW で整列 → TVT の推定値が得られる。
- 入力は 1D 時系列: `hw_GR[row]` と `tw_GR[tvt_idx]`。
- 整列後に `tw_TVT[matched_idx]` が予測 TVT。
- pilkwang Notebook の「Target-Free Alignment」は本質的にこの操作。

## 注意点

- Typewell に座標情報がないため「どの typewell が最も近いか」は well_id で固定済み（1:1 対応）。
  ただし hidden test で異なる typewell が来る場合の対処は現時点不明。
- GR の calibration（affine 補正）は **prefix 行のみ**でフィットする（tail GR でキャリブレーションすると leakage）。
