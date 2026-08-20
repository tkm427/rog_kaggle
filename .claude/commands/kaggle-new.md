---
description: 新コンペの立ち上げ。docs/{competition}/ を生成し Phase 0/1 のゲートを展開する
argument-hint: <competition-slug>
---

新コンペ `$ARGUMENTS` を立ち上げる。`$ARGUMENTS` が空なら、コンペの slug を先に尋ねること。

## 1. ドキュメントの生成

`docs/_templates/` を `docs/$ARGUMENTS/` にコピーする（`README.md` は除く）。

```bash
mkdir -p docs/$ARGUMENTS
cp -r docs/_templates/. docs/$ARGUMENTS/
rm docs/$ARGUMENTS/README.md
mv docs/$ARGUMENTS/experiments/exp000_template.md docs/$ARGUMENTS/experiments/_template.md
mv docs/$ARGUMENTS/postmortems/pm000_template.md docs/$ARGUMENTS/postmortems/_template.md
```

生成後、コンペページを読んで `competition_overview.md` の基本情報（URL / ホスト / 種別 /
開始・締切 / 評価指標 / Code Comp 制約）と `strategy.md` の期間・時間予算ブロックを埋める。
**Kaggle は SPA なので WebFetch では本文が取れない。claude-in-chrome を使う。**

## 2. リポジトリのリセット（人間に確認してから実行）

このリポジトリはコンペをまたいで使い回す。以下を提示し、承認を得てから実行する。

- `conf/train/expXXX.yaml` など旧コンペ固有の config を削除（`conf/config.yaml` の骨格は残す）
- `src/{dataset,features,model}.py` を新コンペ用に作り直す（旧実装は git 履歴から引ける）
- `scripts/analyze_*.py` / `visualize_*.py` の旧コンペ固有スクリプトを削除
- `kaggle_kernel/kernel-metadata.json` の id / title / competition_sources を更新、
  `submission.ipynb` は新規作成
- `data/raw/` を入れ替え
- `pyproject.toml` の依存を見直す — **Gate S3 の NN 系依存（torch / timm 等）を忘れない**

**`docs/{旧コンペ}/` は削除しない。** 次コンペの資産として残す。

## 3. Phase 0/1 のゲートを TodoWrite に展開

CLAUDE.md 第3節から以下をタスク化する。**R2 と R5 を最優先に置く。**

- R1 `competition_overview.md` 完成
- **R2 Discussion upvote 上位 10 + host 投稿の本文・コメント欄を読んで要約（未読 0 件）**
- R3 類似コンペ TOP5 の要約
- R4 公開 NB 3 本を実コードで読み、リーク判定
- **R5 定式化候補 3 案以上を `formulations.md` に列挙**
- R6 EDA の発見 3〜5 本

## 4. ダッシュボードの初期生成

```bash
python3 scripts/build_dashboard.py -c $ARGUMENTS --open
```

全ゲートが未達の状態で表示されることを確認する。以後、人間はここを見る。

## 5. 報告

生成したファイル一覧と、Phase 1 の期限（開始から 7 日）、最初の一手を提示する。
