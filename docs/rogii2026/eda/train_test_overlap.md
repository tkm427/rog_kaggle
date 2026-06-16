# EDA: Train/Test ウェル重複とリーク含意

実行日: 2026-06-16  
スクリプト: `scripts/eda_overview.py`

## 発見

**配布された 3 本の test ウェルはすべて train にも存在する。**

```
Train/Test 重複ウェル: {'000d7d20', '00bbac68', '00e12e8b'}
```

## 含意

### Public LB について
- Public LB の採点に使われる test wells（配布版）は train データと完全一致。
- → `PF_SELECTOR_USE_SAME_WELL_PHYSICAL=True`（same-well 物理経路）を使うと
  **訓練データの物理的な情報が答えへのショートカット**になる。
- pilkwang Notebook が警告している「public-aggressive」モード（→ `competition_overview.md` 参照）はまさにこのリスク。

### Private LB について
- 隠れテストセットは未知のウェルになる可能性が高い（コード提出でリラン方式）。
- same-well 依存の特徴は **Private で崩壊するリスクが高い**。

## 推奨アクション

1. **GroupKFold (well_id)** で CV を組む。同一ウェルを val に丸ごと入れる。
2. same-well 特徴（物理経路マッチ等）は `PF_SELECTOR_USE_SAME_WELL_PHYSICAL=False`
   をデフォルトにし、True との比較は診断目的のみ。
3. CV RMSE と Public LB の乖離が大きい場合は same-well 依存を疑う。

## 備考

`competition_overview.md` の「Leakage Risk Table」で `PF_SELECTOR_USE_SAME_WELL_PHYSICAL` の
True/False 両方で比較するよう明示されている。本 EDA でその重要性が数値的に裏付けられた。
