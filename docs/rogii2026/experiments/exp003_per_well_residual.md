# exp003: ウェル別残差分析

## 仮説

exp001 baseline（trajectory+GR特徴のみ, OOF 14.28）は、(a) tail が長いウェル、(b) TVT変化が急峻な
レジーム（rare, `tvt_diff_abs > 0.91`）の行比率が高いウェル、のいずれかで系統的にRMSEが悪化している。
pm001（beam alignment, ABANDONED）で観察された「少数ウェルでtrue TVTの急峻な変化に追従できず大きく
外れる」パターンが、beam特徴を使わないbaselineでも同様に少数ウェルの外れ値として現れているはず。

## 事前予測

- ウェル別RMSEの分布は右に長い裾を持つ（少数の外れ値ウェルが全体平均14.28を引き上げている）
- tail長（ウェルあたりの予測対象行数）とウェル別RMSEは正の相関（長い予測区間ほど誤差が蓄積）
- rare行比率の高いウェルはRMSEが高い（regime別RMSEの差 13.84 vs 14.28 [exp001] と整合的）

## 設定

- 親 config: `conf/config.yaml`（`train.enable_beam_features=false` がデフォルト、exp002の悪化を踏まえ変更なし）
- baseline再学習: `python scripts/train.py wandb.run_name=20260629_lgbm_baseline_rerun`
  （`outputs/oof.parquet` を exp002 時点の値から baseline 相当に作り直すため）
- 分析: `scripts/analyze_per_well_rmse.py`（新規、ウェル別RMSE集計・外れ値抽出・散布図/ヒストグラム生成）

## 実際の結果

`outputs/oof.parquet`（baseline再学習後、`20260629_lgbm_baseline_rerun`）に対し
`scripts/analyze_per_well_rmse.py`（n_wells=773）を実行。

- 全体OOF RMSE: **14.2796**（exp001と一致、baseline再現確認OK）
- ウェル別RMSE: mean **11.60** / median **9.74** / p90 **20.15** / max **72.35**
- **事前予測①（右に長い裾）: 支持された** — ヒストグラム（`eda/fig/exp003_rmse_histogram.png`）は
  明確に右裾が長く、上位 ~10% のウェル（RMSE>20ft）が平均を引き上げている
- **事前予測②（tail長との正相関）: 支持されなかった** — corr(RMSE, n_rows) = **0.099**（ほぼ無相関）
- **事前予測③（rare行比率との正相関）: 支持されなかった** — corr(RMSE, rare_frac) = **0.004**（無相関）。
  worst 10ウェルはすべて `rare_frac` が 0.0000〜0.0005 とほぼゼロ
  （`eda/fig/exp003_per_well_rmse.csv` 参照）

**追加分析（事前予測が外れたため深掘り）**: worst wellsの true vs pred TVTプロット
（`eda/fig/exp003_worst_wells.png`）を見ると、rareな急峻ジャンプではなく **tail全体にわたる
緩やかだが大きいドリフト**にモデルが追従できていないパターンが多い。`oof_pred`の予測変動量
（標準偏差）を真のTVT標準偏差で割った比率を実際に計算したところ:

| well_id | true_std | pred_std | pred/true比 | パターン |
|---|---|---|---|---|
| 1b1eba53 | 25.4 | 3.3 | 0.13 | 予測ほぼ平坦 |
| 86454a6f | 24.6 | 4.5 | 0.18 | 予測ほぼ平坦 |
| **896d15b9** | **17.2** | **15.3** | **0.89** | **予測は動くが方向誤り** |
| 389ae58f | 13.8 | 4.7 | 0.34 | 予測ほぼ平坦 |
| a959858c | 14.8 | 3.6 | 0.24 | 予測ほぼ平坦 |
| **a8ed028a** | **7.5** | **11.6** | **1.54** | **予測が過剰変動・方向誤り** |
| 94d813a4 | 22.0 | 6.0 | 0.27 | 予測ほぼ平坦 |
| c8d9680c | 17.3 | 1.9 | 0.11 | 予測ほぼ平坦 |
| f88ddb26 | 21.9 | 3.9 | 0.18 | 予測ほぼ平坦 |
| 91b301ce | 33.3 | 4.8 | 0.14 | 予測ほぼ平坦 |

8/10は「予測が平坦に留まる」パターン（比0.11〜0.34）だが、**2/10は予測が大きく動くのに
方向を間違えている別パターン**であり、一律に「平坦」とは言えない。

次に worst 10ウェルで「true TVTのtail内ネット変位」と「-Z（trajectory変位）のtail内ネット
変位」を比較した（-Zは`tvt_regime.md`でCorr(TVT,-Z)=0.917と報告されているが、
**これは1本目ウェルの例のみで773ウェル全体での検証なし**）:

