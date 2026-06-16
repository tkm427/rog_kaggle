# 過去類似コンペの TOP 解法

> CLAUDE.md「コンペ開始 3 日以内に TOP 5 解法を要約」目標。本コンペは「水平坑井での層位置推定 / TVT 回帰」という独特なタスクで、完全に類似するコンペは少ない。**近接ドメイン** のコンペから手法を引っ張ってくる戦略を取る。
>
> 最終更新: 2026-06-16（FORCE 2020 TOP3 + SEG2016 代替調査 + arXiv 2510.07564 を追記）

## 調査対象候補

| コンペ | 類似点 | 解法を読む価値 | 状況 |
|---|---|---|---|
| **FORCE 2020 Well Log Lithology Prediction** | ガンマ線等のログから岩相を予測。最も近い | ★★★ | ✅ TOP3 調査済み（下記） |
| FORCE Machine Predicted Lithology | ↑と同一コンペ（別名） | ★★★ | 統合済み |
| SEAM AI Applied Geoscience challenge | 地震波形 + ログ統合 | ★★ | ⚠️ 該当コンペなし。代わりに **SEG 2016 ML Contest** を調査（下記） |
| Kaggle Petrofizik 系（過去にあれば） | 物理ログ→未知量 | ★★ | 未調査 |
| Kaggle "Predict Future Sales" 等の系列回帰 | グループ系列回帰の検証戦略 | ★ | 未調査（優先度低） |
| HuBMAP（医療セグメンテーション）系 | 物理連続量の Smoothing 後処理 | ★ | 未調査（優先度低） |

## 記録テンプレート

各解法を読んだら以下を埋める:

### {コンペ名} {順位}
- URL:
- モデル:
- データ処理:
- 特徴量エンジニアリング:
- 検証戦略:
- 後処理:
- 工夫:
- 学び（本コンペへの示唆）:

---

## FORCE 2020 Machine Predicted Lithology

公式リポジトリ: https://github.com/bolgebrygg/Force-2020-Machine-Learning-competition
全体結果: https://www.sodir.no/en/force/Previous-events/2020/results-of-the-FORCE-2020-lithology-competition/

タスクはガンマ線・密度・抵抗率等の検層ログから岩相（lithology）を分類する問題。カスタムのペナルティ行列（誤分類の種類によって罰則が異なる）が評価指標。

### 1位: Olawale Ibrahim（final score: -0.4690）
- URL: https://github.com/bolgebrygg/Force-2020-Machine-Learning-competition （※1位本人の詳細記事は見つからず。Medium記事は別参加者(open LB 24位)による解説のため参考程度）
- モデル: XGBoost 単体。10-fold Stratified CV のアンサンブル
- データ処理: 欠損が多いカーブ（SGR, DTS, RXO, ROPA等）は除外。**欠損値の補完は意図的に行わず**、XGBoostのネイティブな欠損値処理に委ねた
- 特徴量エンジニアリング: ウィンドウ統計量（windowing）+ gradient（勾配）特徴量が主軸。GROUP/FORMATION/WELLのラベルエンコーディング
- 検証戦略: 10-fold Stratified K-Fold CV
- 後処理: 特になし（fold アンサンブル予測のみ）
- 工夫: カスタムペナルティ行列は学習損失に組み込まず、**モデル選択・HPOのみ**に使用。シンプルな特徴量+アンサンブルでブラインドテストがオープンLBより大きく改善
- 学び（本コンペへの示唆）: 欠損ログを無理に補完せずGBDTに委ねる選択は、TVT予測でも欠損区間への過度な前処理を避ける根拠になる。**windowing統計 + gradient特徴量というシンプルな設計がTOPでも核** → GR/TVDのrolling統計・1次/2次差分（gradient）を最初の特徴量セットとして優先する

### 2位: GIR Team（Lucas Aguiar ら, UENF, ブラジル / final score: -0.4792）
- URL: https://giruenf.org/force-2020-lithology-machine-learning-competition/ , https://ispl.deib.polimi.it/2nd-place-at-xeek-force-challenge-on-machine-predicted-lithology/
- モデル: XGBoost 標準実装
- データ処理: 欠損カーブを**他の関連カーブから物理ベースで予測補完**（単純な統計補完ではなく石油物理学的知見を活用。例: RHOBの欠損を関連ログから推定）
- 特徴量エンジニアリング: 全カーブに gradient 特徴量、元特徴量の polynomial 特徴量、さらに **wavelet 変換** で岩相を区別しやすい特徴量を選択・生成
- 検証戦略: 標準的なCV（詳細未記載だが、CV戦略のチューニングに注力したと明言）
- 後処理: 明示的な記述なし
- 工夫: アルゴリズム選択ではなく「**欠損補完＋特徴量拡張**」で差をつけたとチーム自身が明言
- 学び（本コンペへの示唆）: wavelet変換特徴量は DTW アラインメント後の GR 波形の局所パターン抽出に応用可能。「物理的知見に基づく欠損補完」は、typewell と対応がない区間や TVT_input が欠損する区間の扱いに応用できる

