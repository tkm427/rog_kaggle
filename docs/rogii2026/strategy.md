# 戦略・時間配分・週次ふりかえり

> このファイルは「**今週何をするか**」を決めるための作業ドキュメント。週次で更新する。静的なコンペ仕様は `competition_overview.md`、実験ログは `experiments.md`。

## 時間予算（最終値・事後記入）

```
更新日: 2026-08-05
残り日数: 0
1実験の平均所要: 4
残り実験可能数: 0
現在の best: 14.28
目標: 7.0
残距離: 7.28
null: 15.91
計画中の実験段数: 6
今週の提出回数: 0
現在のフェーズ: Phase 1
未達ゲート: R2, R5
```

> 事後記入。当時このブロックがあれば「7/17 時点で残り19日・平均4日 → 実行可能 4〜5本」に対し
> exp007〜exp012 の 6 段計画が過大だと即座に分かった。

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
7. **[H9] 単一整列手法ではなくDTW/PF/beam/NCCを並行アンサンブルし、CatBoost追加+Ridge stack+Savitzky-Golay後処理を組み合わせれば、exp001(OOF 14.28)からboristown notebookのlegitimate GroupKFold OOF相当(10.42)に近づけるはず**（2026-06-29調査、`research/public_notebooks.md`）  
   → pm001（beam単体の外れ値問題）への直接対策。exp003完了で次の最優先候補に確定（trajectory-TVTデカップリングwellsを優先ターゲットにできるはず）。着手開始（2026-07-17）。

   **H9ステージ設計（exp005〜exp012、各stageに定量gate基準）:**

   | exp | 内容 | 状態 | 主なgate基準 |
   |---|---|---|---|
   | exp005 | real-tail評価ハーネス + decoupled-well判定（インフラ） | DONE | beam再現: mean RMSE 11.85±1.0ft, flat割合73.3±5pp |
   | exp006 | Multi-scale NCC整列特徴 | ABANDONED | mean≤13.0ft, max≤45ft, outlier率≤10%, decoupled subsetでflat anchorに勝つ → **不合格**（mean 56.65ft）。原因: MD/TVTサンプリング密度不一致 |
   | exp007 | Sakoe-Chiba banded DTW（要numba検討、次の最優先） | TODO | 同上基準（局所傾きを動的に追従するバンドでexp006の問題に直接対策） |
   | exp008 | Particle Filter（trajectory-informed transition + prefix由来obs_sigma） | TODO | 同上基準 |
   | exp009 | 整列手法統合 — **H9の核心go/no-go** | TODO | OOF≤13.28（exp001比-1.0以上改善）, p90≤20.15, max≤72.35, decoupled subset≥15%改善 |
   | exp010 | CatBoostResidualModel追加 | TODO | 単体OOF≤LGBMの1.15倍 かつ 誤差相関<0.95 |
   | exp011 | Ridge meta-stack（fold-consistent） | TODO | stacked OOFがmin(lgbm,catboost)より0.3以上改善 |
   | exp012 | Savitzky-Golay + warm-up decay後処理 | TODO | OOF 0.1以上改善 かつ rare regime p90悪化なし |

   exp009合格時点で初めて`conf/train/default.yaml`のenable flagを昇格させ、
   `kaggle_kernel/submission.ipynb`への同期義務が発生する。exp009不合格の場合は1回だけablationし、
   それでも改善しなければH9はそこで打ち切り（postmortem対象）。
8. **[H10] trajectory(-Z)とGRベース整列の不一致度（disagreement, signed/abs）を特徴量化すれば、LightGBMが「trajectory予測を信用できない区間」を学習し系統誤差が減るはず**（2026-06-29、exp003の発見より）  
   → exp003でworst 10ウェルの4/10がtrajectory変位とTVT変位の符号すら反転していたことが根拠。H9（重いアンサンブル）着手前に軽量に検証できる候補

## 検証戦略