| well_id | true TVTドリフト | -Zドリフト | 符号一致 |
|---|---|---|---|
| 1b1eba53 | +70.9 | +94.1 | ○ (ratio 0.75) |
| 86454a6f | +79.2 | +307.6 | ○ (ratio 0.26) |
| 896d15b9 | +19.9 | -175.7 | **✗ 符号反転** |
| 389ae58f | +51.7 | +188.4 | ○ (ratio 0.27) |
| a959858c | +89.2 | +276.0 | ○ (ratio 0.32) |
| a8ed028a | +16.2 | -88.6 | **✗ 符号反転** |
| 94d813a4 | -54.9 | -191.8 | ○ (ratio 0.29) |
| c8d9680c | +33.0 | -236.1 | **✗ 符号反転** |
| f88ddb26 | -41.0 | +54.7 | **✗ 符号反転** |
| 91b301ce | -91.0 | -282.2 | ○ (ratio 0.32) |

corr(RMSE, abs_net_drift) = **0.580**、corr(RMSE, total_variation) = 0.323（n_rowsの0.099・
rare_fracの0.004より大幅に強い）。

## 考察

事前予測（tail長・rare比率）は誤りだった。実際の系統的弱点は **「tail内でTVTが大きく単調に
変位するウェル（corr(RMSE, abs_net_drift)=0.580）」**であり、その中でもtrajectory(-Z)の変位と
実TVTの変位が食い違う（4/10で符号反転）ウェルが最悪。

**検証済み事実（追加分析より）**:

1. **モデルはtrajectory系特徴全体を圧倒的に優先している（GRはほぼ無視）**: 5-fold LightGBMモデルの
   feature importance（gain）を実際に集計した結果:
   - trajectory系（last_known_TVT, X, Y, delta_Z, delta_Y, delta_X, Z, neg_Z, delta_MD, MD）:
     合計 **約94%**
   - GR系（gr_cal, gr_roll_mean/std各3窓, gr_gradient）: 合計 **約1.9%**
   - ~~「-Zを強い事前情報として使う」~~ → 訂正: `neg_Z` 単体は5.4%に過ぎず、
     **X(16.5%), Y(14.4%), delta_Z(11.7%)など位置・変位の方が支配的**。
     「-Z依存」ではなく「trajectory全体に強く依存しGRをほぼ無視」が正確。

2. **worst 10ウェルでの予測挙動は2パターン存在**:
   - 8/10: 予測がanchor付近にほぼ平坦に留まり、真のTVT大変位に追従できない（pred/true_std比 0.11〜0.34）
   - 2/10 (896d15b9, a8ed028a): 予測が大きく動くが方向が誤り（neg_Zとの相関 0.92〜0.95、
     しかしtrue TVTとneg_Zが逆相関のウェル）

3. **構造的傾斜が原因という仮説は部分的に支持、ただし全ウェル未検証**:
   worst 2ウェル（1b1eba53, 86454a6f）の地層サーフェス列（ASTNU等、train専用・モデル未使用）が
   tailの中でstd 24〜78ftの大きなシフトを示し、かつ全サーフェスが同量だけ一斉に動く
   （整合的な地層傾斜と矛盾しない）ことを確認。**ただしこれは2ウェルのみの観察で、
   773ウェル全体でのシステマティックな検証は未実施**。因果の確定は保留。

これはpm001（beam alignment失敗）の「急峻なTVT変化への追従失敗」とは異なるメカニズム:
pm001は**短い区間での急変**への追従失敗、exp003は**長いtailにわたる持続的な大きなネット変位
（trajectory系特徴と整合しない）**への追従失敗。対策も別になる可能性が高い。

## 次のアクション

- [x] baseline再学習・分析スクリプト実行・結果記録
- [ ] **H9アンサンブル（PF/beam/DTW/NCC + CatBoost + Ridge stack）に着手する際、
  trajectory系特徴とGR系列由来の整列結果が食い違うウェルを優先的にターゲットする**
  （GR系列アンサンブルはtrajectory非依存の情報源のため、このdecoupled wellsで効くはず）
- [ ] 新規仮説候補（H10）: 「trajectoryとGRベース整列の不一致度合い」自体を特徴量
  （signed/abs disagreement）として追加すれば、モデルが自信度を調整できLightGBMの予測精度が
  上がるはず → 次の小実験で先に検証してからH9着手でも良い
- [ ] tail長・rare比率は今回反証されたため、exp004（後処理スムージング）・exp005（空間特徴）
  より優先度を下げる

## 関連実験
- exp001（baseline）, exp002（beam alignment, ABANDONED）
- `postmortems/pm001_beam_alignment_drift.md`（少数ウェル外れ値という同種パターンの初出）
