# Kaggle 提出ワークフロー

`src/` や `make_submission.py` を毎回手動アップロードしないための仕組み。

- `submission.ipynb`: 推論ロジックを埋め込んだ自己完結 Notebook（`src/dataset.py` / `src/features.py` / `scripts/make_submission.py::run_inference` のコピー）。**コードを変更したときだけ**編集して push する。
- モデル本体（`outputs/models/fold*.txt`）は別の Kaggle Dataset としてアップロードし、Notebook にアタッチする。**実験ごとに変わるのはここだけ**。

## 一度だけ行うセットアップ

1. モデル用 Dataset を作成（`outputs/models/` に学習済みモデルがある状態で実行）

   ```bash
   kaggle datasets init -p outputs/models
   # outputs/models/dataset-metadata.json の "id" を "tkm427/rogii-models" に変更
   kaggle datasets create -p outputs/models
   ```

2. `kernel-metadata.json` の `dataset_sources` / `competition_sources` が実際の slug と合っているか確認
3. Notebook を初回 push

   ```bash
   kaggle kernels push -p kaggle_kernel/
   ```

## 実験ごとの提出（2コマンド + ブラウザでの Submit ボタン1クリック）

```bash
# 1. 新しいモデルで Dataset を更新
kaggle datasets version -p outputs/models -m "exp00X: <変更内容>"

# 2. 推論コードを変更した場合のみ Notebook も更新（変更なしならスキップ可）
kaggle kernels push -p kaggle_kernel/
```

その後 Kaggle 上で該当 Notebook を開き、Run All → 「Submit to Competition」をクリックする
（Code Competition の仕様上、この最終提出操作は CLI 化できない）。

## TODO（初回利用時に埋める）

- `kernel-metadata.json` の `id` / `dataset_sources`: 実際の Kaggle username に置き換え済み（`tkm427`）か確認
- `submission.ipynb` の `MODEL_DIR` / `TEST_DIR`: 実際にアタッチした Dataset 名・コンペの入力パスに合わせて修正
