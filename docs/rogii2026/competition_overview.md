# ROGII - Wellbore Geology Prediction: コンペ概要

> このファイルは **静的なコンペ仕様** をまとめた決定版ドキュメント。コンペ中の戦略変更や実験ログは別ファイル（`strategy.md` / `experiments.md`）に書く。

## 基本情報

| 項目 | 内容 |
|---|---|
| URL | https://www.kaggle.com/competitions/rogii-wellbore-geology-prediction |
| ホスト | ROGII |
| タイプ | Featured **Code Competition**（Notebook 提出） |
| 開始日 | 2026-05-05 |
| 最終提出締切 | 2026-08-05 23:59 UTC |
| 賞金プール | $50,000 |
| 引用 | Igor Kuvaev, Rafael Aguilar, John Granmayeh, Ryan Holbrook, María Cruz, Ashley Oldacre. *ROGII - Wellbore Geology Prediction*. Kaggle, 2026. |

## タスク

**回帰問題**: 水平坑井（horizontal wellbore）の評価ゾーンにおける TVT (True Vertical Thickness、真の鉛直層厚、ft) を予測する。

### TVT とは
- 水平掘削中の坑井が、地質層スタックのどの位置にあるかを表す指標。
- 通常は地質学者が手動で解釈する作業（**geosteering**）の中核アウトプット。
- 本コンペはこの解釈を機械学習で自動化することが目的。
- 物理的には深度方向に **連続かつ滑らか** であり、急峻なジャンプは層境界跨ぎで発生する。

## 評価指標

**RMSE (Root Mean Squared Error)**: 全テスト行の予測 `tvt` と真値の二乗誤差の平均の平方根。

$$
\text{RMSE} = \sqrt{\frac{1}{N} \sum_{i=1}^{N} (\hat{y}_i - y_i)^2}
$$

低いほど良い。外れ値の影響を受けやすいので、後処理クリッピング・スムージングが効きやすい指標。

## データ構成

`train/` / `test/` 配下、ウェルごとに 8 桁ハッシュ ID（例: `015fe0d2`）で管理。

| ファイル | 内容 |
|---|---|
| `{WELLNAME}__horizontal_well.csv` | 水平坑井の軌跡 + 地質層境界 + ログ。評価ゾーンの `tvt` は NaN |
| `{WELLNAME}__typewell.csv` | 同エリアの垂直リファレンス坑井ログ（タイプウェル） |
| `sample_submission.csv` | 提出フォーマット |

**注意**: 配布された `test/` には学習データから抜粋した数本のみが入っている。実際の採点時には隠されたテストデータと差し替えられる（Code Competition のリラン方式）。

### `horizontal_well.csv` の主要カラム
- `WELLNAME`: ウェルの一意な識別子（pilkwang Notebook の前処理データでは結合キーが `well_id` という名前で登場。同一の ID に対応する可能性が高いが要 EDA 確認）
- `MD` (Measured Depth, ft): 坑井経路に沿った全長
- `X` (Easting, ft): 水平面上の東西座標
- `Y` (Northing, ft): 水平面上の南北座標（推定）
- `Z` / `TVD` (True Vertical Depth, ft): 鉛直深度（推定）
- `GR` (Gamma Ray): 自然ガンマ線。シェール（高 GR）と砂岩（低 GR）を区別する基本ログ
- `TVT` / `tvt`: ターゲット。評価ゾーンでは NaN
- `TVT_input`: 評価ゾーン外で部分的に与えられる TVT 系列のヒント。known prefix では `TVT_input == TVT` （pilkwang Section 6 で確認済み）なので `last_known_TVT` を anchor として使える。**境界条件として強力だがリーク管理が必須 → 「リーク管理」セクション参照**
- **train のみに存在する地質層境界（formation surface）列**: `ANCC`, `ASTNU`, `ASTNL`, `EGFDU`, `EGFDL`, `BUDA`（6 種）。hidden test には存在しないため、直接特徴量にはできない。空間 imputer（`(X,Y) -> formation top`）を train のみでフィットし、val/test に投影する形でのみ利用可（pilkwang Section 5）


**参考（pilkwang Notebook Task Snapshot より、pilkwang が使用したローカルデータの規模感）**: train wells 773 / train tail rows（hidden 区間に相当する行数）3,783,989 / 配布 test wells 3 / 提出行数 14,151。隠れテストではウェル数・行数が大きく増える前提で実装する。

### `typewell.csv`（タイプウェル）
- 水平坑井の近隣にある垂直坑井のログ。
- 地質層の鉛直方向のリファレンス。
- **水平坑井の GR とタイプウェルの GR を相関させて層内の位置（= TVT）を推定するのが伝統的アプローチ。**

## 提出フォーマット

```
id,tvt
000d7d20_1442,0.0
000d7d20_1443,0.0
000d7d20_1444,0.0
```

- `id` = `{WELLNAME}_{row_index}`
- `tvt` = 予測値（ft）