- **GroupKFold（well_id 単位）5-fold が基本**。ウェル内の行を別 fold に混ぜない。
- 各 fold の OOF 予測を保存し、`scripts/analyze_per_well_rmse.py` でウェル別 RMSE を可視化。外れ値ウェルを特定。
- **TVT レジーム別 RMSE** も必ず見る（稀少 = 急峻区間、通常 = 連続区間）。CLAUDE.md の `val_score_rare` / `val_score_common` に対応。
- LB との相関: 最初の 5 提出で OOF RMSE と Public LB を散布図に。乖離が大きければ検証設計を見直す。
- Public/Private 分割の挙動: 終盤は Public への過学習リスクを意識（コンペ規模が小さい場合は特に）。


## 既知のベンチマーク（リサーチ時点）

公開 Notebook の最高スコア（2026-06-29 再調査で更新。詳細は `research/public_notebooks.md`）:

| LB | Notebook | 備考 |
|---|---|---|
| 8.072 | pilkwang | EDA + Target-Free Alignment（最高公開、06-29時点でも更新の確証なし） |
| 9.251 | nihilisticneuralnet | **タイトルは「DWT」だが実装はPF+beam+DTW+NCCアンサンブル**（06-29精読で訂正） |
| 9.538 | rauffauzanrambe | 学習 Notebook |
| 9.956 🆕 | romantamrazov | BETTER SOLUTION（旧SUPER BASELINE 12.602の改善版、手法詳細未確認） |
| "TOP 3"（数値不明）🆕 | romantamrazov | SUPER SOLUTION（BETTER SOLUTIONの更なる改善版、173 upvotes、手法詳細未確認） |
| 12.602 | romantamrazov | Super Baseline（同著者の旧版） |

🆕 = 2026-06-29 Web調査で新規発見。手法詳細はローカル未DLのため未検証（要 `kaggle kernels pull` 等での手動取得）。

**追記（2026-06-29、ユーザー提供notebook精読）**: boristown「Public Rebuild」系列で公開LB **7.159**を確認（`research/public_notebooks.md`）。ただし精読の結果、この値は**配布test 3 wellのtrain重複を直接利用するsame-well shortcutで底上げされている**ことが判明（`competition_overview.md`のリーク管理セクション参照）。同notebookのリーク無視部分を除いた legitimate な技術スタック（PF+beam+NCC整列アンサンブル+LightGBM/CatBoost+Ridge stack+後処理）はGroupKFold OOF **10.42**（773 well）で、これは公開LBの数字より信頼できる「本当の改善分」の目安になる。

→ **目安**: 7 を切れたらメダル圏視野、6 切りで上位安定、5 以下で勝負（あくまで現時点・終盤に下がる前提）。**ただし公開LBの絶対値はsame-well shortcutで底上げされている疑いが強いため、今後は公開LBの順位を直接の目標にせず、GroupKFold OOF（重複ウェルを除いた検証）を信頼する。** 中位帯（romantamrazov系列）もこの2週間で明確に進化しており、公開水準は今後も下降し続ける前提でロードマップを組む。

## 週次ふりかえり

### Week 1 (2026-06-15 〜 06-21)

- やったこと:
- 学んだこと:
- 戦略変更点:
- 次週のフォーカス:

### Week 2 (2026-06-22 〜)

- ...
---

## 最終結果とふりかえり（2026-08-21 追記）

コンペ終了。**private 12.693 / public 12.959、4365位 / 6125チーム、提出 1 回**（exp001、締切2ヶ月前）。
上位: 1st 5.639 / 2nd 5.802 / 3rd 5.836、49位 6.999。flat anchor（null model）は約 15.9。

- 上位解法の要約 → `research/top_solutions.md`
- 全体ふりかえり（5 Why と次回のルール変更案）→ `postmortems/pm002_competition_retrospective.md`

このファイルの当初の想定スケジュール（Week 4-7 のアンサンブル・最終調整）は実行されなかった。
git log は 2026-07-09 で停止、実験記録は 07-17 の exp006 が最後で、**終盤 3 週間の活動記録が無い**。
