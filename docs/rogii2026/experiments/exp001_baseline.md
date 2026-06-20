# exp001: Anchor + Trajectory + GR特徴 + LightGBM残差モデル（ベースライン確立）

> CLAUDE.md の「Phase 2: 公開 Notebook を fork してもよい。とにかく `submission.csv` を出す」「ローカル val ↔ LB の相関を1回測定」に対応。
> 当初は公開 Notebook を fork する案だったが、pilkwang Notebook（最高公開スコア）の手法をベースに自前パイプラインを構築する方針に変更（リーク管理・特徴量設計を自分で把握できる利点を優先）。

## 仮説

Flat anchor（null model, train RMSE 15.91、`eda/null_model_baseline.md`）に対し、以下を特徴量として加えた LightGBM 残差モデル（target = `TVT - last_known_TVT`）は明確に改善する:

- Trajectory 変位特徴（`delta_X`, `delta_Y`, `delta_Z`: prediction start からの累積変位）
- `-Z`（`eda/tvt_regime.md` で `Corr(TVT, -Z) = 0.917` を確認済み。直接の強い予測子になるはず）
- GR affine calibration（prefix のみでフィット, `eda/gr_calibration.md`）+ trailing rolling mean/std + gradient（FORCE2020/SEG2016 の知見、`research/past_solutions.md`）

### 当初の計画との差分（重要な経緯）

当初は pilkwang Notebook の Target-Free Alignment（DTW によるタイプウェル GR とのマッチング）を exp001 に含める計画だった。実装し prefix 区間で sanity check したところ、以下が判明したため **DTW は exp001 のスコープから除外**した（`src/features.py` に `dtw_align` 関数は保持、未使用）:

- `fastdtw`（scipy euclidean, radius=200）: 1 well で 239 秒 → 773 well で約 51 時間、実用不可
- 軽量化（`dist=None`, radius 5〜50）でも 1 well 0.7〜16 秒まで短縮できたが、**prefix 区間（正解 TVT が既知）でのアラインメント誤差 RMSE が 50〜260ft** と flat anchor（12.8ft）より大幅に悪化。typewell 範囲を anchor 周辺に絞っても改善せず
- 素朴な GR 振幅ベースの全系列 DTW は、似た GR パターンが複数深度に出現するため誤った経路に収束しやすいと考えられる。pilkwang が PF/beam search・anchor 制約等の複数ガードレールを組み合わせているのはこの問題への対処と推測 → 専用の exp002 で再設計する

## 事前予測

- 全体 OOF RMSE: **13〜15 程度**（flat anchor 15.91 からの改善は小さい〜中程度。DTW 抜きでは pilkwang 8.07 には遠く及ばない想定）
- 稀少レジーム（境界跨ぎ）RMSE: 改善は限定的（trajectory/GR特徴は緩やかな drift の捕捉が中心で、急峻なジャンプの予測には弱いはず）
- 通常レジーム RMSE: trajectory特徴（特に `-Z`）の寄与で flat anchor より明確に改善するはず

## 設定

- 親 config: `conf/config.yaml`（defaults: model=lgbm, data=default, train=default）
- 特徴量: `src/features.py::build_feature_frame`（DTW 抜き版）
- モデル: `src/model.py::LGBMResidualModel`（target = 残差）
- 検証: `GroupKFold(well_id, 5-fold)`、学習・評価は tail 行のみ
- W&B Run: `20260619_lgbm_baseline_no_dtw`

## 手順

1. `src/dataset.py` でデータロード + prefix/tail 境界・anchor付与
2. `src/features.py` で GR calibration・rolling/gradient特徴を構築
3. `scripts/train.py` で GroupKFold(well_id, 5) の OOF を作成、overall/rare/common RMSE を W&B に記録
4. `scripts/make_submission.py` で配布 test 3 wells に対する submission.csv を生成（値域クリップのみの後処理）

## 実際の結果

実行日: 2026-06-19（ローカル smoke test、libgomp の関係で docker 外で実行。本番実行はユーザーが docker 上で再実行する想定）

- 全体 OOF RMSE: **14.28**（fold別 val RMSE: 14.63 / 14.33 / 13.26 / 14.25 / 14.88）
- 通常レジーム RMSE: 14.28
- 稀少レジーム（境界跨ぎ）RMSE: 13.84
- LB: 12.959
- 学習時間: 5-fold 合計 約13分（このマシン、num_boost_round=3000 / early_stopping=100）
- submission.csv: 14,151 行・id がすべて `sample_submission.csv` と一致することを確認済み

## 考察

事前予測と比較:
- 全体 OOF RMSE 14.28 は事前予測レンジ「13〜15」の範囲内 → trajectory(-Z 等) + GR特徴による改善は予測通り小さめだった（flat anchor 15.91 から **-1.63**の改善）
- 稀少レジーム RMSE（13.84）が通常レジーム（14.28）より**良い**のは予想外（「稀少レジームの改善は限定的」と予測したが、実際は稀少行のほうがむしろ低RMSE）。ただし「稀少」の定義は真の `tvt_diff_abs`（真のTVTから計算）に基づくため、これは「実際に急変した行」の RMSE であり、必ずしも「モデルが急変を検知できたか」を意味しない。むしろサンプル数が少なく分散が大きい可能性がある（要 sample size 確認）

考えられる原因:
- (a) 単一モデルでは pilkwang の 8.07 に遠く及ばない（14.28 vs 8.07）→ DTW/Target-Free Alignment 相当の信号が依然として最大のレバーであることを示唆。exp002 で再設計する優先度が高いことが確認された
- (b) `-Z` 単独の相関は 0.917 と強いが、ウェルごとに系統誤差（オフセット）があるはずで、anchor からの残差予測だけでは吸収しきれていない可能性。ウェル別 OOF RMSE の分布を見て、系統誤差が大きいウェル群を特定する価値がある（exp003 候補）

## 次のアクション

- [ ] exp002: DTW Target-Free Alignment の再設計（pilkwang の anchor制約・PF/beam search 相当のガードレールを踏まえる。typewell範囲を trajectory/構造面 prior で絞った上でのローカル探索など）
- [ ] 稀少/通常レジーム別の RMSE を見て、trajectory特徴がどちらに効いているか確認
- [x] CV-LB 相関を測るため、実際に Kaggle へ提出して比較
