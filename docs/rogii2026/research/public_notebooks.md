# 公開 Notebook 調査

> 最終更新: 2026-06-29（2回目の調査。ローカル保存済みDWT Notebookの精読 + Web再調査で更新）

## 主要 Notebook 一覧

| Notebook | 著者 | LB | 主な手法 | URL |
|---|---|---|---|---|
| 🛢️ EDA + Target-Free Alignment for TVT | pilkwang | **8.099** (best 8.072) | EDA + リーク整理 + ターゲットフリー層位整列 + Super Stack | https://www.kaggle.com/code/pilkwang/12-049-rogii-eda-leakageriskdiscussion |
| ~~9.251 DWT-based~~ → 実体はPF+beam+DTW+NCCアンサンブル | nihilisticneuralnet | 9.251 | **タイトルに反しDWTは未使用**（下記参照）。Particle Filter + Beam Search + multi-scale DTW + NCC + LightGBM/CatBoost + Hill Climbing + Optuna後処理 | https://www.kaggle.com/code/nihilisticneuralnet/9-251-rogii-wellbore-geology-prediction-dwt-based |
| 9.538 Training | rauffauzanrambe | 9.538 | 学習スクリプト | https://www.kaggle.com/code/rauffauzanrambe/9-538-rogii-wellbore-geologyprediction-training |
| [ROGII] SUPER BASELINE | romantamrazov | 12.602 | 公開ベースライン | https://www.kaggle.com/code/romantamrazov/rogii-super-baseline-lb |
| [ROGII] BETTER SOLUTION 🆕 | romantamrazov | 9.956 | SUPER BASELINE の改善版（手法詳細未取得、要DL） | https://www.kaggle.com/code/romantamrazov/rogii-better-solution-lb-9-956 |
| [ROGII] SUPER SOLUTION 🆕 | romantamrazov | "TOP 3"（具体値不明、173 upvotes） | BETTER SOLUTION のさらなる改善版（手法詳細未取得、要DL） | https://www.kaggle.com/code/romantamrazov/rogii-super-solution-lb-top-3 |
| ROGII Wellbore Final Kriging 🆕 | artgor | 不明 | 空間 Kriging 補間（手法詳細未取得） | https://www.kaggle.com/code/artgor/rogii-wellbore-final-kriging |
| ROGII Dual Pipeline + Self-Verifying 🆕 | lightningv08 | 不明 | 未調査 | （URL未確認、要検索） |
| rogii-dwt-sgw25-candidate 🆕 | beicicc | 不明 | 未調査。**nihilisticneuralnetと同様「DWT」表記が実装と一致しない可能性あり、内容未検証のまま信用しないこと** | （URL未確認、要検索） |
| Hill Climbing | ravaghi | — | LightGBM + CatBoost + Hill Climbing + 後処理。アルゴリズム自体は公開GitHub（[ravaghi/hill-climbing](https://github.com/ravaghi/hill-climbing)）の`Climber`/`ClimberCV`（greedy重み探索、改善停止で終了）と確認。ROGII固有の重み値は未取得 | https://www.kaggle.com/code/ravaghi/wellbore-geology-prediction-hill-climbing |
| Submission v1 | thbdh5765 | 20.079 | 単純提出（最小例） | https://www.kaggle.com/code/thbdh5765/rogii-wellbore-geology-submission-v1 |
| 🛢️ ROGII Wellbore Geology Prediction | koushikkumardinda | — | 一般 | https://www.kaggle.com/code/koushikkumardinda/rogii-wellbore-geology-prediction |

🆕 = 2026-06-29 調査で新規発見（前回06-15調査時点では未確認）。**いずれもローカル未ダウンロードのため手法詳細は未検証**。Kaggle の Notebook/Discussion ページは WebFetch では本文取得不可（タイトルのみ返却、JS-rendered SPA）と確認済みのため、詳細を読むには `kaggle kernels pull` 等での手動ダウンロードが必要（このマシンに Kaggle CLI 未インストール・認証情報なしのため自動化不可）。

## 重要: nihilisticneuralnet Notebook の実装訂正（2026-06-29、ローカルファイル精読）

前回調査ではタイトルから「DWT (Discrete Wavelet Transform) で GR 信号を多重解像度分解」と要約していたが、**ローカル保存済みファイル（`research/9-251-rogii-wellbore-geology-prediction-dwt-based (1).ipynb`）を実際にパースして精読した結果、DWT の実装は一切存在しないことが判明**（`pywt` import なし、`wavelet`/`dwt` 文字列が全24セル・metadata中に0件）。**タイトルと実装が一致しない公開 Notebook**であり、今後同種の Notebook（例: 上記 `beicicc/rogii-dwt-sgw25-candidate`）もタイトルだけで判断せず実装を確認する。

実際の実装は以下のアンサンブル（むしろ pilkwang notebook に近い設計思想）:

- **Particle Filter** (`_pf_ancc`, `_pf_z`, numba `@njit`): typewell GR密度グリッドに対し逐次ベイズ更新（尤度 `exp(-0.5*((gr-expected)/sigma)^2)`）でTVTを推定
- **Beam Search** (`_beam_jit`): 7種類のパラメータセット(`BEAMS`)でGR-typewell GRマッチングコストを最小化
- **Multi-scale DTW** (`_dtw_sakoe_chiba`, `_dtw_stochastic_realizations`): Sakoe-Chibaバンド制約 + radius=(20,50,100,200)のマルチスケール + 確率的(Gumbelノイズ)実現 K=12本でばらつき推定
- **Multi-scale NCC**（正規化相互相関）: window幅8/15/25
- **空間補完**: `FormationPlaneKNN`（地層トップの空間平面フィット, k=10）、`DenseANCCImputer`（k=20 NN密度補完）
- **GR派生特徴**: rolling mean/std (window 5/21/51/101)、lag/lead (1/5/15/30)、1次/2次差分、エンベロープ、energy (`sqrt(mean(gr^2))`)、typewell GR残差(`tda*/tdbc*/tdsc*/tdpf*/tddtw*`) — 合計数百カラム
- **モデル**: LightGBM (GPU, num_leaves=255, 3 seed) + CatBoost (GPU, depth=7) を各3シード学習 → Hill Climbing でアンサンブル
- **検証**: `GroupKFold(n_splits=5, groups=well)` — ウェル単位で正しく実施
- **後処理**: `alpha`/`tau`(減衰時定数)/`w_pf`(PF混合比) を Optuna 500 trials で最適化 + Savitzky-Golay (`sg_w=17, sg_p=3`) でウェルごとにスムージング
- **リーク観点**: **Offline/batch policy**。評価区間自身を含む GR 全系列 (`full_gr`) を使って DTW・typewell相関を計算している（target である TVT そのものは使っていないが、未来の GR covariate は使用）

### このコンペの「主流手法」についての示唆（重要）

pilkwang（最高LB）と nihilisticneuralnet（実装訂正後）は、**設計思想が驚くほど似ている**:

1. **単一の整列手法に依存しない**: DTW・beam search・particle filter・NCC を複数パラメータ設定で並行に走らせ、その出力を特徴量として GBDT に渡す（「どの整列が正しいか」をモデル自身に選ばせる）。当プロジェクトの exp002 はビームサーチ単体（3パラメータ設定のみ、他手法との冗長性なし）で統合し、一部ウェルの外れ値が直接ノイズとして混入して悪化した（`postmortems/pm001_beam_alignment_drift.md`）。**上位解法が複数の独立した整列法を冗長に持たせているのは、まさにこの「少数ウェルの外れ値」問題への対処**と考えられる
2. **GBDT (LightGBM + CatBoost) のシードアンサンブル + Hill Climbing**が共通の最終段
3. **Optuna等での後処理パラメータ最適化 + Savitzky-Golay**が共通
4. **GroupKFold(well_id)** が両者で確認済み（リーク管理の業界標準が再確認された）

→ exp003（ウェル別残差分析）の後、再度 alignment 系特徴に投資する場合は、**ビームサーチ単体ではなく DTW/PF/NCC 等の複数手法を並行実装し、GBDTに「投票」させる設計**にすることが、pm001 の外れ値問題への直接的な対策になる（戦略候補として `strategy.md` の仮説リストに追記検討）。

## 必読: pilkwang Notebook（最高公開スコア）

> 2026-06-16: 全 115 セル（markdown 全文）を読了。Section 0/0.1/0.2/5 のリーク方針は `competition_overview.md` の「リーク管理: Information Policies and Leakage Rules」セクションに反映済み。

セクション構成:

| Section | 内容 | 自分の示唆メモ |
|---|---|---|
| 0 | Information Policies and Leakage Rules | Strict(drilling-time) / Offline(batch) の2トラック。Offline は未来 GR/trajectory は OK だが未来 TVT は禁止。Allowed/Excluded 特徴量ファミリー表とともに `competition_overview.md` に反映済み |
| 0.1 | Leakage Risk Table | 8 項目のリスク表を `competition_overview.md` に反映済み。最重要: `GroupKFold(well_id)` 必須、train-only formation 列は hidden test に無い、PF selector の same-well 物理ブランチは public-aggressive |
| 0.2 | Public/Private Feature Policy | 「direct leakage か」と「train/test well 重複に依存するか」は別軸。`PF_SELECTOR_USE_SAME_WELL_PHYSICAL` の True/False 比較が診断ペア。`competition_overview.md` に反映済み |
| 1 | File Inventory | `well_id`（≒ `WELLNAME`）で horizontal/typewell/PNG を結合。id 不整合が GR アラインメントを壊すので結合チェックを data loader に入れる |
| 2 | Column Check and Representative Well | train は `TVT` + formation 列（`ANCC`,`ASTNU`,`ASTNL`,`EGFDU`,`EGFDL`,`BUDA`）あり。hidden test は `MD,X,Y,Z,GR` + prefix `TVT_input` のみ → 特徴量は hidden test スキーマで再現可能なものに限定。列名を `competition_overview.md` に反映済み |
| 3 | Prediction Zone and Submission Mapping | 予測対象 = `TVT_input` が欠損する行のみ。`id = {well_id}_{row_index}`。各 test well に 1 つの隠れ tail がある prefix-conditioned forecasting → `make_submission.py` の id 生成ロジックに反映予定 |
| 4 | Horizontal Well Aggregate Summary | prefix 長・tail 長・GR 欠損率・anchor 誤差(`constant_tail_rmse`)が事前難易度指標。tail 長は数千行に及ぶため小さな slope bias が蓄積する |
| 5 | Leakage Boundary and Column Roles | Column Role Map（Observable / Known-prefix / Hidden-tail / Train-only formation）と Safe/Unsafe pattern を `competition_overview.md` に反映済み |
| 6 | TVT_input Consistency Check | known prefix では `TVT_input == TVT` を確認済み → `last_known_TVT` を anchor として使える（`competition_overview.md` に反映） |
| 7 | Target Behavior, Smoothness, and Jumps | TVT は曲線的だが単調ではない。prefix slope の単純 extrapolation はリスク高、smoothing/clip 系後処理が必須 |
| 8 | Typewell Data Inventory | typewell GR は TVT でインデックスされた参照曲線。サンプリング密度・TVT スパン・GR レンジ・geology ラベルが整列確信度を決める |
| 9 | Stratigraphic Surface and Typewell Alignment Signals | `TVT + Z ≈ S(X,Y) + b_w` という構造面座標の関係。known-prefix での GR 残差スケール(`gs_w`)が PF 観測ノイズ scale の目安になる → DTW/PF 特徴量設計の式として再利用可 |
| 10 | Baseline Evaluation | null model = `last_known_TVT` 一定（constant anchor）。これに勝つには drifting well を改善しつつ flat well を悪化させない residual 予測が必要 |
| 11 | Row-Level Features | Strict 特徴（prefix context, row position, trailing GR 等）と Offline 特徴（tail fraction, centered GR, candidate path, beam 等）のカタログ。`TVT_input_bfill` 等は全 policy で禁止 → 特徴量カタログとして `src/features.py` 設計に使う |
| 12 | Curve-Level Target Diagnostics | tail カーブは少数の knot で要約可能 → row 予測には smoothing/clip 後処理が有効 |
| 13 | Nearby-Well Spatial Signal | 近隣ウェルは構造 drift を共有 (H6)。validation fold のターゲットを neighbor 参照テーブルに混ぜないことが guardrail |
| 14 | Representative Well Plot | 代表ウェル可視化テンプレ: TVT 連続性・GR 欠損・typewell 類似度・flat/drifting tail・jump の確認に使う |
| 15 | Model Logic from EDA | 予測 = `last_known_TVT` + (GR/geology/trajectory からの residual) + 軽い後処理。`GroupKFold(well_id)`・hidden-tail 行のみ・row-level loss が validation guardrail |
| 16 | Residual Prediction Model | Anchor → Model(raw residual) → Clip/shrink → Fade-in → Slope limiter の pipeline。16.0 で Strict/Offline/Excluded の全特徴量リストを再確認済み（11 のカタログと同内容） |
| 17 | Offline Candidate-Path Feature Check | Offline 限定の signal map（candidate path, beam, formation plane 等）。すべて未来 TVT / direct test formations は不使用 |
| 18 | Super Stack Submission Engine | 最終提出 = residual target(`TVT - last_known_TVT`) を LGB seeds + CatBoost で学習 → Ridge/Hill-climb で stack → PF/DTW/beam/formation/ANCC を信号として混合 → shrink/fade/smooth で後処理 |

## ravaghi Notebook（Hill Climbing）

セクション構成:
1. Imports and configs
2. Data loading and preprocessing
3. Training (3.1 LightGBM, 3.2 CatBoost)
4. **Hill climbing** — モデル重みを greedy に最適化
5. Postprocessing
6. Inference
7. Results

→ アンサンブル設計の参考。Hill Climbing の重み最適化コードを `scripts/ensemble_hillclimb.py` に取り込み候補（ライセンス確認の上）。

## nihilisticneuralnet Notebook（DWT-based）

→ DWT (Discrete Wavelet Transform) で GR 信号を多重解像度分解 → 各スケールの統計量を特徴量化。tree モデルとの相性が良い古典的アプローチ。**EDA で実装を確認 → 自前 feature engineering に組み込み候補**。

## boristown「Public Rebuild」系列（LB 7.159〜7.295、2026-06-29ユーザー提供・精読済み）

> ユーザーがブラウザから4本ダウンロードし `research/public_notebooks/` に配置。最終更新2026-06-29。

| ファイル | LB | 備考 |
|---|---|---|
| `public-score-rogii-lb-7-159.ipynb` | 7.159（現状最高） | Public Rebuild最終版 |
| `rogii-lb-7-201.ipynb` | 7.201 | 同系列の前バージョン |
| `rogii-lb7295-public-rebuild.ipynb` | 7.295 | 同系列の前バージョン |
| `rogii-lb7295-public-rebuild-v1-xr-recovery (1).ipynb` | 7.295系 | 別系統。weight probe（後述） |

**重要**: 上記3ファイル（7.159/7.201/7.295）は**コードが完全に同一**（39セル、cell単位diffで論理差分ゼロ、文字エンコーディングの表記違いのみ）。GroupKFold CV RMSEも完全一致（Overall **10.4197**、773 wellでの5-fold OOF）。スコア差はrerun時の浮動小数点誤差レベルの揺れであり、**手法的な改善ではない**。

### パイプライン概要

- **整列特徴**: beam search（14パラメータ組のアンサンブル, `run_beam_ensemble`）+ likelihood-weighted Particle Filter（128-seed, 複数scale 3/5/8/12, Numba JIT）+ multi-scale NCC（window 8/15/25）の **3系統並行アンサンブル**。`research/past_solutions.md`の「複数整列手法の冗長アンサンブル」パターンを再確認
- **空間特徴**: `FormationPlaneKNN`（KNN+逆距離重み付き局所平面フィット）、`DenseANCCImputer`
- **モデル**: LightGBM 3種 + CatBoost 2種（GPU）→ Ridgeメタスタッキング（`alpha=1.66, positive=True`）
- **後処理**: Savitzky-Golay（`sg_win=61, sg_poly=3`）+ warm-up減衰（`tau=85ft`）+ prefix-holdoutバックテストで候補手法を選択する「Gold calibration」
- **検証**: `GroupKFold(n_splits=5, groups=well)`。773 train well全体でのOOFが前述の10.42

### 🚨 same-well shortcut（最重要・要警戒）

cell 17 で次のロジックを確認:
```python
if wid in train_wells:
    hw_te['TVT_input'] = hw_tr['TVT_input'].values
```
配布されているtest 3 wellは「visible/train-test重複ウェル向け高速パス（Strict XR fast path）」で**trainデータから直接TVT_input相当をコピー**している。著者コメント: 「By construction this is >= the plain blend: exact wells win, mismatched wells are skipped」。

**`eda/train_test_overlap.md`（2026-06-16作成）で当プロジェクトが既に検出していた「配布test 3 well（`000d7d20`/`00bbac68`/`00e12e8b`）は全てtrainと重複」というリスクが、実際に上位公開Notebookで明示的に悪用されていることが確認された。** 同ドキュメントの予測（「same-well依存の特徴はPrivateで崩壊するリスクが高い」）はこの発見でより説得力を持つ。

**結論**: 公開LB 7.159は (a) 上記same-well shortcutによる配布test特有のブースト、(b) 整列アンサンブル+CatBoost+Ridge stack+後処理という legitimate なGroupKFold OOF改善（10.42、当プロジェクトのexp001=14.28より明確に良い）の**両方が混在**している。**(a)はPrivate/隠れtestで再現しない可能性が高く、公開LB順位を直接の目標にするのは危険**。技術的に追うべきは(b)のCV改善分。

## rogii-lb7295-public-rebuild-v1-xr-recovery（weight probe、2026-06-29精読）

48セル、上記と別系統。「sp45」パイプライン（PF+beam+projection後処理）と「fleongg」パイプライン（事前学習LGBM stacking）を線形ブレンド `tvt = w_sp45*tvt_sp45 + (1-w_sp45)*tvt_fleongg` する重み`w_sp45`を、**Kaggleへの複数回提出とLBフィードバックで手動探索**している（V44時点で0.55→0.56→0.58→0.60の刻みを試行中、確定LBスコアはmarkdown未記載）。

著者自身の言及（cell 1 markdown）: *"To avoid overreacting to a noisy single score or extrapolating too far without feedback, V44 adds a conservative interpolation point..."* — LB probingのノイズリスクを著者も認識し、慎重なステップを選んでいる。一方、内部パラメータ`w_sub1=0.60`は別途GroupKFold CV（Nelder-Mead+grid、773 well、「optimum is flat 0.55-0.68」）で検証済みであり、**外側の重み(w_sp45, LB依存)と内側の重み(w_sub1, CV検証済み)で頑健性が大きく異なる**点に注意。**LB probingは当プロジェクトでは採用しない**（Public/Private分割があるコンペでPublicスコアのみに基づくチューニングは過学習リスクが高く、`strategy.md`の「終盤はPublicへの過学習リスクを意識」という既定方針と整合する）。

## アクション

- [x] pilkwang Notebook を最後まで読み、Leakage Risk Table を `competition_overview.md` に反映（2026-06-16）
- [x] DWT Notebook の特徴量定義を読む → **DWTは未実装と判明、PF+beam+DTW+NCCアンサンブルだった**（2026-06-29、上記参照）。`src/features.py` への「DWT関数」実装は前提が誤りだったため取り下げ
- [ ] nihilisticneuralnet の particle filter (`_pf_ancc`/`_pf_z`) ・multi-scale DTW (`_dtw_sakoe_chiba`)・NCC 実装を精読し、exp002後継（beam search単体ではなく複数整列法の冗長構成）の元ネタとして比較する
- [ ] romantamrazov の新規2 notebook（BETTER SOLUTION 9.956 / SUPER SOLUTION TOP3）, artgor の Kriging notebook をダウンロードして手法を確認（このマシンに Kaggle CLI 未認証のため、ユーザー側でのDLが必要）
- [ ] Discussion「Look Ahead and Data Leakage on Horizontal Well Train and Test Data」(Tiago Soares) の本文を確認する（WebFetchではタイトルのみ取得、本文未読 → `discussions.md` に追記済み、要手動確認）
- [ ] Hill Climbing Notebook の重み最適化コードを `scripts/ensemble_hillclimb.py` に取り込む（ライセンス確認）。アルゴリズム自体は [ravaghi/hill-climbing](https://github.com/ravaghi/hill-climbing) の `Climber`/`ClimberCV` で概要確認済み
- [ ] 各 Notebook の CV 戦略を見比べ、GroupKFold が採用されているか確認 → pilkwang・nihilisticneuralnet ともに `GroupKFold(well_id)` 確認済み
- [ ] pilkwang Section 11/16.0 の Strict/Offline/Excluded 特徴量カタログを `src/features.py` の feature policy 設計のチェックリストとして使う
- [ ] `PF_SELECTOR_USE_SAME_WELL_PHYSICAL=True/False` の両方で local validation し、public-aggressive スコアと unseen-well robustness の差を確認する

## メモ

- 公開 Notebook の多くは LightGBM/CatBoost ベース。深層モデルベースの強い公開 Notebook はまだ少ない（2026-06-29 時点でも変わらず）→ シーケンスモデルで差別化の余地あり
- LB スコアの差分（12.602 → 9.5 → 8.0）は特徴量エンジニアリングとアンサンブルで生まれている。**モデルアーキテクチャ変更だけでは越えられない壁** がある可能性
- **Notebook タイトルの手法表記は信用しない**: nihilisticneuralnet の「DWT-based」が実装と一致しなかった前例があるため、`beicicc/rogii-dwt-sgw25-candidate` 等も同様の可能性を念頭に、引用前に必ず実装を確認する
- 公開LBの最高値（8.072）が2026-06-29時点で更新されたという確証は得られなかったが、romantamrazov の新バージョン（9.956 → "TOP 3"）など中位〜上位帯の Notebook 群がこの2週間で明確に進化している。**公開水準は依然下降傾向にある可能性が高く、`strategy.md` の「メダル圏には公開水準を有意に下回る必要」という前提は変わらず有効**