### 3位: Lab.ICA Team（Smith W. A. Canchumuni ら, PUC-Rio, ブラジル / final score: -0.4954）
- URL: technical retrospective（Sodir PDF、LinkedIn要約経由で確認） https://www.linkedin.com/pulse/force-2020-lithology-prediction-technical-peder-aursand
- モデル: Random Forest
- データ処理: 欠損カーブはメディアン値で単純補完
- 特徴量エンジニアリング: GR・RHOBの正規化特徴量、ログのgradient特徴量、FORMATIONをカテゴリ特徴量として使用
- 検証戦略: 5-fold Stratified Cross-Validation
- 後処理: 特になし
- 工夫: 正解率自体は2位より高かったが、ペナルティ行列により「明らかに間違った岩相」への誤分類が重く罰せられ順位が下がった
- 学び（本コンペへの示唆）: シンプルなRFでも正規化＋gradient特徴量だけでTOP3に入れる → ROGIIでも複雑なモデルより先にシンプルなGBDT/RF + 良い特徴量でbaselineを固めるのが効率的。ただし「**評価指標が物理的妥当性を重視する**」傾向には注意（ROGIIでもTVTの物理的滑らかさを損なう予測は誤差として目立ちやすい可能性）

### FORCE 2020 全体総括（ROGIIへの主要な学び）

1. **GBDT (XGBoost/RF) + windowing統計・gradient特徴量がTOP3共通の核**。ROGIIでもGR/TVDのrolling mean/std、1次・2次差分（gradient）を最初の特徴量セットとして優先する
2. **欠損値処理は「単純補完 vs 物理ベース補完 vs 補完なし」で順位は分かれたが、性能差はTOP5-7で僅差**。ROGIIでも補完法に時間をかけすぎず、まずGBDTのネイティブ欠損処理で試す
3. **カスタム評価指標を学習損失に直接組み込んだチームはTOP3にいなかった**が、3位はそれが間接的な要因で2位より下がった。ROGIIでTVTの「物理的に滑らか」という性質を重視するなら、**後処理（Savitzky-Golay/Gaussianスムージング）で滑らかさを担保する方針**（H3）は的を得ている
4. **wavelet変換特徴量（2位GIRチーム）**はGR波形の局所パターン抽出に有効 → DTWアラインメント後のGR特徴量強化候補。`research/public_notebooks.md` のnihilisticneuralnet (DWT) Notebookとも一致する方向性

---

## SEAM AI Applied Geoscience（該当コンペなし → SEG 2016 ML Contest で代替調査）

**注記**: "SEAM AI Applied Geoscience" 名称に最も近いのは **SEAM AI Applied Geoscience GPU Hackathon (2021, SEG/SEAM/NVIDIA/OpenACC共催)** だが、これは3D地震ボクセルのfacies分類・信号分離タスクであり、ROGIIの「typewell vs horizontal well のwell-log相関・回帰」とは性質が大きく異なる（詳細はpaywallで未確認: https://seg.org/news/ai-applied-geoscience-hackathon-results-released/ , https://www.gpuhackathons.org/index.php/event/seam-ai-applied-geoscience-gpu-hackathon）。

代わりに、well-log facies分類というタスクが近い **SEG 2016 Machine Learning Contest** を代替調査した。

### SEG 2016 ML Contest — LA Team (優勝, Mosser & de la Fuente)
- URL: https://github.com/seg/2016-ml-contest , https://wiki.seg.org/wiki/Facies_classification_using_machine_learning
- モデル: XGBoost (Boosted Trees)。F1-micro median 0.6388
- データ処理: PEログなど欠損の多いチャンネルは0埋め/平均値埋め。各特徴量を正規化・標準化
- 特徴量エンジニアリング:
  - **深度方向のgradient/1次差分特徴**（GR等の深度トレンド変化検出）
  - **rolling window統計**（上下の深度区間の値をパディングして特徴に含める／spatial context augmentation）
  - 物理モチーフに基づく交互作用特徴（rock physics motivated feature augmentation, arXiv:1808.09856）
- 検証戦略: STUART/CRAWFORDの2坑井を**完全ブラインドホールドアウト**（well単位のグループ分割）。確率的モデルは100回試行のmedianでスコアリング
- 後処理: 明記なし
- 工夫: 物理モチーフベースの特徴量拡張が複数チームでスコア向上に寄与
- 学び（本コンペへの示唆）:
  1. **well単位のホールドアウト/GroupKFoldは業界標準** → ROGIIのGroupKFold(well_id)方針(H2)を裏付ける
  2. GR系列のgradient・rolling統計は**DTWアラインメント後の局所マッチング特徴**として転用可能（FORCE2020の知見とも一致）
  3. 欠損ログはシンプルな補完（0埋め/平均値）で十分な可能性 → typewellとの対応外区間でも複雑な補完より単純な手法から試す

---

## arXiv 2510.07564: GRU + 物理拘束による Wellbore Trajectory 予測

詳細な論文メモは [`research/papers.md`](./papers.md) 参照。要点のみ:

