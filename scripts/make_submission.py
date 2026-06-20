"""推論 + submission.csv 生成。

scripts/train.py で保存した fold モデルをアンサンブル（平均）し、test wells の tail 行を予測する。
後処理: 値域クリップのみ（exp001 v1）。DTW信頼度シュリンク等は exp002 以降。

`run_inference` は Hydra/OmegaConf に依存しないプレーンな関数。Kaggle Notebook へコピーする際は
src/dataset.py, src/features.py, src/model.py の内容（DTW関数は不要）と本関数だけを使い、
main() の Hydra 部分は使わずプレーンな引数で直接呼び出すこと（CLAUDE.md 運用ルール参照）。
"""
import glob
import os
import sys

import lightgbm as lgb
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.dataset import list_well_ids, load_well, load_typewell
from src.features import build_feature_frame

# scripts/train.py の NON_FEATURE_COLS と同期させること
NON_FEATURE_COLS = ["well_id", "row_index", "is_tail", "TVT", "resid", "tvt_diff_abs"]


def run_inference(
    models: list[lgb.Booster],
    test_dir: str,
    gr_rolling_windows: list[int],
    tvt_min: float,
    tvt_max: float,
) -> pd.DataFrame:
    """test_dir 配下の全ウェルに対して推論し、submission 用 DataFrame（id, tvt）を返す。"""
    well_ids = list_well_ids(test_dir)
    rows = []
    for well_id in well_ids:
        hw = load_well(well_id, test_dir)
        tw = load_typewell(well_id, test_dir)
        feat = build_feature_frame(hw, tw, gr_rolling_windows)

        tail_feat = feat[feat["is_tail"]].copy()
        feature_cols = [c for c in feat.columns if c not in NON_FEATURE_COLS]

        preds = np.mean([m.predict(tail_feat[feature_cols]) for m in models], axis=0)
        pred_tvt = tail_feat["last_known_TVT"].to_numpy() + preds
        pred_tvt = np.clip(pred_tvt, tvt_min, tvt_max)

        ids = [f"{well_id}_{int(r)}" for r in tail_feat["row_index"]]
        rows.append(pd.DataFrame({"id": ids, "tvt": pred_tvt}))

    return pd.concat(rows, ignore_index=True)


def main() -> None:
    import hydra
    from omegaconf import DictConfig

    @hydra.main(version_base=None, config_path="../conf", config_name="config")
    def _main(cfg: DictConfig) -> None:
        model_paths = sorted(glob.glob("outputs/models/fold*.txt"))
        assert model_paths, "outputs/models/fold*.txt が見つかりません。先に scripts/train.py を実行してください。"
        models = [lgb.Booster(model_file=p) for p in model_paths]

        submission = run_inference(
            models, cfg.data.test_dir, cfg.train.gr_rolling_windows, cfg.data.tvt_min, cfg.data.tvt_max
        )

        os.makedirs("outputs", exist_ok=True)
        submission.to_csv("outputs/submission.csv", index=False)
        print(f"saved outputs/submission.csv ({len(submission)} rows)")

    _main()


if __name__ == "__main__":
    main()
