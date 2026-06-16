# 公開 Notebook 調査

> 最終更新: 2026-06-15（初版、調査ベース）

## 主要 Notebook 一覧

| Notebook | 著者 | LB | 主な手法 | URL |
|---|---|---|---|---|
| 🛢️ EDA + Target-Free Alignment for TVT | pilkwang | **8.099** (best 8.072) | EDA + リーク整理 + ターゲットフリー層位整列 + Super Stack | https://www.kaggle.com/code/pilkwang/12-049-rogii-eda-leakageriskdiscussion |
| 9.251 DWT-based | nihilisticneuralnet | 9.251 | Discrete Wavelet Transform 特徴 | https://www.kaggle.com/code/nihilisticneuralnet/9-251-rogii-wellbore-geology-prediction-dwt-based |
| 9.538 Training | rauffauzanrambe | 9.538 | 学習スクリプト | https://www.kaggle.com/code/rauffauzanrambe/9-538-rogii-wellbore-geologyprediction-training |
| [ROGII] SUPER BASELINE | romantamrazov | 12.602 | 公開ベースライン | https://www.kaggle.com/code/romantamrazov/rogii-super-baseline-lb |
| Hill Climbing | ravaghi | — | LightGBM + CatBoost + Hill Climbing + 後処理 | https://www.kaggle.com/code/ravaghi/wellbore-geology-prediction-hill-climbing |
| Submission v1 | thbdh5765 | 20.079 | 単純提出（最小例） | https://www.kaggle.com/code/thbdh5765/rogii-wellbore-geology-submission-v1 |
| 🛢️ ROGII Wellbore Geology Prediction | koushikkumardinda | — | 一般 | https://www.kaggle.com/code/koushikkumardinda/rogii-wellbore-geology-prediction |

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

## アクション

- [x] pilkwang Notebook を最後まで読み、Leakage Risk Table を `competition_overview.md` に反映（2026-06-16）
- [ ] DWT Notebook の特徴量定義を読み、`src/features.py` に DWT 関数を実装
- [ ] Hill Climbing Notebook の重み最適化コードを `scripts/ensemble_hillclimb.py` に取り込む（ライセンス確認）
- [ ] 各 Notebook の CV 戦略を見比べ、GroupKFold が採用されているか確認
- [ ] pilkwang Section 11/16.0 の Strict/Offline/Excluded 特徴量カタログを `src/features.py` の feature policy 設計のチェックリストとして使う
- [ ] `PF_SELECTOR_USE_SAME_WELL_PHYSICAL=True/False` の両方で local validation し、public-aggressive スコアと unseen-well robustness の差を確認する

## メモ

- 公開 Notebook の多くは LightGBM/CatBoost ベース。深層モデルベースの強い公開 Notebook はまだ少ない（2026-06-15 時点）→ シーケンスモデルで差別化の余地あり
- LB スコアの差分（12.602 → 9.5 → 8.0）は特徴量エンジニアリングとアンサンブルで生まれている。**モデルアーキテクチャ変更だけでは越えられない壁** がある可能性