- タイトル: *A Geomechanically-Informed Framework for Wellbore Trajectory Prediction: Integrating First-Principles Kinematics with a Rigorous Derivation of Gated Recurrent Networks*（Kumar & Sahoo, IIT Kharagpur）
- URL: https://arxiv.org/abs/2510.07564
- モデル: 単層GRU（隠れ64）。入力ウィンドウ50点(=25m, 0.5m刻み)・ストライド10点。入力5ch（GAMMA, POROSITY, PERM, FLUVIALFACIES, NETGROSS）→ 出力2（傾斜角・方位角）
- データ処理: Min-Maxスケーリング[0,1]、0.5m等間隔への**線形補間**リサンプリング（スプラインは境界付近で非現実的な値を作るため不採用）
- 検証戦略: holdout 20% + 完全未見の坑井によるテストセット
- 後処理: 予測角度をAverage Angle / Minimum Curvature法で数値積分し3D軌跡(TVD含む)を再構成
- 工夫（物理制約の組み込み方）: **損失関数への明示的なsmoothness/単調性ペナルティは無し（標準MSE）**。物理的妥当性は (a) 入力ログを「岩石機械特性の代理変数」として選ぶ、(b) 線形補間によるリサンプリング、(c) 後処理での運動学的積分、という**アーキテクチャ・前処理側のソフトな設計**で実現
- 結果: 傾斜角 MAE 0.21°/R²=0.88、方位角 MAE 0.45°/R²=0.82、DLS MAE 0.15deg/100ft/R²=0.75。誤差は地質的複雑度が高い区間（急なDLS変化・岩相急変）に集中
- 学び（本コンペへの示唆）:
  1. MD方向に固定長ウィンドウ（50点/25m, stride10）でGRU入力を作る設計はTVT予測にも転用可能（GR + typewell対応特徴をチャンネルとして束ねる）
  2. 「物理制約」は損失項ではなく **(a) ΔTVTを予測して累積積分で復元 (b) ジャンプ検出→区間別スムージング** という2段階の後処理アプローチがより実証的（H3の検証設計に直結）
  3. 線形補間によるリサンプリングはMDの不均一サンプリングへの前処理として転用可能。スプラインはTVTジャンプ近傍で避けるべき
  4. **誤差が地質的複雑区間（=TVTジャンプ近傍）に集中**するという知見は、「稀少レジームRMSE」(`competition_overview.md`の定義)の重要性を裏付ける。誤差解析はジャンプ近傍区間を分離して行う

---

## 既知の手法カテゴリ（geosteering ドメイン）

過去解法から独立した、geosteering 文献由来の手法群:

| 手法 | 概要 | 本コンペでの位置づけ |
|---|---|---|
| **DTW (Dynamic Time Warping)** | タイプウェル GR との時系列整列 | 古典的・最強候補 |
| **HDE (Horizontal Drilling Equivalent) Scaling** | TVT スケールにオフセット井データを変換 | 特徴量化候補 |
| **GRU / LSTM** | 系列モデル | arXiv 2510.07564（[`papers.md`](./papers.md)）参照。ΔTVT予測+積分復元のアプローチが有力 |
| **1D-CNN / TCN（Dilated Conv）** | 多重スケールパターン抽出 | 軽量で効きそう |
| **Transformer + 位置エンコーディング** | 長距離依存 | 終盤のアンサンブル要員 |
| **Kalman / Particle Filter** | 物理的滑らかさを担保する後処理 | 興味深いが工数大 |
| **Savitzky-Golay フィルタ** | 滑らかな多項式フィット | 後処理の第一候補。FORCE2020・arXiv論文双方の知見から優先度高 |
| **Wavelet / DWT 変換** | GR波形の多重解像度特徴 | FORCE2020 2位 + nihilisticneuralnet Notebookで有効性確認 |
| **Gradient / Rolling Window統計** | 深度方向の1次差分・移動統計 | FORCE2020 TOP3全員 + SEG2016優勝チームで共通 → 最優先で実装 |

## アクション

- [x] FORCE 2020 の TOP 3 解法を精読し、本ファイルに要約
- [x] SEAM AI Applied Geoscience の代替調査（SEG 2016 ML Contest）
- [x] arXiv 2510.07564（GRU + 物理拘束）の前処理・後処理を抽出（`research/papers.md`）
- [ ] FORCE2020/SEG2016由来の **gradient特徴量・rolling window統計** を `src/features.py` の最優先実装候補としてリスト化（GR・TVD・typewell GRに対して）
- [ ] wavelet (DWT) 特徴量を `src/features.py` に実装する際、nihilisticneuralnet Notebookの実装と比較
- [ ] H3（後処理スムージング）の検証時、arXiv論文の **「ΔTVT予測 + 累積積分復元」** と **「ジャンプ検出 → 区間別スムージング」** を別アプローチとして比較する exp を立てる
- [ ] 「稀少レジーム（TVTジャンプ近傍）」の誤差が大きくなりやすいという知見を `eda/tvt_regime.md` の閾値設計に反映
- [ ] strategy.md の仮説リストに以下を追加候補として検討:
  - [H7] GBDT欠損値処理（補完なし）で十分か、typewell対応外区間で検証
  - [H8] wavelet/DWT特徴量がDTW後のGR特徴を強化するか
