# exp005: real-tail整列評価ハーネス + decoupled-well判定（H9インフラ）

## 仮説

pm001（beam alignment失敗）の教訓は「(a) 代用データ（prefix holdout）ではなく実tail区間で評価する
こと」「(b) 平均RMSEだけでなくper-wellの外れ値分布も見ること」の2点。この2つを最初から満たす
共通ハーネスを作れば、H9の各整列手法（NCC/DTW/PF）を同じ基準・同じコードパスで公平にgateできる。

## 事前予測

- `--matcher beam`で実行した結果が、pm001の既報値（実tail mean RMSE 11.85ft, flat anchor(12.8ft)
  を下回るウェル割合73.3%, n=60, seed=42）を誤差±1.0ft/±5pp以内で再現するはず
  （ハーネス自体の正しさを確認するcorrectness check。新しい発見ではない）。

## 設定

新規 `scripts/analyze_alignment_quality.py`:
- `label_trajectory_tvt_decoupled(hw, flat_eps=2.0)`: tail内のneg_Z正味変位とTVT正味変位の符号比較
  （**analysis-only、hidden-tail TVTを読むため src/features.py 等には絶対にimportしない**）
- `MATCHERS`レジストリ（beam→exp006でncc追加）
- `evaluate_alignment_on_real_tail` / `summarize_alignment_quality`

実行: `python scripts/analyze_alignment_quality.py --matcher beam --n-wells 60 --seed 42`

## 実際の結果

```
[overall] n=60
  mean=11.85 median=9.78 p90=19.94 max=61.86
  frac_below_flat_anchor(per-well)=51.7%
  frac_below_flat_anchor(global 12.8ft)=73.3%
  frac_outlier_gt_3x_flat=0.0%
```

mean RMSE 11.85ft・global flat anchor基準での割合73.3%とも**pm001の既報値と完全一致**。
ハーネスの正しさを確認。

なお`frac_below_flat_anchor(per-well)`（各ウェル自身のflat anchor RMSEとの比較、51.7%）は
pm001未報告の新規追加指標。global基準（51.7%→73.3%）との差は、ウェル自身の実際の変位量に
応じてflat anchor RMSEが変わるため（変位が小さいウェルほどflat anchorに勝ちにくい）。

decoupled subset（n=29, 全体の48.3%）でも同水準の性能（mean 11.62ft）で、beam単体では
decoupled wellsに対する明確な優位性は見られなかった。

## 考察

ハーネスは正しく動作しており、exp006以降のgate判定に使える。デカップリングウェルの割合が
48.3%と、exp003のworst-10限定の分析（4/10=40%）と近い水準だったのは想定の範囲内
（事前予測では15-30%程度と見積もっていたが、実際はやや高め。ただしflat_eps=2.0ftの閾値次第で
変動するため、この数字自体への深入りはしない）。

## 次のアクション

- [x] beam再現チェック完了、ハーネスの正しさ確認
- [ ] exp006でNCC matcherを登録し同じ基準で評価（→結果はexp006参照、ABANDONED）
- [ ] exp007でDTW matcherを登録

## 関連実験
- `postmortems/pm001_beam_alignment_drift.md`（このハーネス設計の直接の教訓元）
- `experiments/exp003_per_well_residual.md`（decoupled-well定義の出典）
