# 実験インデックス

> 全実験の俯瞰表。各実験の詳細は `experiments/expXXX.md`。

## 現在のフォーカス

exp003（ウェル別残差分析）完了。事前予測（tail長・rare比率との相関）は**反証**され、実際の弱点は
「trajectory(-Z)とGRベースのTVT変位が食い違う（符号反転含む）ウェル」と判明（corr(RMSE, abs_net_drift)=0.580）。
詳細は `experiments/exp003_per_well_residual.md`。

次は **H9アンサンブル（PF/beam/DTW/NCC + CatBoost + Ridge stack）着手、または先にH10（trajectory-GR不一致度を
特徴量化する小実験）で仮説検証** のいずれかが候補。理由: exp003でtrajectory単独に依存するモデルの系統的弱点
（trajectoryとTVTの局所的デカップリング）が特定できたため、trajectory非依存の情報源（GR系列アンサンブル）が
有効なはず。pm001（beam alignment失敗、急峻ジャンプへの追従失敗）とは異なるメカニズムである点に注意。
他の未着手タスク: `discussions.md` の実調査。

## 実験一覧

| ID | 仮説 | 主な変更 | OOF RMSE | LB RMSE | 状態 | 備考 |
|---|---|---|---|---|---|---|
| exp001 | Anchor+Trajectory+GR特徴でLightGBM残差モデルがflat anchor(15.91)を改善する | GroupKFold(well_id,5) + LightGBM残差予測 | 14.28（rare 13.84 / common 14.28） | 12.959 | DONE | DTWは性能・精度問題で除外（exp002へ）。submission.csv生成・フォーマット確認済み、提出済み |
| exp002 | anchor制約付きbeam search（pilkwang `beam_typewell_path`移植）でtypewell整列特徴を追加すればOOFが改善する | beam_alignment_features（tight/cons/loose） + LightGBM残差予測 | 14.66（rare 13.88 / common 14.66、exp001比+0.38悪化） | 未提出 | ABANDONED | 短horizon sanity checkは通過したが実tail長で累積drift。`postmortems/pm001_beam_alignment_drift.md` |
| exp003 | baselineモデルはtail長/rare比率の高いウェルで弱いはず | scripts/analyze_per_well_rmse.py でウェル別RMSE分析（n=773） | 14.28（baseline再現） | - | DONE | 事前予測は反証。実際の弱点はtrajectory(-Z)とTVTのネット変位が食い違うウェル（corr 0.580）。`experiments/exp003_per_well_residual.md` |

新しい実験を追加したら必ず 1 行追加する。状態は `TODO / RUNNING / DONE / ABANDONED`。

## CV-LB 相関メモ

| exp | OOF RMSE | Public LB | 差 (LB-OOF) | 備考 |
|---|---|---|---|---|
| exp001 | 14.28 | 12.959 | -1.32 | LBがOOFより良い。1点のみで相関は未確定。公開test 3wellsとtrain well id重複の可能性は要確認（competition_overview.mdのリーク管理セクション） |

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
- [ ] exp004候補: trajectory-GR不一致度を特徴量化（H10、小規模で先に仮説検証する案）
- [ ] H9: PF/beam/DTW/NCCアンサンブル + CatBoost + Ridge stack（trajectory非依存wellsを優先ターゲット、次の最優先候補）
- [ ] exp005: 後処理スムージング（Savitzky-Golay）
- [ ] exp006: 近隣ウェル空間特徴
- [ ] exp007: CatBoost ベースライン
- [ ] exp008: 1D-CNN / TCN シーケンスモデル
- [ ] exp009: Transformer
- [ ] exp010: アンサンブル（Hill Climbing）
- [ ] ...

## 失敗・廃案の記録

実験が失敗したり方針を変えたりしたら、**ここに 1 行残してから削除**する。後で類似アイデアが浮かんだときに無駄な再試行を避ける。

| exp | 試したこと | 結果 | 廃案理由 |
|---|---|---|---|
| exp001(DTW部分) | fastdtw による全系列GR-Typewell GRのDTWマッチング | 1well 239秒(radius200)〜0.7-16秒(軽量化後)だが、prefix区間でのアラインメントRMSEが50-260ft（flat anchor 12.8ftより悪化） | 計算コストと精度の両方で実用不可。anchor制約・PF/beam search等のガードレール無しの素朴な実装では機能しない → exp002で再設計 |
| exp002 | pilkwang `beam_typewell_path` 移植（anchor制約+局所遷移+beam枝刈り）でtypewell整列特徴を追加 | sanity check（prefix末尾30%, 平均511行）はRMSE 6.1〜6.8ftで通過したが、本番統合後OOFが14.28→14.66に悪化。原因は実tail長（平均4867行）での累積drift（holdout長85%でRMSE 339〜520ft） | beam searchはanchorへの再制約が探索開始点のみで、長horizonでは素朴DTWと同様に破綻する。sanity checkのholdout長を本番tail長分布に合わせていなかったのが検出漏れの原因。`postmortems/pm001_beam_alignment_drift.md` |