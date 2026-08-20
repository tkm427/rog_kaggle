# 実験インデックス

> 全実験の俯瞰表。各実験の詳細は `experiments/expXXX.md`。

## 現在のフォーカス

**コンペ終了（2026-08-05）。最終順位 4365位 / 6125チーム（private 12.693 / public 12.959、提出1回）。**

- 上位解法の要約: `research/top_solutions.md`（1st 5.639 / 2nd 5.802。両者とも「2D整列の確率場推定 + CNN + 合成データ」）
- 全体ふりかえり: `postmortems/pm002_competition_retrospective.md`

exp002〜exp006 は「手作り整列で単一パスを推定 → LightGBM の特徴量にする」という同一定式化の枝であり、
この定式化自体が多峰な posterior を平均モードに潰すため上限が低かった。H9 ロードマップ（exp007〜exp012）は未実施のまま終了。

## 実験一覧

| ID | 定式化 | 仮説 | 主な変更 | OOF RMSE | LB RMSE | 失敗の層 | 状態 | 備考 |
|---|---|---|---|---|---|---|---|---|
| exp001 | F1 | Anchor+Trajectory+GR特徴でLightGBM残差モデルがflat anchor(15.91)を改善する | GroupKFold(well_id,5) + LightGBM残差予測 | 14.28（rare 13.84 / common 14.28） | 12.959 | 該当なし | DONE | DTWは性能・精度問題で除外（exp002へ）。submission.csv生成・フォーマット確認済み、提出済み |
| exp002 | F1 | anchor制約付きbeam search（pilkwang `beam_typewell_path`移植）でtypewell整列特徴を追加すればOOFが改善する | beam_alignment_features（tight/cons/loose） + LightGBM残差予測 | 14.66（rare 13.88 / common 14.66、exp001比+0.38悪化） | 未提出 | 定式化 | ABANDONED | 短horizon sanity checkは通過したが実tail長で累積drift。`postmortems/pm001_beam_alignment_drift.md` |
| exp003 | F1 | baselineモデルはtail長/rare比率の高いウェルで弱いはず | scripts/analyze_per_well_rmse.py でウェル別RMSE分析（n=773） | 14.28（baseline再現） | - | — | DONE | 事前予測は反証。実際の弱点はtrajectory(-Z)とTVTのネット変位が食い違うウェル（corr 0.580）。`experiments/exp003_per_well_residual.md` |
| exp004 | F1 | trajectory-GR不一致度を特徴量化すればモデルが「trajectory非信頼区間」を学習しRMSEが改善する（H10） | prefix相関×4 + rolling GR-negZ corr×3 + GR NN TVT×2 を追加 | 14.3241（rare 14.3037 / common 14.3241、**baseline比+0.04悪化**） | 未提出 | 定式化 | DONE | 符号反転ウェル一部は改善（a8ed028a top10圏外へ）したが他ウェルでregression。Group 3(GR NN)のノイズとGroup 2の情報量不足が原因と推測。`experiments/exp004_trajectory_gr_disagreement.md` |
| exp004b | F1 | exp004でGroup2・3がノイズという仮説検証: prefix相関4特徴のみに絞ればbaselineを超えるはず | disagreement_groups=[1]（prefix相関×4のみ） | 14.2955（rare 13.9856 / common 14.2955、**baseline比+0.015 微悪化**） | 未提出 | 定式化 | DONE | ノイズ源除去仮説は確認（exp004 14.32→14.30改善）。ただしbaseline(14.28)には届かず。prefix相関スカラー単体でLightGBMへの情報伝達が不十分と結論。H10アプローチ終了。 |
| exp005 | F1 | pm001の教訓（実tail評価・per-well外れ値分布）を満たす共通ハーネスがあれば、H9の各整列手法を公平にgateできる | `scripts/analyze_alignment_quality.py`（MATCHERS registry, real-tail評価, decoupled-well判定） | - | - | — | DONE | beam再現チェックでpm001既報値(mean 11.85ft, global flat anchor割合73.3%)を誤差なく再現。`experiments/exp005_alignment_harness.md` |
| exp006 | F1 | stride間隔で独立に位置を探すmulti-scale NCCなら、beamのような誤り伝播を避けられ整列特徴になるはず(H9) | `ncc_typewell_path`/`ncc_alignment_features`（window 8/15/25） | —（gate段階で不合格、OOF未測定） | 未提出 | 定式化 | ABANDONED | horizontal well(GR-vs-MD ~1ft/row)とtypewell(GR-vs-TVT ~0.5ft/sample)のサンプリング密度不一致が原因。窓幅を物理TVT-ft幅に換算する修正も効果なし（局所傾き推定自体がDTW/beam/PFの解く問題と同じ）。`experiments/exp006_ncc_alignment.md` |

新しい実験を追加したら必ず 1 行追加する。状態は `TODO / RUNNING / DONE / ABANDONED`。

## CV-LB 相関メモ

| 日付 | exp | OOF RMSE | Public LB | 差 (LB-OOF) | 備考 |
|---|---|---|---|---|---|
| 2026-06-21 | exp001 | 14.28 | 12.959 | -1.32 | LBがOOFより良い。1点のみで相関は未確定。公開test 3wellsとtrain well id重複の可能性は要確認（competition_overview.mdのリーク管理セクション） |

