# 関連論文メモ

> 関連論文の調査メモ。`past_solutions.md` から参照される。最終更新: 2026-06-16

---

## arXiv 2510.07564: A Geomechanically-Informed Framework for Wellbore Trajectory Prediction: Integrating First-Principles Kinematics with a Rigorous Derivation of Gated Recurrent Networks

- URL: https://arxiv.org/abs/2510.07564 （HTML版: https://arxiv.org/html/2510.07564）
- 著者: Shubham Kumar (Dept. of Geology and Geophysics, IIT Kharagpur), Anshuman Sahoo (Dept. of Metallurgical and Materials Engineering, IIT Kharagpur)

### 問題設定

- 予測対象: **傾斜角 (Inclination) と方位角 (Azimuth)**（坑井軌跡を決める2変量）。TVT/TVDを直接予測するのではなく、軌跡角度 → 運動学的積分でTVD等を再構成する設計
- 入力: GAMMA, POROSITY, PERM, FLUVIALFACIES, NETGROSS の5系統の物理検層・地質ログ
- データソース: Gulfaks油田（北海）の14坑井から1,594シーケンスを生成

### モデル (GRU)

- 単層GRU、隠れ層64ユニット、単方向（双方向ではない）
- 入力ウィンドウサイズ50点（0.5m刻み = 25m区間）、ストライド10点
- 入力次元5（上記5ログ）、出力次元2（傾斜角・方位角）

### データ処理（前処理）

- **Min-Maxスケーリング [0,1]** を採用（Z-scoreではなく、GRUのゲート（sigmoid/tanh）の非飽和域に値を収めるため）
- 不均一なサンプリング間隔のログを **0.5m等間隔グリッドへ線形補間**でリサンプリング
- **スプライン補間は不採用**: 地質境界付近で「非現実的な特徴（オーバーシュート）」を作るため、と明記

### 検証戦略

- holdout 20% 分割 + 完全に未見の坑井によるテストセット（坑井レベルの一般化評価）

### 後処理

- 予測した傾斜角・方位角を **Average Angle法 / Minimum Curvature法** で数値積分し、累積変位ベクトル（XYZ軌跡）を再構成
- Dogleg Severity (DLS) も予測角度から幾何計算
- 3D軌跡プロットで実測と比較

### 「物理制約」の組み込み方（重要なポイント）

論文タイトルは "Geomechanically-Informed" だが、**損失関数への明示的なsmoothnessペナルティや単調性制約は実装されていない**。損失はMSEのみで、勾配クリッピングを使用。物理的妥当性は以下の**アーキテクチャ・前処理レベルのソフトな設計選択**で確保している:

1. 入力ログ（GAMMA, POROSITY, PERM, FLUVIALFACIES, NETGROSS）を「岩石の機械的性質の代理変数」として選定し、モデルに間接的に物理情報を与える
2. 隠れ状態が局所的な "Mechanical Earth Model" を暗黙的に学習すると主張（reset gateの活性化が岩相境界でピークになると期待 — 仮説提示のみで検証は限定的）
3. 後処理での運動学的積分（Average Angle / Minimum Curvature）により、出力系列全体の物理的整合性（軌跡として成立すること）を確保
4. リサンプリングに線形補間を選び、スプラインによる非現実的な境界アーティファクトを回避

### 訓練details

- Adam (lr=0.001)、batch size=64
- 86 epochで収束（early stopping, patience=10）

### 結果

| 指標 | MAE | RMSE | R² |
|---|---|---|---|
| 傾斜角 (Inclination) | 0.21° | 0.35° | 0.88 |
| 方位角 (Azimuth) | 0.45° | 0.68° | 0.82 |
| DLS | 0.15 deg/100ft | — | 0.75 |

### 限界（論文記載）

- 不確実性定量化なし
- Gulfaks単一油田のみで汎化未検証
- 動的な掘削パラメータ（WOB, RPM等）未使用
- **最大誤差は地質的複雑度が高い区間（急なDLS変化、岩相急変、異常ログ値）に集中**

### 本コンペ（ROGII TVT回帰）への示唆

1. **シーケンスウィンドウ設計の転用**: MD方向に固定長ウィンドウ（本論文は50点=25m, stride10）でGRU/LSTM/1D-CNN入力を構築する設計はそのまま使える。GR・typewell対応特徴量・座標系特徴をチャンネルとして束ね、出力をTVT（または傾斜角に相当する量）とする構成が考えられる

2. **物理制約は損失項ではなく後処理・特徴量設計側で実現するのが実証的**: 本コンペでTVTは境界ジャンプ以外は滑らかという特性がある(`competition_overview.md`)。この論文の知見を踏まえると、
   - (a) **ΔTVTを予測して累積積分で復元**するアプローチ（差分予測 + 積分は、本論文のAverage Angle積分に相当）
   - (b) **ジャンプ検出 → 区間ごとにSavitzky-Golay/Gaussianスムージング**を適用する後処理
   という2段階アプローチが、smoothness損失項を追加するより実証的に近い。H3（後処理スムージング検証）の比較対象として両方をexp化する

3. **線形補間によるリサンプリング**は、ROGIIの不均一なMDサンプリングへの前処理として直接ポータブル。スプライン補間はTVTジャンプ近傍で不自然な値を作るリスクがあるため避ける

4. **誤差は地質的複雑区間（ジャンプ近傍）に集中する**という知見は、`competition_overview.md`の「稀少レジームRMSE」の重要性を裏付ける。誤差解析・モデル改善はジャンプ近傍区間を分離して評価すべき（`scripts/analyze_per_well_rmse.py`にレジーム別の集計を追加する際の根拠）

5. **Min-Maxスケーリング + 坑井ごとの正規化の必要性**: 本論文はGulfaks単一油田での検証のみで、複数フィールドへの汎化は未検証と明記。ROGIIは複数ウェル・複数フィールドを学習するため、グローバルなMin-Maxではなく**ウェル単位/typewell相対のスケーリング**（例: GR - typewell GRの差分特徴）が汎化に効く可能性が高い

### Sources
- https://arxiv.org/abs/2510.07564
- https://arxiv.org/html/2510.07564
