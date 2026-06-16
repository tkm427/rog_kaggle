# 実験インデックス

> 全実験の俯瞰表。各実験の詳細は `experiments/expXXX.md`。

## 現在のフォーカス

**まだ実験開始前。** Week 1 のタスク:
1. データダウンロード & 中身確認
2. ~~`competition_overview.md` の ★ TODO を埋める~~
3. `eda/` に最初の発見を 3-5 本
4. exp001（公開 Notebook fork で submission）を出す

## 実験一覧

| ID | 仮説 | 主な変更 | OOF RMSE | LB RMSE | 状態 | 備考 |
|---|---|---|---|---|---|---|
| exp001 | 公開 Notebook fork で最小 E2E を確立 | — | — | — | TODO | ベースライン確立 |

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

- [ ] exp001: 公開 Notebook fork → submission（CV-LB のキャリブレーション開始）
- [ ] exp002: GroupKFold (well_id) で OOF を作る
- [ ] exp003: GR × Typewell の DTW 特徴量追加
- [ ] exp004: ウェル別残差を分析 → 失敗パターン抽出
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