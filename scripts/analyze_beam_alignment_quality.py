"""exp002 必須ゲート: anchor制約付き beam search (src/features.py::beam_typewell_path) の
prefix-holdout sanity check。flat anchor RMSE (12.8ft, eda/null_model_baseline.md) を下回ることを
確認してから build_feature_frame に統合する。

使い方:
    python scripts/analyze_beam_alignment_quality.py --n-wells 50
"""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.dataset import list_well_ids, load_well, load_typewell
from src.features import calibrate_gr, beam_alignment_quality

FLAT_ANCHOR_RMSE = 12.8


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-dir", default=os.environ.get("ROGII_TRAIN_DIR", "data/raw/train"))
    parser.add_argument("--n-wells", type=int, default=50)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    well_ids = list_well_ids(args.train_dir)
    rng = np.random.default_rng(args.seed)
    sample = rng.choice(well_ids, size=min(args.n_wells, len(well_ids)), replace=False)

    rmses = []
    for well_id in sample:
        hw = load_well(well_id, args.train_dir)
        tw = load_typewell(well_id, args.train_dir)
        gr_cal = calibrate_gr(hw, tw)
        rmse = beam_alignment_quality(hw, tw, gr_cal)
        if np.isfinite(rmse):
            rmses.append(rmse)

    rmses = np.array(rmses)
    print(f"wells evaluated: {len(rmses)} / {len(sample)}")
    print(f"beam alignment holdout RMSE: mean={rmses.mean():.2f} median={np.median(rmses):.2f} "
          f"p90={np.percentile(rmses, 90):.2f}")
    print(f"flat anchor RMSE (reference): {FLAT_ANCHOR_RMSE}")
    frac_better = float((rmses < FLAT_ANCHOR_RMSE).mean())
    print(f"flat anchorを下回ったウェル割合: {frac_better:.1%}")
    if rmses.mean() < FLAT_ANCHOR_RMSE:
        print("GATE PASSED: 統合に進んでよい")
    else:
        print("GATE FAILED: パラメータ調整 or exp002中断を検討")


if __name__ == "__main__":
    main()