評価ゾーンの行のみを提出する（学習データの行ではない）。

## Code Competition の制約

| 項目 | 値 |
|---|---|
| 提出方式 | Kaggle Notebook |
| インターネット | OFF（提出時） |
| ランタイム上限 | CPU Notebook <= 9 hours run-time |
| GPU | GPU Notebook <= 9 hours run-time |
| 最終提出選択数 | 2 |


## 稀少 / 頻出の定義（本コンペ用解釈）

CLAUDE.md の `val_score_rare` / `val_score_common` は分類タスクを想定した命名。本コンペは回帰なので以下のように読み替える。

- **`val_score_rare`** → **稀少レジーム RMSE**: 急峻な層境界跨ぎ・ジャンプ・通常レンジ外の TVT を含む区間の RMSE
- **`val_score_common`** → **通常レジーム RMSE**: なだらかで連続的な区間の RMSE

具体的な閾値は EDA で TVT の差分分布を見て決める（例: `|d_TVT/d_MD| > 95 パーセンタイル` を稀少と定義）。`eda/tvt_regime.md` で正式化。

## ドメイン用語ミニ辞書

| 用語 | 意味 |
|---|---|
| Geosteering | 水平掘削中に地質情報をもとに掘削方向をリアルタイム調整する作業 |
| TVT (True Vertical Thickness) | ある点における層の鉛直厚み |
| TVD (True Vertical Depth) | 表面からその点までの鉛直距離 |
| MD (Measured Depth) | 坑井経路に沿った距離 |
| TST (True Stratigraphic Thickness) | 層に垂直方向に測った厚み |
| Dogleg Severity (DLS) | 坑井の曲率（角度変化率） |
| Typewell | 同フィールドの垂直リファレンス坑井 |
| Stratigraphic Surface | 地質層境界面 |
| GR (Gamma Ray) | 自然ガンマ線量。岩相判別の基本ログ |
| LAS (Log ASCII Standard) | 坑井ログの業界標準ファイル形式 |
| BHA (Bottom Hole Assembly) | 坑底掘削組立 |

## リーク管理: Information Policies and Leakage Rules

> 出典: pilkwang Notebook「🛢️ ROGII EDA + Target-Free Alignment for TVT」（LB **8.099**, best 8.072）Section 0 / 0.1 / 0.2 / 5。詳細メモは `research/public_notebooks.md` 参照。特徴量を作る前に必ずこのセクションで「Strict / Offline どちらの policy か」「Allowed か Excluded か」を確認する。

### Two-track information model

| Policy | 使ってよい情報 | 使ってはいけない情報 | 用途 |
|---|---|---|---|
| **Strict (drilling-time)** | prefix + 現在/直前行までの evidence | 未来の tail 形状、centered window、tail 長 | geosteering 的な保守的検証 |
| **Offline (batch)** | test CSV に含まれる covariate 全体（未来の `MD/X/Y/Z/GR` を含む） | 未来の `TVT`、target 由来の summary | Kaggle 提出候補 |

> **鉄則**: Offline 特徴は test ファイルに含まれる未来の **GR / trajectory** を見てよいが、未来の **TVT** は絶対に見てはならない。

### Allowed / Excluded 特徴量ファミリー

| Feature family | Strict | Offline | 理由 |
|---|:---:|:---:|---|
| 現在行の `MD/X/Y/Z/GR` | ✅ | ✅ | 観測済み covariate |
| prefix `TVT_input` | ✅ | ✅ | 既知の target prefix |
| trailing GR window | ✅ | ✅ | 未来行を見ない |
| centered GR / lead-lag GR | 🚫 | ✅ | 未来 covariate（target-free） |
| tail length / tail fraction | 🚫 | ✅ | batch モードでのみ既知 |
| candidate-path typewell 特徴 | 🚫 | ✅ | tail 全体の位置を使うパス |
| beam alignment | 🚫 | ✅ | hidden GR からのシーケンス特徴 |
| train-only surfaces を直接使用 | 🚫 | 🚫 | hidden test に列が無い |
| fold-safe formation imputer 出力 | 🚫 | ✅ | 再現可能な空間参照モデル経由なら OK |
| tail `TVT` ラベル | 🚫 | 🚫 | 直接的な target leakage |

### Leakage Risk Table（pilkwang Section 0.1）

| Risk source | 何が起きるか | Guardrail |
|---|---|---|
| train/test で同じ well id が重複 | 同一ウェルの空間ヒントが、未知ウェルへの汎化より強く見えてしまう | overlap を許可した selector と禁止した selector の両方で比較する |
| PF selector の same-well physical branch | public score が overlap 依存のショートカットに支配される | `PF_SELECTOR_USE_SAME_WELL_PHYSICAL=True` は public-aggressive とみなし、ロバスト性診断には `False` を使う |
| 行単位のランダム分割 | 同一ウェル内の自己相関が fold 間でリークする | `GroupKFold(well_id)` を使う |
| train-only な地層サーフェス列（`ANCC`等） | hidden test にはこの列が存在しない | 空間 imputer 経由でのみ使う |
| prefix `TVT_input` | Prediction Start より前でのみ有効 | prefix 行のみに使う |
| tail length / centered window | 未来 covariate | offline 特徴としてのみ使う |
| true tail TVT alignment | 直接的な target leakage | hidden-tail の target 値は絶対に使わない |
| GR calibration | tail GR でキャリブレーションすると局所ノイズに過学習する | affine GR calibration は prefix のみでフィットする |

