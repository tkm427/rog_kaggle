# 実験インデックス

> 全実験の俯瞰表。各実験の詳細は `experiments/expXXX.md`。

## 現在のフォーカス

exp001 完了。次は **DTW/Target-Free Alignment の再設計（exp002）** が最優先。
理由: exp001（trajectory+GR特徴のみ）の OOF RMSE 14.28 は flat anchor(15.91)からの改善は小さく、pilkwang(8.07)とのギャップが大きい。DTWに相当する信号が依然最大のレバーと判断（詳細 `experiments/exp001_baseline.md`）。
他の未着手タスク: Kaggle への実提出（CV-LB相関の最初の1点）、`discussions.md` の実調査、ウェル別残差分析。

## 実験一覧

| ID | 仮説 | 主な変更 | OOF RMSE | LB RMSE | 状態 | 備考 |
|---|---|---|---|---|---|---|
| exp001 | Anchor+Trajectory+GR特徴でLightGBM残差モデルがflat anchor(15.91)を改善する | GroupKFold(well_id,5) + LightGBM残差予測 | 14.28（rare 13.84 / common 14.28） | 12.959 | DONE | DTWは性能・精度問題で除外（exp002へ）。submission.csv生成・フォーマット確認済み、未提出 |

新しい実験を追加したら必ず 1 行追加する。状態は `TODO / RUNNING / DONE / ABANDONED`。

## CV-LB 相関メモ

| exp | OOF RMSE | Public LB | 差 (LB-OOF) | 備考 |
|---|---|---|---|---|

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
- [ ] exp002: GR × Typewell の DTW/Target-Free Alignment を再設計（anchor制約・PF/beam search 相当のガードレール）
- [ ] exp003: ウェル別残差を分析 → 失敗パターン抽出
- [ ] exp004: 後処理スムージング（Savitzky-Golay）
- [ ] exp005: 近隣ウェル空間特徴
- [ ] exp006: CatBoost ベースライン
- [ ] exp007: 1D-CNN / TCN シーケンスモデル
- [ ] exp008: Transformer
- [ ] exp009: アンサンブル（Hill Climbing）
- [ ] ...

## 失敗・廃案の記録

実験が失敗したり方針を変えたりしたら、**ここに 1 行残してから削除**する。後で類似アイデアが浮かんだときに無駄な再試行を避ける。

| exp | 試したこと | 結果 | 廃案理由 |
|---|---|---|---|
| exp001(DTW部分) | fastdtw による全系列GR-Typewell GRのDTWマッチング | 1well 239秒(radius200)〜0.7-16秒(軽量化後)だが、prefix区間でのアラインメントRMSEが50-260ft（flat anchor 12.8ftより悪化） | 計算コストと精度の両方で実用不可。anchor制約・PF/beam search等のガードレール無しの素朴な実装では機能しない → exp002で再設計 |