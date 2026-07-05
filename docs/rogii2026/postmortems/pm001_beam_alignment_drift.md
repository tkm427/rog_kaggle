# pm001: anchor制約付きbeam searchが本番統合後にOOFを悪化させた

## 訂正（2026-06-28）

初版では「horizon長に対して誤差が急激に増大する（累積drift）」と結論づけたが、これは
**prefixの一部（60%/85%）を「仮のtail」として代用したsanity checkの誤差**であり、
本物のtail区間（train CSVには tail 行にも真の `TVT` 列が入っている）で直接評価していなかった。

`scripts/visualize_beam_alignment_drift.py` で本物のtail区間（is_tail行、本番の
`beam_alignment_features` が処理する区間そのもの）に対し直接 `beam_typewell_path` を実行し、
真の `TVT` と比較したところ、**累積drift仮説は支持されなかった**:

- 本物のtail（n=60サンプル, 平均約4800行/well）: mean RMSE **11.85ft** / median **9.78ft**
- flat anchor (12.8ft) を下回るウェル割合: **73.3%**（30%代用sanity checkの90%よりは劣るが、
  初版が示した「late区間339〜520ft」のような破滅的な値ではない）
- `docs/rogii2026/postmortems/fig/pm001_drift_vs_step.png`: 本物のtailでステップ数に対するRMSEを
  見ても、beam search と flat anchor はほぼ同じ曲線を描き、16-1800行あたりでflat anchor gate
  (12.8ft) を一旦超えるが、その後7000行を超えると両者ともむしろ改善する（drift増大とは逆の動き）
- `pm001_path_overlay.png`: 大半のウェルでは整列パスはtrue TVTにある程度追従する
  （例: ce8399b7 RMSE 2.7ft, ddc790ff RMSE 8.2ft）。一部のウェル（例: 2fd68f7b RMSE 61.9ft）で
  true TVTが急激に変化する区間に追従できず大きく外れる、という**少数ウェルの外れ値**が主な問題

以下の「何が起きたか」「5 Why」は初版の記述を保持しつつ、上記の訂正を反映して書き直す。

## 何を期待していたか

exp002（`experiments/exp002_beam_alignment.md`）の事前予測:
- pilkwang notebookの `beam_typewell_path`（anchor制約付きビタビ風beam search）を移植すれば、exp001（trajectory+GR特徴のみ, OOF 14.28）からRMSEが明確に改善し、1桁台後半〜10台前半まで縮まるはず
- 統合前の必須ゲート（prefix区間でのsanity check, flat anchor 12.8ftとの比較）はクリアした上で本番統合する計画

## 何が起きたか

- **必須ゲートは通過した**: prefixの末尾30%を「仮のtail」として切り出すsanity check（`scripts/analyze_beam_alignment_quality.py`）で mean RMSE 6.06ft（n=30）/ 6.75ft（n=200）、flat anchor(12.8ft)を89〜93%のウェルで下回った → GATE PASSED と判断し統合
- **本番統合後にOOFが悪化**: `train.enable_beam_features=true` でGroupKFold再学習した結果、**OOF RMSE 14.66**（exp001の14.28から+0.38、改善ではなく悪化）。事前予測（1桁台後半〜10台前半）から大きく外れた
- **（訂正済）当初の原因調査**: prefixの60%/85%を「仮のtail」として代用した再検証で誤差がhorizon長に対して急激に増大するように見えた（30%: 9.70ft → 60%: 149.79ft → 85%: 520.24ft）。しかし上記「訂正」の通り、本物のtailで直接評価するとこの破滅的な増大は再現しない（mean 11.85ft）。**代用データでの検証は、anchorからの距離だけでなくprefix自体のGR系列の性質（typewell側と一致しやすい/しにくい区間）の違いを混同していた可能性が高い**

## なぜ起きたか（5 Why）

1. なぜOOFが悪化したか？ → beam特徴の典型的なRMSE（本物のtailでmean 11.85ft）はflat anchorと同程度だが、一部のウェル（例: RMSE 60ft超）で大きく外れた整列結果が混入し、LightGBMに対するノイズの多い・時に誤った信号として学習されたから
2. なぜ一部のウェルだけ大きく外れるのか？ → `beam_typewell_path` は1ステップあたりtypewell index ±1までしか動けない局所遷移で、true TVTが急激に変化する区間（`pm001_path_overlay.png`の2fd68f7bのような急峻な立ち上がり）では追従が物理的に追いつかず、anchorの制約も探索開始点（start_idx）にしか効かないため、そのまま外れた状態が継続する
3. なぜ再制約が無いまま実装したか？ → pilkwang notebookの該当関数（cell 69 `beam_typewell_path`）を忠実に移植したが、pilkwangは実際にはこの関数を**他の多数の特徴・PFアンサンブル（500particle×複数seed/scale）・ridge artifactブレンドと組み合わせて使っており、単体では急峻な変化区間に弱い**ことを実装前に確認していなかった
4. なぜ統合前のsanity checkで本番相当の悪化を検出できなかったか？ → sanity checkのholdout区間をprefixの30%（平均511行）に設定し、「flat anchorを下回ればOK」という単一の平均値基準だけで判定した。本物のtailでの評価では平均的には同程度のRMSEだったため、この基準自体は大筋で誤っていなかったが、**少数の大外れウェルがLightGBMの学習に与える影響を平均RMSEだけでは検知できなかった**
5. なぜ「少数ウェルの大外れがモデル全体を悪化させるリスク」を事前に評価しなかったか？ → 必須ゲートを「ウェル平均RMSEとflat anchorの比較」という単一の集計指標で運用し、外れ値の分布（per-wellのRMSE分布、tailの形状）やそれが下流モデル（LightGBM）の学習に与える影響を検証する手順がなかったから

## 次回どうするか

- **短期**:
  - `enable_beam_features` はデフォルト無効化済み（`conf/train/default.yaml`）。関数は将来の再設計用に保持
  - 次の一手はexp003（ウェル別残差分析）に切り替え、trajectory+GR特徴だけのモデルがどのウェル群で弱いかを先に特定する
  - beam search自体を再挑戦する場合は、(a) 大外れが出ているウェル（`pm001_path_overlay.png`の2fd68f7b系）の特徴を分析し、急峻なTVT変化を検知して特徴を無効化/ダウンウェイトする仕組みを追加する、(b) 探索窓を固定半径ではなくtrajectoryからの許容偏差で動的に絞る、等の改善を加えてから再統合する
- **長期（CLAUDE.mdへの追記候補）**:
  - 「sanity checkは必ず本番が処理する実際の区間（代用データではなく）で評価すること。代用データで検証する場合は、本番区間との違い（horizon長だけでなく系列の統計的性質）を明示し、結論を本番区間での再検証なしに確定させない」
  - 「必須ゲートはウェル平均RMSEだけでなく、per-wellのRMSE分布（外れ値の有無）も確認すること。平均が基準を満たしていても、少数の大外れが下流モデルを悪化させることがある」

## 関連実験
- exp001（trajectory+GR特徴ベースライン）, exp002（beam alignment統合・失敗）
- 訂正の根拠: `scripts/visualize_beam_alignment_drift.py`（本物のtailでの直接評価、n=60）