💡 **Anchor sanity check**: $H_0: y_{w,i} = y_{w,PS-1}$（flat anchor、`last_known_TVT` を予測区間全体にコピーするだけの null model）。安定ウェルではこれを破るのが難しい。residual 特徴は drifting ウェルを改善しつつ flat ウェルを悪化させないことが目標。

### Public/Private Feature Policy（pilkwang Section 0.2）

同じ特徴量でも評価設定によって安全性が変わる。直接的な target leakage か否かだけでなく、**train/test の well 重複に依存するか** が重要な軸。

| Signal family | Direct target leakage? | Public/PB での振る舞い | Private/汎化リスク |
|---|:---:|---|---|
| prefix `TVT_input` 統計量 | No | 安定した anchor | 低い（prefix 行のみ使う限り） |
| hidden GR 全シーケンス | No | 強い batch signal | 中（hidden log 全体が推論時に使える前提） |
| centered GR window | No | offline batch で有用 | リアルタイム geosteering では不可だが Kaggle batch 推論では許容 |
| formation 列を直接コピー | hidden 推論では Yes | test で再現不可 | 除外すべき |
| 空間的に imputed された formation surface | No（val/test target を使わずにフィットする限り） | 有用な地質 prior | 空間外挿の質に依存 |
| same-well physical/contact path | hidden-tail TVT は読まない | public test が train ウェルと重複していれば非常に強い | private ウェルが未重複・構造的に異なる場合は高リスク |
| PF/beam selector（GR/typewell 由来） | hidden-tail TVT は読まない | 強い target-free alignment signal | typewell 相関と GR ギャップ品質に依存 |

> `PF_SELECTOR_USE_SAME_WELL_PHYSICAL=True` で得た高スコアは「overlap を利用した地質的ショートカット」であり、「未知ウェルへの汎用的な保証」ではない。`True`/`False` 両方で比較するのが診断ペア。

### Column Role Map（pilkwang Section 5）

| Role | 例 | 使い方 |
|---|---|---|
| Observable covariates | `MD`, `X`, `Y`, `Z`, `GR`, typewell logs | 行特徴として直接使用可 |
| Known-prefix target | prefix `TVT_input` | anchor、prefix 統計量、GR calibration のペア |
| Hidden-tail target | tail `TVT` | train/CV のラベルとしてのみ。**特徴量には絶対使わない** |
| Train-only formation surfaces | `ANCC`, `ASTNU`, `ASTNL`, `EGFDU`, `EGFDL`, `BUDA` | fold-safe な空間 imputer の補助ラベルとしてのみ |

- **Safe pattern**: ① train ウェルだけで `(X,Y) -> formation top` をフィット → ② `formation_hat(X,Y)` を val/test 行に投影 → ③ `TVT ≈ -Z + formation_hat + prefix_bias` で target-free な式を作る。
- **Unsafe pattern**: `ANCC` 等を直接特徴に使う（hidden test に無い）／ GroupKFold の検証ウェルを imputer のフィットに混ぜる（fold leakage）／ tail `TVT` summary や bfill 値（`TVT_input_bfill` 等）を使う（直接的な answer-key leakage）。

## このコンペ固有の落とし穴

1. **リーク管理が極めて重要**: `TVT_input` の与え方や評価ゾーンの定義により、推論時に使ってよい情報・使ってはいけない情報の境界が複雑。詳細は上記「リーク管理」セクション（pilkwang Notebook Section 0/0.1/0.2/5 を反映）を参照。特に **train/test の well id 重複**は public score と private score で意味が変わるため要注意。

2. **時系列性（深度順）**: ウェル内では MD 順に物理的に連続する。Random shuffle 検証は致命的に危険。**GroupKFold（ウェル単位）必須**。

3. **ウェルごとに長さが異なる**: 数千〜数万行までばらつく可能性。バッチ化で注意。

4. **物理的滑らかさ**: TVT は本来連続関数なので、後処理スムージング（Savitzky-Golay / ガウシアン）で RMSE が改善するケースが報告されている（ravaghi Notebook 等）。

5. **タイプウェルとの相関**: GR の **DTW (Dynamic Time Warping)** マッチングが古典的かつ有力。Target-Free Alignment という言葉で公開 Notebook にも登場（pilkwang）。

6. **隠れテストでの I/O 量**: Code Competition のリラン時に test ウェル数が大幅に増える可能性。`make_submission.py` は **メモリ・推論時間を意識して実装** すること。
