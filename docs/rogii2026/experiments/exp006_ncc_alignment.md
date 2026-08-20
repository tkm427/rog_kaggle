# exp006: Multi-scale NCC整列特徴（ABANDONED）

## 仮説

窓幅8/15/25サンプルのnormalized cross-correlation（NCC）で、start_tvt近傍(±150ft)に限定した
typewell区間に対しstride間隔で独立に最良位置を探せば、beam searchのような「1ステップごとの
局所遷移でパスを積み上げる」設計と違い一区間の誤マッチが後続に伝播しないため、pm001で報告された
少数ウェルの外れ値問題を回避できるはず。

## 事前予測

- real-tail mean RMSE 9-13ft（beamの11.85ftと同程度）
- max per-well RMSE ≤ 45ft（beamの61.9ftより明確に改善、パス伝播がないため）
- decoupled subsetでflat anchorに勝つ

## 設定

`src/features.py::ncc_typewell_path` / `ncc_alignment_features`（scripts/analyze_alignment_quality.py
の`MATCHERS`に`"ncc"`として登録）。`python scripts/analyze_alignment_quality.py --matcher ncc --n-wells 60 --seed 42`

## 実際の結果

```
[overall] n=60
  mean=56.65 median=55.63 p90=61.21 max=88.54
  frac_below_flat_anchor(per-well)=0.0%
  frac_outlier_gt_3x_flat=86.7%
```

事前予測から大きく外れ、flat anchor(12.8ft)にも遠く及ばない。gate閾値(mean≤13.0, max≤45,
outlier率≤10%)を全て大幅に不合格。

**原因調査**（1ウェルの相関値を直接確認）: 最大相関(0.99)が真の位置から-91ft離れた場所にあり、
真の位置付近ではむしろ負の相関だった。原因はサンプリング密度の不一致:
- horizontal well: GRはMD 1ft/rowでサンプル
- typewell: GRはTVT 0.5ft/sampleでサンプル

水平坑井はほぼ水平に掘削されるため、MDが1ft進んでもTVT（層内垂直位置）はごくわずかしか動かない
（dTVT/dMD ≪ 1、ウェルごとに大きくばらつく。実測net displacementはtail全体で3〜91ft程度）。
つまり「horizontal well側のNサンプル窓」と「typewell側のNサンプル窓」は全く異なる物理的な
深度スパンを表しており、単純な同サンプル数窓の相関比較は物理的に無意味な値を返していた。

**1回の修正試行**（gate運用ルールの範囲内）: 窓幅をサンプル数ではなく物理TVT-ft幅で定義し、
両側をそれぞれのft/sample密度で換算するよう変更。10ウェルで再検証したが、mean RMSE
70〜90ftとむしろ悪化。原因は、正しい換算にはウェル固有の局所dTVT/dMD推定が必要で、
これは全ウェル共通の1係数（search_radius_tvt/n_tailから逆算）では大きく誤差が出る
（実測net displacementがsearch_radius_tvt(150ft)よりずっと小さいウェルが多く、
傾き推定が実態より過大になり窓が短すぎるままだった）上、**正確な局所傾き自体を推定する問題は、
まさにDTW/beam/PFが動的計画法で解いている問題そのもの**であるため。

## 考察

「単一のcommitted pathを持たない独立キーフレーム相関」というNCCの設計思想自体は
pm001の外れ値問題への対策として理にかなっていたが、**このデータセット特有のMD-TVT
サンプリング密度不一致**という別の問題に阻まれた。この問題はbeam/DTW/PFのような
動的計画法・逐次ベイズ更新ベースの手法では（局所遷移や尤度計算が両ドメインの対応関係を
陽に扱うため）発生しにくい構造的な違いがある。NCCを正しく機能させるには結局DTW相当の
仕組みが必要になり、「NCCの方が単純」というメリットが失われるため、この設計のまま
深追いする価値は低いと判断。

## 次のアクション

- [x] H9ロードマップ上でexp006はABANDONED、`experiments.md`の失敗記録に追記
- [ ] exp007（Sakoe-Chiba banded DTW）に進む。DTWは局所傾き(slope = len(tw_tvt)/len(gr_seq))を
  動的に追従するバンドを最初から設計に組み込んでおり、ここで判明したdTVT/dMD不一致問題への
  直接対策になっている
- [ ] `ncc_typewell_path`/`ncc_alignment_features`は`dtw_align`と同様、将来の再設計用に
  コードは残すが`build_feature_frame`からは呼ばない（config配線もしない）

## 関連実験
- `postmortems/pm001_beam_alignment_drift.md`（NCCが対策しようとした外れ値問題の初出）
- `experiments/exp005_alignment_harness.md`（評価ハーネス）
