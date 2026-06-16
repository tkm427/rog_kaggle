# 戦略・時間配分・週次ふりかえり

> このファイルは「**今週何をするか**」を決めるための作業ドキュメント。週次で更新する。静的なコンペ仕様は `competition_overview.md`、実験ログは `experiments.md`。

## コンペ期間と時間配分

- 開始: 2026-05-05
- 終了: 2026-08-05
- **本テンプレ作成時点**: 2026-06-15（残り約 7 週間）



### 想定スケジュール

| 期間 | フェーズ | 主目標 |
|---|---|---|
| Week 1 (06/15-06/21) | リサーチ + ベースライン | 公開 Notebook fork で submission を出し、CV-LB 相関を測定 |
| Week 2-3 (06/22-07/05) | ベースライン強化 | DTW・FE・GroupKFold で 公開水準 8.0 を下回る |
| Week 4-5 (07/06-07/19) | 改善実験 | LGBM/CatBoost、シーケンスモデル、後処理、タイプウェル整列 |
| Week 6 (07/20-07/26) | アンサンブル | seed avg・モデル平均・Hill Climbing |
| Week 7 (07/27-08/05) | 最終調整 | 提出枠の使い切り・私的ふりかえり |

### このコンペでの優先順位

公開 Notebook の最高スコアが 8.07 と比較的低い段階。**メダル圏に入るには公開水準を有意に下回る必要がある**ため、次の順で投資する:

1. **データ理解とリーク把握**（Week 1 最優先） — ここが甘いとどんなモデルも崩れる
2. **検証設計（GroupKFold + 安定した OOF）**（Week 1-2） — 信頼できる CV がないと意思決定できない
3. **タイプウェル整列特徴量**（Week 2-3） — ドメイン的に最も筋がいい
4. **後処理（スムージング・物理拘束）**（Week 3-4） — 安価で効きやすい
5. **シーケンスモデル / アンサンブル**（Week 4-7） — 効果は出るが投資対効果は他より下

## 現在の仮説リスト（優先度順）

実験開始前にここを更新する。以下はリサーチ初期の作業仮説。

1. **[H1] GR と Typewell GR の DTW マッチングが TVT 推定の最強単一信号**  
   → exp001 で残差を確認、exp003 で DTW 特徴を追加して検証
2. **[H2] GroupKFold (well_id) で組んだ CV のほうが Random KFold より LB と相関が高い**  
   → 最初の 3 提出で散布図を取る
3. **[H3] TVT は物理的に滑らかなため、後処理スムージング（Savitzky-Golay or ガウシアン）で RMSE が改善**  
   → 各ベース提出に対して post-hoc で検証
4. **[H4] 評価ゾーンの境界の `TVT_input` を拘束条件として使うと精度が上がる**  
   → リーク境界を pilkwang Notebook と公式仕様で確認してから検証
5. **[H5] ウェル内 MD 順の系列モデル（1D-CNN / Transformer）が単独行モデル (LGBM) を上回る**  
   → exp00X で point-wise LGBM vs sequence model を比較
6. **[H6] 近隣ウェル（X, Y 座標）の TVT を空間特徴として使うと改善**  
   → pilkwang の Section 13 "Nearby-Well Spatial Signal" を参考に

## 検証戦略

- **GroupKFold（well_id 単位）5-fold が基本**。ウェル内の行を別 fold に混ぜない。
- 各 fold の OOF 予測を保存し、`scripts/analyze_per_well_rmse.py` でウェル別 RMSE を可視化。外れ値ウェルを特定。
- **TVT レジーム別 RMSE** も必ず見る（稀少 = 急峻区間、通常 = 連続区間）。CLAUDE.md の `val_score_rare` / `val_score_common` に対応。
- LB との相関: 最初の 5 提出で OOF RMSE と Public LB を散布図に。乖離が大きければ検証設計を見直す。
- Public/Private 分割の挙動: 終盤は Public への過学習リスクを意識（コンペ規模が小さい場合は特に）。


## 既知のベンチマーク（リサーチ時点）

公開 Notebook の最高スコア:

| LB | Notebook | 備考 |
|---|---|---|
| 8.072 | pilkwang | EDA + Target-Free Alignment（最高公開） |
| 9.251 | nihilisticneuralnet | DWT 特徴 |
| 9.538 | rauffauzanrambe | 学習 Notebook |
| 12.602 | romantamrazov | Super Baseline |

→ **目安**: 7 を切れたらメダル圏視野、6 切りで上位安定、5 以下で勝負（あくまで現時点・終盤に下がる前提）。

## 週次ふりかえり

### Week 1 (2026-06-15 〜 06-21)

- やったこと:
- 学んだこと:
- 戦略変更点:
- 次週のフォーカス:

### Week 2 (2026-06-22 〜)

- ...