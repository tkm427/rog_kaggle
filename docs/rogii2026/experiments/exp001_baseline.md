# exp001: 公開 Notebook fork で最小 E2E を確立する

> CLAUDE.md の「Phase 2: 公開 Notebook を fork してもよい。とにかく `submission.csv` を出す」に対応。

## 仮説

公開 Notebook（例: nihilisticneuralnet の DWT-based、LB 9.251）を fork して動かせば、自前パイプラインに移植する前に **データ I/O・提出フォーマット・ローカル CV と LB の関係** を 1 度で確認できる。

## 事前予測

- LB: fork 元と同程度（±0.1 以内）→ 大きく外れたら fork ミスを疑う
- ローカル GroupKFold (well_id, 5-fold) OOF RMSE は LB より **やや低い** はず（well 数が少ないため fold ごとの分散大）
- ウェル別 RMSE はばらつき大（特定ウェルで突出して悪い可能性 → exp004 で深掘り対象）

## 設定

- 親 config: `conf/config.yaml`
- 変更: TBD（fork 元のハイパラを踏襲）
- W&B Run: `20260615_exp001_lgbm_fork_baseline`
- Project: `baseline`

## 手順

1. Kaggle CLI でデータダウンロード: `kaggle competitions download -c rogii-wellbore-geology-prediction -p data/raw/`
2. fork 元の Notebook ロジックを `src/dataset.py` + `src/model.py` + `scripts/train.py` に整理
3. GroupKFold (well_id) で 5-fold OOF
4. `scripts/make_submission.py` で submission.csv 生成
5. Kaggle Notebook にコピー → 提出

## 実際の結果

（実験完了後に埋める）

- 全体 OOF RMSE:
- 通常レジーム RMSE:
- 稀少レジーム RMSE:
- LB:
- 学習時間:
- 推論時間（推定本番）:

## 考察

（実験完了後に埋める）

事前予測と比較:
- ...

考えられる原因:
- (a) ...
- (b) ...

## 次のアクション

- exp002: GroupKFold が正しく機能しているか確認するため、Random KFold と OOF RMSE を比較
- ウェル別 RMSE が悪い上位 5 ウェルを特定 → `eda/bad_wells.md` に記録