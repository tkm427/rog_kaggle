# EDA: データ構造・基本統計

実行日: 2026-06-16  
スクリプト: `scripts/eda_overview.py`

## ウェル数・行数

| 項目 | 値 |
|---|---|
| Train wells | 773 |
| Test wells | 3 (`000d7d20`, `00bbac68`, `00e12e8b`) |
| Train 総行数 | 5,092,255 |
| Prefix（既知 TVT_input）行数 | 1,308,266 |
| Tail（隠れ TVT）行数 | 3,783,989 |
| Tail 割合（ウェル平均） | 73.3% ± 6.4% |

## カラム構成

### `horizontal_well.csv`（train）
```
MD, X, Y, Z, ANCC, ASTNU, ASTNL, EGFDU, EGFDL, BUDA, TVT, GR, TVT_input
```
- 地層サーフェス列（ANCC〜BUDA）は **train にのみ存在**。test CSV には無い。

### `horizontal_well.csv`（test）
```
MD, X, Y, Z, GR, TVT_input
```
- `TVT` 列なし（これが予測対象）。地層サーフェス列なし。

### `typewell.csv`
```
TVT, GR, Geology
```
- X/Y/Z 座標なし。`well_id` で対応付けるのみ。
- `Geology` に形成名（ANCC, ASTNU, EGFDU... 等）がラベル付きで入っている。

## ウェル長さ分布

| 統計量 | 値（行数） |
|---|---|
| mean | 6,588 |
| std | 1,312 |
| min | 2,058 |
| 25% | 5,706 |
| median | 6,576 |
| 75% | 7,388 |
| max | 12,141 |

→ MD は 1ft ステップ換算で **約 6,500ft（≈ 2km）** が中央値。

## TVT の値域

| 項目 | 値 |
|---|---|
| 全 train の TVT min | 9,245 ft |
| 全 train の TVT max | 12,894 ft |
| 典型的なウェル内 TVT 範囲 | 〜727 ft（平均） |

## GR 統計

| 対象 | mean | std |
|---|---|---|
| Horizontal well (train 全体) | 88.1 | 17.9 |
| Typewell（000d7d20 例） | 83.3 | 26.3 |

→ レンジは概ね重なるが typewell のほうが std が大きい傾向。

## Prefix/Tail 境界の確認

- 境界は **単一の clean な切れ目**（transitions = 2 = prefix→tail の 1 回のみ）。
- `TVT_input == TVT` が prefix 全行で **100% 一致**（target-free ではなくアンカーとして使える）。
- `last_known_TVT`（Prediction Start 直前の TVT_input）がアンカーとして利用可。

## Typewell カバレッジ

- Typewell の TVT ステップ: **0.487 ft**（横坑井の MD 1ft より細かい）。
- 横坑井の TVT 範囲が Typewell に完全に包含されるケース: **97 / 100**（サンプル）。
- → DTW マッチングの前提が 97% のウェルで成立。

## 空間分布

- 全 train ウェルの空間範囲: X ≈ 56km、Y ≈ 41km
- 各坑井の軌跡は短い（test ウェルで X/Y 幅 ≈ 100〜5000ft ≈ 0.03〜1.5km）

## Test ウェルのアンカー TVT

| Well | last_known_TVT (ft) | Tail 行数 |
|---|---|---|
| 000d7d20 | 11,747.37 | 3,836 |
| 00bbac68 | 12,223.54 | 6,014 |
| 00e12e8b | 11,604.82 | 4,301 |

→ Flat anchor（`tvt = last_known_TVT` で全 tail を埋める null model）が最低限の baseline。
