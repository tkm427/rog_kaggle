"""H9共通ハーネス: 複数の整列手法（beam/NCC/DTW/PF）を実tail区間で評価し、per-well RMSE分布と
trajectory-TVTデカップリングウェルでの性能を報告する（exp005）。

pm001（postmortems/pm001_beam_alignment_drift.md）の教訓を踏まえた設計:
- 必ず実tail区間（本番`build_feature_frame`が処理する区間そのもの）で評価する。
  代用データ（prefixのholdoutなど）は本番区間との違い（系列の統計的性質）を混同するため使わない。
- 平均RMSEだけでなく、per-wellの外れ値分布（frac_outlier_gt_3x_flat, max）も必ず確認する。
  平均が基準を満たしていても少数の大外れが下流モデル(LightGBM)を悪化させることがある(pm001)。

各整列手法は `MATCHERS` に統一シグネチャで登録する:
    matcher(gr_values, tw_tvt, tw_gr, start_tvt, **kwargs) -> (matched_tvt, matched_gr_or_none)
（`src/features.py::beam_typewell_path` と同じ規約）。exp006以降はこのファイルの MATCHERS に
一手法ずつ追加していく。

使い方:
    docker compose exec workspace python scripts/analyze_alignment_quality.py --matcher beam --n-wells 60 --seed 42
"""
import argparse
import os
import sys
from typing import Callable

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.dataset import list_well_ids, load_well, load_typewell
from src.features import calibrate_gr, beam_typewell_path, ncc_typewell_path, _BEAM_PRESETS

FLAT_ANCHOR_RMSE = 12.8

MATCHERS: dict[str, Callable] = {
    "beam": lambda gr, tw_tvt, tw_gr, anchor, **kw: beam_typewell_path(
        gr, tw_tvt, tw_gr, anchor, **{**_BEAM_PRESETS["cons"], **kw}
    ),
    "ncc": ncc_typewell_path,
}


def label_trajectory_tvt_decoupled(hw: pd.DataFrame, flat_eps: float = 2.0) -> bool | None:
    """tail内での neg_Z 正味変位と真TVT正味変位の符号を比較する（exp003のworst-10分析を全ウェルに拡張）。

    **analysis-only（分析専用）**: 真の tail TVT を読むため、hidden-tail target leakage に該当する。
    `src/features.py` / `scripts/make_submission.py` / `kaggle_kernel/submission.ipynb` からは
    絶対に import しないこと。このファイルはウェル別性能分析の目的でのみ使う。

    Returns:
        None: tail内でTVTがほぼ動かない（flat well、|net_tvt| < flat_eps）ため判定対象外。
        True: trajectoryとTVTの正味変位の符号が逆転している（デカップリングウェル）。
        False: 符号が一致している。
    """
    tail = hw.loc[hw["is_tail"]]
    if len(tail) < 2 or "TVT" not in tail.columns:
        return None
    true_tvt = tail["TVT"].to_numpy()
    neg_z = tail["neg_Z"].to_numpy()
    valid = np.isfinite(true_tvt) & np.isfinite(neg_z)
    if valid.sum() < 2:
        return None
    idx = np.where(valid)[0]
    net_tvt = true_tvt[idx[-1]] - true_tvt[idx[0]]
    net_negz = neg_z[idx[-1]] - neg_z[idx[0]]
    if abs(net_tvt) < flat_eps:
        return None
    return bool(np.sign(net_tvt) != np.sign(net_negz))