CV-LB の相関係数が安定してきたら、提出を出さずに OOF だけで意思決定できるようになる。最初は 5-10 件取って判断する。

## 公開ベースライン目安

リサーチ時点（2026-06-15）で観測された公開 Notebook のスコア:

| Notebook | LB RMSE | URL |
|---|---|---|
| ROGII Wellbore Geology Submission v1 (thbdh5765) | 20.079 | https://www.kaggle.com/code/thbdh5765/rogii-wellbore-geology-submission-v1 |
| [ROGII] SUPER BASELINE (romantamrazov) | 12.602 | https://www.kaggle.com/code/romantamrazov/rogii-super-baseline-lb |
| 9.251 DWT-based (nihilisticneuralnet) | 9.251 | https://www.kaggle.com/code/nihilisticneuralnet/9-251-rogii-wellbore-geology-prediction-dwt-based |
| 9.538 Training (rauffauzanrambe) | 9.538 | https://www.kaggle.com/code/rauffauzanrambe/9-538-rogii-wellbore-geologyprediction-training |
| 🛢️ EDA + Target-Free Alignment (pilkwang) | 8.072 (best) | https://www.kaggle.com/code/pilkwang/12-049-rogii-eda-leakageriskdiscussion |

→ 公開で 8.0 付近。これを超えた時点で「公開水準到達」と判断。

## ロードマップ（更新随時）

- [x] exp001: Anchor+Trajectory+GR特徴 + LightGBM残差モデルでベースライン確立（GroupKFold OOF含む）
- [x] exp002: anchor制約付きbeam searchによるalignment特徴 → 長horizon累積driftで失敗（ABANDONED）
- [x] exp003: ウェル別残差を分析 → trajectory-TVTデカップリングが主要弱点と判明
- [x] exp004/4b: trajectory-GR不一致度を特徴量化（H10）→ baseline超えられず終了
- [x] exp005: real-tail評価ハーネス + decoupled-well判定（H9インフラ）
- [x] exp006: multi-scale NCC整列特徴（H9）→ MD/TVTサンプリング密度不一致でABANDONED

**H9ロードマップ（詳細は`strategy.md`のH9仮説の下の表）:**
- [ ] exp007: Sakoe-Chiba banded DTW（次の最優先候補。numba導入要否を要判断）
- [ ] exp008: Particle Filter（trajectory-informed transition + prefix由来obs_sigma）
- [ ] exp009: beam+NCC(失敗のため実質beam+DTW+PF)+CatBoost候補の統合 — H9の核心go/no-go
- [ ] exp010: CatBoostResidualModel追加（旧exp007候補を統合）
- [ ] exp011: Ridge meta-stack（fold-consistent）
- [ ] exp012: Savitzky-Golay + warm-up decay後処理（旧exp005候補を統合）

**H9以外の未着手候補（優先度は継続検討中）:**
- [ ] 近隣ウェル空間特徴（H6）
- [ ] 1D-CNN / TCN シーケンスモデル
- [ ] Transformer
- [ ] ...

## 失敗・廃案の記録

実験が失敗したり方針を変えたりしたら、**ここに 1 行残してから削除**する。後で類似アイデアが浮かんだときに無駄な再試行を避ける。

| exp | 試したこと | 結果 | 廃案理由 |
|---|---|---|---|
| exp001(DTW部分) | fastdtw による全系列GR-Typewell GRのDTWマッチング | 1well 239秒(radius200)〜0.7-16秒(軽量化後)だが、prefix区間でのアラインメントRMSEが50-260ft（flat anchor 12.8ftより悪化） | 計算コストと精度の両方で実用不可。anchor制約・PF/beam search等のガードレール無しの素朴な実装では機能しない → exp002で再設計 |
| exp002 | pilkwang `beam_typewell_path` 移植（anchor制約+局所遷移+beam枝刈り）でtypewell整列特徴を追加 | sanity check（prefix末尾30%, 平均511行）はRMSE 6.1〜6.8ftで通過したが、本番統合後OOFが14.28→14.66に悪化。原因は実tail長（平均4867行）での累積drift（holdout長85%でRMSE 339〜520ft） | beam searchはanchorへの再制約が探索開始点のみで、長horizonでは素朴DTWと同様に破綻する。sanity checkのholdout長を本番tail長分布に合わせていなかったのが検出漏れの原因。`postmortems/pm001_beam_alignment_drift.md` |
| exp006 | multi-scale NCC（window 8/15/25サンプル、start_tvt±150ft限定）でtypewell整列特徴を追加(H9) | real-tail mean RMSE 56.65ft（flat anchor 12.8ft・gate閾値13.0ftのいずれにも遠く届かず）。窓幅を物理TVT-ft幅換算に変更する修正でも10wellでmean 70〜90ftと悪化 | horizontal well(GR-vs-MD ~1ft/row)とtypewell(GR-vs-TVT ~0.5ft/sample)のサンプリング密度がウェルごとのdTVT/dMDのばらつきにより対応せず、同サンプル数窓の相関比較が物理的に異なる深度スパンを比較していた。正しい窓幅換算にはウェル固有の局所傾き推定が必要で、これはDTW/beam/PFが動的計画法で解く問題そのもの。`experiments/exp006_ncc_alignment.md` |