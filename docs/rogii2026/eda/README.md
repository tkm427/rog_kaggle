# EDA: データ理解の発見集

> 1 発見 = 1 ファイル。`{number}_{topic}.md` 形式で命名。
> 例: `01_tvt_distribution.md`, `02_well_length_variance.md`, `03_gr_typewell_correlation.md`

## 推奨される最初の EDA トピック

CLAUDE.md「Phase 1: データを眺めて `eda/` に 3-5 本の発見を書く」に対応。

1. **TVT の分布**: 全体 / ウェル別 / 評価ゾーン別。レンジ・分散・外れ値
2. **TVT の差分 (`d_TVT/d_MD`) 分布**: 急峻区間（稀少レジーム）の閾値決定
3. **ウェル長の分布**: 行数のヒストグラム。バッチサイズ設計のため
4. **GR と TVT の関係**: 散布図 + 相関
5. **タイプウェル GR と水平坑井 GR の対応**: DTW で整列したときの典型例
6. **評価ゾーンの位置**: ウェル内のどこに来るか（先頭・末尾・中間）
7. **TVT_input の与えられ方**: どの区間で NaN、どの区間で値あり
8. **欠損値**: カラム別欠損率
9. **空間分布 (X, Y)**: ウェルがどう散らばっているか。近隣ウェル特徴の妥当性
10. **train と test ウェルの分布差**: 公開された test 数本との比較

## ファイルテンプレ

```markdown
# {topic}

## やったこと
（どのスクリプトをどう実行したか）

## 発見
- 数値根拠を必ず引用（CLAUDE.md「分析の原則」）

## 図表
（`notebooks/` の図への参照）

## 示唆（次の実験・特徴量設計へ）
- ...
```

## EDA インデックス

| ファイル | トピック | 主な発見 |
|---|---|---|
| [data_structure.md](data_structure.md) | データ構造・基本統計 | 773 train / 3 test wells、5.09M 行、tail 率 73%、typewell は TVT+GR+Geology のみ |
| [train_test_overlap.md](train_test_overlap.md) | Train/Test ウェル重複 | 3 test wells すべてが train に存在 → same-well 依存特徴は private で崩壊リスク |
| [tvt_regime.md](tvt_regime.md) | TVT 変化率・稀少レジーム定義 | p95 = 0.91 ft/行 を閾値とする。大ジャンプ（>5ft）は 0.0014% のみ |
| [typewell_structure.md](typewell_structure.md) | Typewell の構造と DTW への含意 | 0.5ft 解像度、97% のウェルで HW TVT を完全カバー、GR-TVT 直接相関は低い |
| [null_model_baseline.md](null_model_baseline.md) | Null model（flat anchor）RMSE | Train 全体 RMSE = 15.91。目標 8.07（pilkwang）まで 7 ft 以上の改善余地 |
| [gr_calibration.md](gr_calibration.md) | GR キャリブレーション特性 | ウェル間で -22〜+41 API のシフト。31% のウェルで 10 API 超 → DTW 前に必須 |