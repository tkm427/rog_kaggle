# 本コンペ (ROGII 2026) の上位解法

> コンペ終了後（2026-08-21）に writeup 本文を読んで要約。最終順位: 1st 5.639 / 2nd 5.802 / 3rd 5.836（private RMSE）。
> 自分（tkm427）は private 12.693、4365位 / 6125チーム、提出 1 回。

## 1st place — Ruby (@w5833946), private 5.639 / public 5.980

- URL: https://www.kaggle.com/competitions/rogii-wellbore-geology-prediction/writeups/1st-place-solution
- 推論 NB: https://www.kaggle.com/code/w5833946/submit-reproduce / 学習: https://github.com/IAmAValidUsername/kaggle_ROGII_1st_place_solution_Ruby

**定式化**: 回帰ではなく **2D alignment タスク** とし、cross-entropy を主損失にする。
- グリッド: 水平坑井 345 位置（32分の1にダウンサンプル、可視1024 + target 10000）× typewell 400 位置（last visible TVT ±100ft, 0.5ft 分解能）
- 全 TVT は **last visible TVT を原点とした相対値**
- 学習ターゲットは正解整列を中心に指数平滑した確率分布（typewell 軸で正規化）
- 補助損失: 期待 TVT パスへの Huber、GR ペナルティ `mean(prob × grid_GR_gap)`

**モデル**: 2D U-Net + ConvNeXt (`timm/convnext_small.in12k_ft_in1k_384`)。LayerNorm→BatchNorm 置換が一貫して良い（BF16 必須）。down/up sampling は average pool + interpolate が学習可能版より良い。

**特徴（画像チャネル）**: typewell GR / GR-is-NaN / TVT、水平坑井のビンごとの GR mean・nan率・std・slope・last−first・二次フィット係数と残差RMSE・可視区間TVT平均、交互作用 `|typewell_GR − horizontal_GR|` `|typewell_TVT − visible_TVT|`、`z_diff`、**PF の 2D 粒子確率ヒートマップ**、XY近傍予測。typewell GR は可視区間で (TVT,GR) をビン集計して校正。

**Particle Filter**（単体 CV ≈ 7.4）: 公開ベースラインからの改善点は「低確率の大ジャンプを許す」「typewell GR 校正」「FFBSi 平滑化」「多様な cfg プロファイルのブレンド」「64サンプルのビン単位で粒子更新」。

**XY 近傍**（単体 CV ≈ 11.4）: 局所地層面 `S = TVT + Z + C` が局所線形と仮定して `ΔTVT = aΔX + bΔY − ΔZ`、(a,b) を近傍の重み付き最小二乗で推定。CV は一貫して +0.3 改善するが public LB は悪化 → 近傍品質統計を5種調べても説明できず「ラベルの不整合」と結論し **CV を信じた**（結果的に private で正解）。

**Augmentation**（最重要は2つ）:
- **Z-shift**: `TVT + Z` を保ったまま TVT パスをランダムサンプル（実 TVT 差分の block bootstrap）。GR は `TVT + TVTノイズ` で typewell から再生成。稀に fault jump も注入
- **GR transform**: typewell GR に `GR' = a·GR + b`。絶対値でなく形状に依存させる
- 他: 逆走パス、MD stretch、2Dチャネルマスク、GR noise shift、tail crop、typewell軸の系列マスク、PF チャネルの rotate/shift（ショートカット学習の抑制）

**アンサンブル**: XY 近傍が信頼できないウェル（約10%）には XY チャネル無しモデル + z_diff を使う。6モデル weighted → CV 4.627 / public 5.980 / private 5.639。

**効かなかったもの**: Transformer backbone、合成データでの2段階事前学習（同時学習の方が良い）、最終単体モデルでの PF 特徴（aug と backbone 強化後は寄与消失、多様性目的で残した）、凝った loss weighting、ラベルが目視で悪いウェルの除去、モデル/解像度のスケールアップ。

## 2nd place — Bilzard (@tatamikenn), private 5.802 / public 6.146

- URL: https://www.kaggle.com/competitions/rogii-wellbore-geology-prediction/writeups/2nd-place-solution-anchorcnn-conditional-probab

**データからの核心的発見**: `z_layer := TVT + z − b_well` と置くと恒等式

    dTVT = dz_layer − dz    …(1)

`dz_layer/dMD`（構造傾斜）は実データでは **階段状**（大半の区間で一定、たまにステップ、ステップは約10%の列のみ）。つまりステップが無い区間では `dTVT` の形は `−dz` と完全一致する。**`dz/dMD` を入力特徴にすると、モデルの仕事は「滑らかな構造傾斜 dz_layer の推定」だけに縮む。**

**合成データ**: `GR_obs = f(TVT) + r(TVT)`（f = typewell の TVT–GR プロファイル）という層ケーキ仮定に基づき、任意の TVT 軌道から無限にデータを生成できる。
- train の typewell は **54 個の master 系列に統合できる**（discussion の指摘を自前検証）。任意の窓を切り出して f を生成
- 軌道は実軌道の mixup + 鉛直シフトで変形し、元系統の掘削帯における分位点を対象系統の同分位点に写して「再スキン」
- 残差 `r = δ_w(TVT) + ε`（δ_w = ウェル固有の系統的GRずれ、ε = 自己相関を持つ非白色ノイズ）。実残差を貼り付ける方式と AR モデルで合成する方式の2通り
- 変形中は z ではなく **z_layer を内部表現に持つ**ことで恒等式(1)を構成的に保つ

