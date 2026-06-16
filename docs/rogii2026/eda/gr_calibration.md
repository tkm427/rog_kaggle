# EDA: GR キャリブレーション特性

実行日: 2026-06-16  
スクリプト: `scripts/eda_overview.py`（インライン実行）

## GR シフト（typewell − horizontal）の分布（200 wells サンプル）

| 統計量 | GR shift (API) |
|---|---|
| mean | +4.93 |
| std | 9.48 |
| p10 | -6.71 |
| p50 | +4.85 |
| p90 | +15.57 |
| min | -22.29 |
| max | +41.22 |

- **31%（62/200）のウェルで 10 API 超のシフトが必要。**
- シフトはウェルごとに大きくばらつく → DTW マッチング前に affine calibration が重要。

## 含意

### Affine GR Calibration（推奨）
```
hw_GR_cal = hw_GR + (tw_GR_mean(prefix TVT range) - hw_GR_mean(prefix))
```
- Prefix の TVT 範囲に対応する typewell セグメントで平均を合わせる。
- **Prefix 行のみでフィット**（tail の GR でキャリブレーションすると target leakage に近い）。
- スケールも合わせる場合: `hw_GR_cal = (hw_GR - hw_mean) / hw_std * tw_std + tw_mean`

### ウェル別の例

| Well | prefix GR mean | typewell GR mean | shift |
|---|---|---|---|
| 000d7d20 | 87.4 | 86.2 | -1.3 （小さい） |
| 00bbac68 | 88.9 | 94.7 | +5.7 |
| 00e12e8b | 85.0 | 102.3 | **+17.3** （大きい） |
| 01869cd4 | 85.2 | 78.5 | -6.7 |

→ `00e12e8b` のように 17 API のシフトが必要なケースがあり、キャリブレーションなしでは DTW が失敗する。

## まとめ

GR キャリブレーション（affine shift、少なくとも mean shift）は DTW の前処理として**必須**。  
pilkwang Notebook でも prefix-only calibration が実装されている。
