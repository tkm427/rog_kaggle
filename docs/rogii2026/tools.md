# 分析ツールカタログ（rogii2026）

> CLAUDE.md 第10節に従い、`scripts/analyze_*.py` を追加したらここに記載する。
> （旧 CLAUDE.md の「分析ツールカタログ」節から移設。コンペ非依存の CLAUDE.md には表を置かない）

| ファイル | 用途 | 主な引数 | 主な出力 | 既知の限界 |
|---|---|---|---|---|
| `scripts/eda_overview.py` | データ全体の俯瞰 EDA | なし | ウェル数・行数・TVT分布・GRシフト・null model RMSE | — |
| `scripts/analyze_beam_alignment_quality.py` | beam search alignment（exp002）の prefix-holdout sanity check | `--train-dir`, `--n-wells`, `--seed` | flat anchor 比較 RMSE | **holdout 長が固定 30% で本番 tail 長（平均4867行）と不一致。この乖離が exp002 のゲート誤通過を招いた（pm001）** |
| `scripts/visualize_beam_alignment_drift.py` | beam search alignment のドリフト・fit 品質の可視化（pm001） | `--train-dir`, `--n-wells`, `--seed` | `postmortems/fig/pm001_drift_vs_step.png` / `pm001_path_overlay.png` / `pm001_rmse_distribution.png` | — |
| `scripts/analyze_per_well_rmse.py` | ウェル別残差分析（exp003）。tail 長・rare 行比率と OOF RMSE の相関、外れ値ウェル抽出 | `--oof-path`, `--rare-threshold`, `--top-n` | `eda/fig/exp003_per_well_rmse.csv` ほか 4 図 | — |
| `scripts/analyze_alignment_quality.py` | 整列手法の共通評価ハーネス（exp005）。real-tail 区間で `MATCHERS` 登録手法を評価し、per-well 外れ値分布・decoupled-well subset の性能を報告 | `--matcher`, `--n-wells`, `--seed` | mean/median/p90/max/frac_below_flat_anchor/frac_outlier_gt_3x_flat | **評価基準が flat anchor 比。目標スコア（5.6）への残距離を測る設計になっていない** |
