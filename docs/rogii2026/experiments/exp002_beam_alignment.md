# exp002: anchor制約付き Beam Search による Target-Free Alignment

## 仮説

exp001（trajectory+GR特徴のみ, OOF 14.28）の素朴な全系列DTW（exp001で実用不可と判明）を、
pilkwang notebook（LB 8.07、`research/rogii-eda-target-free-alignment-for-tvt.ipynb`）の
`beam_typewell_path`（anchor制約付きビタビ風beam search）に置き換えれば、探索の暴走
（似たGR振幅が複数深度に出現して誤った経路に収束する問題）を防ぎつつtypewellとの整列精度が
上がり、LightGBM残差モデルのOOF RMSEが明確に改善するはず。

## 事前予測

- 全体OOF RMSE: 14.28 → 1桁台後半〜10台前半まで改善（pilkwang 8.07には届かないが大きく前進）
- 稀少/通常レジームともに改善するはず（typewell整列はtrajectory単独より境界跨ぎの検知に強いと想定）

## 設定

- `src/features.py::beam_typewell_path`（pilkwang cell 69を移植）+ `beam_alignment_features`
  （tight/conservative/looseの3設定でbeam searchを実行し、delta・spread・step・GR残差を特徴化）
- 統合前の必須ゲート: `scripts/analyze_beam_alignment_quality.py`（prefix末尾30%を仮のtailとして
  sanity check）
- `conf/train/default.yaml::enable_beam_features=true` で `build_feature_frame` に統合
- W&B Run: `20260627_lgbm_beam_align`

## 実際の結果

**必須ゲート（sanity check）**: 通過
- n=30: mean RMSE 6.06ft / n=200: mean RMSE 6.75ft（flat anchor 12.8ftを89〜93%のウェルで下回る）

**本番統合後のOOF**: 悪化
- 全体 OOF RMSE: **14.66**（exp001の14.28から **+0.38の悪化**）
- 通常レジーム: 14.66 / 稀少レジーム: 13.88
- fold別val RMSE: 14.67 / 14.22 / 13.50 / 14.91 / 15.88（fold0のtrain_resid_rmse=11.48が他fold(2〜3)と比べ異常に高い）

## 考察

事前予測と大きく異なり、改善ではなく悪化した。当初はsanity checkのholdout区間（prefixの30%,
平均511行）が本番の実tail長（平均4867行）より大幅に短く、prefix代用での再検証（60%/85%）で
誤差がholdout長に対して急激に増大したことから「累積drift」が原因と推測した。

**訂正**: 本物のtail区間（train CSVのtail行に入っている真の`TVT`列）で直接evaluateしたところ
（`scripts/visualize_beam_alignment_drift.py`）、累積drift仮説は支持されず、典型的なRMSEは
mean 11.85ft（flat anchor 12.8ftと同程度）だった。実際の原因は、**一部のウェルでtrue TVTが
急激に変化する区間に追従できず大きく外れる（少数の外れ値）**ことが、LightGBMの学習にノイズと
して混入したことだと判明。

詳細（訂正版5 Why分析）は `postmortems/pm001_beam_alignment_drift.md` 参照。

## 次のアクション

- [x] `enable_beam_features` をデフォルト無効化（`conf/train/default.yaml`）。関数自体は保持
- [x] postmortem作成（`pm001_beam_alignment_drift.md`）
- [ ] exp003: ウェル別残差分析を先に実施し、trajectory+GR特徴だけのモデルの弱点（系統誤差が大きいウェル群）を特定
- [ ] beam search再挑戦の場合: 一定行数ごとにtrajectory予測へ再anchorする等の再制約機構を追加し、
      実tail長分布に合わせたholdoutでsanity checkしてから再統合する
