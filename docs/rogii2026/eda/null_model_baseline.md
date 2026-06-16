# EDA: Null Model（Flat Anchor）の RMSE

実行日: 2026-06-16  
スクリプト: `scripts/eda_overview.py`

## Null Model の定義

**Flat Anchor**: `predicted_TVT = last_known_TVT_input`  
（Prediction Start 直前の `TVT_input` を tail 全体に対してコピー）

コードで言えば:
```python
anchor = df[df['TVT_input'].notna()]['TVT_input'].iloc[-1]
df.loc[df['TVT_input'].isna(), 'tvt_pred'] = anchor
```

## Train データ上での RMSE

| 統計量 | RMSE (ft) |
|---|---|
| Overall（全 tail 行合算） | **15.91** |
| Per-well mean | 12.81 |
| Per-well median | 10.67 |
| Per-well std | 8.90 |
| Per-well min | 1.12 |
| Per-well max | 70.64 |

- RMSE > 10 のウェル: 414 / 773（53%）
- RMSE < 5 のウェル: 77 / 773（10%）

## 公開ベースラインとの比較

| モデル | RMSE (LB) |
|---|---|
| Flat anchor（null、train 推定値） | 15.91 |
| Super baseline (romantamrazov) | 12.60 |
| DWT-based (nihilisticneuralnet) | 9.25 |
| Training NB (rauffauzanrambe) | 9.54 |
| **Target-Free Alignment (pilkwang)** | **8.07** |

→ flat anchor は 15.91 → LB で ~12.6 程度。Super baseline が flat anchor より僅かにマシな程度。
→ Target-Free Alignment（DTW）で 8.07 まで改善。ここが現在のベンチマーク。

## 含意

- Flat anchor は「TVT が平坦なウェル（drift しないウェル）」では競争力がある（RMSE < 5 が 77 本存在）。
- 高 RMSE ウェル（drift が大きい）は DTW マッチングで改善できる候補。
- 後処理スムージングは flat anchor の RMSE をほぼ改善しない（既に「平坦」だから）。
  → スムージングは DTW 結果の雑音除去に使う。
