# docs/_templates/

新コンペ開始時に `docs/{competition}/` へコピーされる雛形。`/kaggle-new {competition}` が自動でコピーする。

`{PLACEHOLDER}` は実際の値に置き換える。**空欄のまま次のフェーズに進まない**（CLAUDE.md 第3節のゲート）。

| ファイル | 対応ゲート |
|---|---|
| `gates.md` | **全ゲートの宣言（ダッシュボードが読む）** |
| `competition_overview.md` | R1 |
| `research/discussions.md` | **R2（最も崩れやすい。最優先）** |
| `research/past_solutions.md` | R3 |
| `research/public_notebooks.md` | R4 |
| `formulations.md` | **R5（定式化の視野を確保する要）** |
| `eda/README.md` | R6 |
| `strategy.md` | 全期間（時間予算ブロックを毎週更新） |
| `experiments.md` | 各実験完了時 |
| `experiments/exp000_template.md` | 各実験着手時（`/kaggle-exp` が使う） |
| `postmortems/pm000_template.md` | 大きな失敗時 |
| `tools.md` | 分析スクリプト追加時 |