**モデル AnchorCNN**: 入力 `(9, 512, 336)` 画像（縦 = typewell level 0.5ft/bin ±128ft、横 = MD 32ft/列、先頭16列が既知の pre-PS 区間）。9ch = GR mismatch(typewell) / lateral GR / GR validity / typewell coverage / 既知TVTのガウシアン ridge / 既知列フラグ / **GR mismatch(pre-PS 自ウェル基準)** / その coverage / **dip z**。
efficientnet-b0 の各 stage を FPN 風にフュージョンし `(B, 21, 128, 336)` の state grid に写す。各アンカー（座標 (MD, TVT) = level 仮説）から **条件付き移動分布 `P(dTVT | anchor)`** を予測。移動語彙は 21 クラス `{0, ±2, …, ±20} ft/列`。物体検出の anchor 発想の転用。

**なぜ確率場か**: typewell GR は似た縞が繰り返すため posterior は多峰。**単一の teacher path を回帰するモデルはモード間の平均に潰れ、どの仮説にも対応しないパスを出す**（初期実験で確認）。

**学習**: 正解パス上のアンカーにのみ teacher forcing で CE（+ bin 内位置の補助損失）。各 epoch で実ウェル(~620/fold) と オンライン生成した合成ウェル 2048 本を混合。120 epoch、warmup 後 constant lr 1e-3（WSD, decay なし）、EMA。5 fold × 3 seed で単一 GPU 約 10 時間。

**デコード**: rollout サンプリングではなく **DP による期待値デコード**（`p_{k+1}(s) = Σ_{s'} p_k(s')·P(dTVT = s−s' | anchor(s',k))`, `TVT_hat(k) = Σ_s p_k(s)·TVT(s)`）。Viterbi など mode-tracking は一貫して劣った。

**TTA/アンサンブル**: 5fold × 3seed = 15ckpt × **MD-phase TTA 8視点**（列の切り出し位相を 0〜56ft でずらす。GR の相関長 ~18ft に対し 32ft 列の箱平均は粗くエイリアシングするため）× 2解像度(32ft/16ft)。T4 で 200 ウェル 40 分。

**頑健な検証（leave-largest-contribution-out）**: pooled RMSE は「破滅的な数ウェル」に支配される。base と treat のウェル別 SSE 差 `g_w` を `|g_w|` の降順に除去し、改善が消える除去数 `k*` を見る。`k*` が十分大きくない候補は棄却。例: OOF −0.28 に見えた候補は 773 中 8 ウェル除去で消滅 → 棄却。採用したものは 52 ウェル（public LB のサイズ）除去でも生き残った。

**効かなかったもの**: rollout バンドル(N=1024)からの選択（reranker / GRPO）— oracle は数ft良いが選択器が必ず過学習し DP 期待値に勝てなかった。明示的な formation モデリング — 場の粗い地形は捉えるが破滅ウェルを直せない。専門家のラベルは formation を直接参照せず GR マッチングの相対判断だから、と推測。

## 上位2解法の共通構造（＝このコンペの「正解の骨格」）

1. **タスクを「行ごとの回帰」ではなく「2D 整列（typewell level × MD）の確率場推定」として定式化する**
2. **多峰性を潰さない**。単一パスに畳んだ瞬間に平均モードへ崩壊する
3. **CNN で 2D 画像として解く**（Transformer はどちらも負け）
4. **確率場からのデコードは DP による期待値**（Viterbi / サンプリング選択はいずれも劣る）
5. **`GR = f(TVT)` 生成モデルによる合成データ + 重い augmentation** が精度の主エンジン
6. **`z`（trajectory）は最強の prior**。1st は `z_diff` / XY近傍最小二乗、2nd は恒等式 `dTVT = dz_layer − dz` として使う
7. **last visible TVT を原点とする相対座標**
8. **public LB を信じず OOF/CV を信じる**。1st は CV を採って public 悪化を受け入れ、2nd は少数ウェル支配に頑健な受け入れ検定を設計した

## 事前に公開されていた情報（重要）

hengck23 のスレッド（2026-05 投稿、62 upvote、コメント49件）に上位解法の中核がほぼ全部書かれていた。
https://www.kaggle.com/competitions/rogii-wellbore-geology-prediction/discussion/699853

- 2D heatmap → CNN → MDN による multi-trajectory prediction（**2nd place が明示的に出発点と述べている**）+ 動くサンプル NB 2 本
  (https://www.kaggle.com/code/hengck23/cnn-mtp-example, https://www.kaggle.com/code/hengck23/cnn-sdf-example)
- 参照論文: Alyaev et al. "Direct Multi-Modal Inversion of Geophysical Logs Using Deep Learning" https://arxiv.org/pdf/2201.01871
- **dz annotation leak**: ANCC 等は約15制御点の区分線形（StarSteer の疎な dip アノテーション）→ 2nd の恒等式(1)そのもの
- `cumsum(−dz − offset)`（離散 offset）だけで **RMSE 7.7**（当時の公開最高 8.07 より良い）
- 地層面の kriging / grid 補間で validation RMSE ≈ 11（1st の XY近傍単体 11.4 とほぼ同じ）
- host @igorakuvaev のヒント: PS 以前の lateral GR は typewell GR より分解能が高いので GR 相関にはそちらを使うべき（2nd の x6 チャネル）