def evaluate_alignment_on_real_tail(
    matcher_name: str,
    well_ids: list[str],
    train_dir: str,
    matcher_kwargs: dict | None = None,
) -> pd.DataFrame:
    """実tail区間（本番`build_feature_frame`が処理する区間そのもの）で整列手法を評価する。

    beam系のsanity check（`scripts/visualize_beam_alignment_drift.py::run_real_tail`）と同じ
    「本物のtailで直接評価する」設計を、任意のmatcherに一般化したもの。
    """
    matcher = MATCHERS[matcher_name]
    kwargs = matcher_kwargs or {}
    rows = []
    for well_id in well_ids:
        hw = load_well(well_id, train_dir)
        tw = load_typewell(well_id, train_dir)
        tail_mask = hw["is_tail"].to_numpy()
        if tail_mask.sum() < 2 or "TVT" not in hw.columns:
            continue

        gr_cal = calibrate_gr(hw, tw)
        anchor = float(hw["last_known_TVT"].iloc[0])
        gr_tail = gr_cal.to_numpy()[tail_mask]
        true_tvt = hw["TVT"].to_numpy()[tail_mask]
        tw_tvt = tw["TVT"].to_numpy()
        tw_gr = tw["GR"].to_numpy()

        matched_tvt, _ = matcher(gr_tail, tw_tvt, tw_gr, anchor, **kwargs)
        err = matched_tvt - true_tvt
        valid = np.isfinite(err)
        if not valid.any():
            continue
        rmse = float(np.sqrt(np.mean(err[valid] ** 2)))

        flat_err = anchor - true_tvt
        flat_valid = np.isfinite(flat_err)
        flat_rmse = float(np.sqrt(np.mean(flat_err[flat_valid] ** 2))) if flat_valid.any() else float("nan")

        rows.append({
            "well_id": well_id,
            "n_rows": int(tail_mask.sum()),
            "rmse": rmse,
            "flat_anchor_rmse": flat_rmse,
            "is_decoupled": label_trajectory_tvt_decoupled(hw),
        })
    return pd.DataFrame(rows)


def summarize_alignment_quality(per_well: pd.DataFrame) -> dict:
    """全体とdecoupled subsetの両方で統計量を算出。

    frac_below_flat_anchor: 各ウェル自身のflat anchor RMSE（そのウェルの実際の変位量に応じて
    変わる）と比較。3x外れ値判定など、ウェルごとの「何もしないより悪化したか」を見るのに使う。
    frac_below_global_flat_anchor: pm001/exp002が使ったのと同じ、全ウェル共通の定数
    FLAT_ANCHOR_RMSE(12.8ft, eda/null_model_baseline.md)と比較。既存分析との再現性確認用。
    """
    def _stats(df: pd.DataFrame) -> dict:
        if len(df) == 0:
            return {k: float("nan") for k in
                    ["mean", "median", "p90", "max", "frac_below_flat_anchor",
                     "frac_below_global_flat_anchor", "frac_outlier_gt_3x_flat", "n"]}
        rmse = df["rmse"].to_numpy()
        flat = df["flat_anchor_rmse"].to_numpy()
        return {
            "n": int(len(df)),
            "mean": float(np.mean(rmse)),
            "median": float(np.median(rmse)),
            "p90": float(np.percentile(rmse, 90)),
            "max": float(np.max(rmse)),
            "frac_below_flat_anchor": float(np.mean(rmse < flat)),
            "frac_below_global_flat_anchor": float(np.mean(rmse < FLAT_ANCHOR_RMSE)),
            "frac_outlier_gt_3x_flat": float(np.mean(rmse > 3 * flat)),
        }

    decoupled = per_well[per_well["is_decoupled"] == True]  # noqa: E712
    return {
        "overall": _stats(per_well),
        "decoupled": _stats(decoupled),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-dir", default=os.environ.get("ROGII_TRAIN_DIR", "data/raw/train"))
    parser.add_argument("--matcher", default="beam", choices=list(MATCHERS.keys()))
    parser.add_argument("--n-wells", type=int, default=60)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    well_ids = list_well_ids(args.train_dir)
    rng = np.random.default_rng(args.seed)
    sample = rng.choice(well_ids, size=min(args.n_wells, len(well_ids)), replace=False).tolist()

    print(f"matcher={args.matcher} n_wells_requested={len(sample)}")
    per_well = evaluate_alignment_on_real_tail(args.matcher, sample, args.train_dir)
    print(f"n_wells_succeeded={len(per_well)}")

    summary = summarize_alignment_quality(per_well)
    for group, stats in summary.items():
        print(f"\n[{group}] n={stats['n']}")
        if stats["n"] == 0:
            continue
        print(f"  mean={stats['mean']:.2f} median={stats['median']:.2f} p90={stats['p90']:.2f} max={stats['max']:.2f}")
        print(f"  frac_below_flat_anchor(per-well)={stats['frac_below_flat_anchor']:.1%}")
        print(f"  frac_below_flat_anchor(global {FLAT_ANCHOR_RMSE}ft)={stats['frac_below_global_flat_anchor']:.1%}")
        print(f"  frac_outlier_gt_3x_flat={stats['frac_outlier_gt_3x_flat']:.1%}")
    print(f"\nflat anchor RMSE (reference, eda/null_model_baseline.md): {FLAT_ANCHOR_RMSE}")


if __name__ == "__main__":
    main()
