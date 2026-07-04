"""exp002/pm001: anchor制約付き beam search のドリフト・フィット品質を可視化する。

pm001（postmortems/pm001_beam_alignment_drift.md）で判明した「horizon長に対して誤差が
急激に増大する」現象を、(1) ステップ数に対する誤差蓄積カーブ、(2) 個別ウェルの整列パス
オーバーレイ、(3) 短horizon(30%, prefix代用) vs 本物のtail（本番`beam_alignment_features`と
同じ区間。train CSVはtail行にも真のTVT列を持つため直接評価できる）のRMSE分布比較、の3図で示す。

使い方:
    docker compose exec workspace python scripts/visualize_beam_alignment_drift.py --n-wells 60
"""
import argparse
import os
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.dataset import list_well_ids, load_well, load_typewell
from src.features import calibrate_gr, beam_typewell_path, _BEAM_PRESETS

FLAT_ANCHOR_RMSE = 12.8
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "docs", "rogii2026", "postmortems", "fig")


def run_one_well(well_id: str, train_dir: str, holdout_frac: float):
    """anchor位置から先のholdout区間全体でbeam pathと誤差(per-step)を計算する。"""
    hw = load_well(well_id, train_dir)
    tw = load_typewell(well_id, train_dir)
    gr_cal = calibrate_gr(hw, tw)

    prefix_mask = ~hw["is_tail"].to_numpy()
    prefix_idx = np.where(prefix_mask)[0]
    if len(prefix_idx) < 10:
        return None

    cutoff = max(int(len(prefix_idx) * (1 - holdout_frac)), 1)
    anchor_pos = prefix_idx[cutoff - 1]
    holdout_pos = prefix_idx[cutoff:]
    if len(holdout_pos) < 2:
        return None

    anchor = float(hw["TVT_input"].iloc[anchor_pos])
    gr_holdout = gr_cal.to_numpy()[holdout_pos]
    true_tvt = hw["TVT_input"].to_numpy()[holdout_pos]
    md_holdout = hw["MD"].to_numpy()[holdout_pos]
    tw_tvt = tw["TVT"].to_numpy()
    tw_gr = tw["GR"].to_numpy()

    matched_tvt, _ = beam_typewell_path(gr_holdout, tw_tvt, tw_gr, anchor, **_BEAM_PRESETS["cons"])

    beam_err = matched_tvt - true_tvt
    flat_err = anchor - true_tvt  # flat anchor予測の誤差（同じ区間で比較）

    return {
        "well_id": well_id,
        "anchor": anchor,
        "md": md_holdout,
        "true_tvt": true_tvt,
        "beam_tvt": matched_tvt,
        "beam_err": beam_err,
        "flat_err": flat_err,
        "n_steps": len(holdout_pos),
    }


def run_real_tail(well_id: str, train_dir: str):
    """本番の`beam_alignment_features`と全く同じ区間・anchorでbeam pathを計算し、
    train CSVのtail行に入っている真のTVT列(TVT_input ではなく TVT)と比較する。

    prefix代用(run_one_well)とは異なり、こちらは本番統合時に実際に処理された区間そのもの。
    """
    hw = load_well(well_id, train_dir)
    tw = load_typewell(well_id, train_dir)
    gr_cal = calibrate_gr(hw, tw)

    tail_mask = hw["is_tail"].to_numpy()
    if tail_mask.sum() < 2 or "TVT" not in hw.columns:
        return None

    anchor = float(hw["last_known_TVT"].iloc[0])
    gr_tail = gr_cal.to_numpy()[tail_mask]
    true_tvt = hw["TVT"].to_numpy()[tail_mask]
    md_tail = hw["MD"].to_numpy()[tail_mask]
    tw_tvt = tw["TVT"].to_numpy()
    tw_gr = tw["GR"].to_numpy()

    matched_tvt, _ = beam_typewell_path(gr_tail, tw_tvt, tw_gr, anchor, **_BEAM_PRESETS["cons"])

    beam_err = matched_tvt - true_tvt
    flat_err = anchor - true_tvt

    return {
        "well_id": well_id,
        "anchor": anchor,
        "md": md_tail,
        "true_tvt": true_tvt,
        "beam_tvt": matched_tvt,
        "beam_err": beam_err,
        "flat_err": flat_err,
        "n_steps": int(tail_mask.sum()),
    }


def fig_drift_vs_step(results: list[dict], out_path: str, n_bins: int = 30) -> None:
    """ステップ数(anchorからの距離)に対するRMSE蓄積カーブ。beam vs flat anchor。"""
    max_steps = max(r["n_steps"] for r in results)
    bin_edges = np.linspace(0, max_steps, n_bins + 1)
    beam_rmse_per_bin = []
    flat_rmse_per_bin = []
    centers = []

    for lo, hi in zip(bin_edges[:-1], bin_edges[1:]):
        beam_vals, flat_vals = [], []
        for r in results:
            n = r["n_steps"]
            steps = np.arange(n)
            mask = (steps >= lo) & (steps < hi)
            if not mask.any():
                continue
            be = r["beam_err"][mask]
            fe = r["flat_err"][mask]
            beam_vals.append(be[np.isfinite(be)])
            flat_vals.append(fe[np.isfinite(fe)])
        beam_cat = np.concatenate(beam_vals) if beam_vals else np.array([])
        flat_cat = np.concatenate(flat_vals) if flat_vals else np.array([])
        beam_rmse_per_bin.append(np.sqrt(np.mean(beam_cat**2)) if len(beam_cat) else np.nan)
        flat_rmse_per_bin.append(np.sqrt(np.mean(flat_cat**2)) if len(flat_cat) else np.nan)
        centers.append((lo + hi) / 2)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(centers, beam_rmse_per_bin, marker="o", label="beam search (cons)", color="crimson")
    ax.plot(centers, flat_rmse_per_bin, marker="s", label="flat anchor", color="steelblue")
    ax.axhline(FLAT_ANCHOR_RMSE, color="gray", linestyle="--", linewidth=1,
                label=f"flat anchor gate ({FLAT_ANCHOR_RMSE}ft)")
    ax.set_xlabel("steps from anchor (rows)")
    ax.set_ylabel("RMSE (ft)")
    ax.set_title("beam search error vs step count over the real tail\n(beam search vs flat anchor)")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"saved: {out_path}")


def fig_path_overlay(results: list[dict], out_path: str, n_examples: int = 4) -> None:
    """個別ウェルでの整列パス(true vs beam vs flat anchor)オーバーレイ。フィット品質を直接見る。"""
    # 最終誤差の大きさで並べ、ばらつきが見える4本を選ぶ(最良/中央2本/最悪)
    sorted_r = sorted(results, key=lambda r: np.sqrt(np.mean(r["beam_err"] ** 2)))
    picks_idx = np.linspace(0, len(sorted_r) - 1, n_examples).astype(int)
    picks = [sorted_r[i] for i in picks_idx]

    fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharey=False)
    for ax, r in zip(axes.flat, picks):
        rmse = np.sqrt(np.mean(r["beam_err"] ** 2))
        ax.plot(r["md"], r["true_tvt"], label="true TVT", color="black", linewidth=2)
        ax.plot(r["md"], r["beam_tvt"], label="beam matched TVT", color="crimson", linewidth=1.2)
        ax.axhline(r["anchor"], color="steelblue", linestyle="--", linewidth=1, label="flat anchor")
        ax.set_title(f"{r['well_id']} (n={r['n_steps']} rows, RMSE={rmse:.1f}ft)")
        ax.set_xlabel("MD")
        ax.set_ylabel("TVT")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)
    fig.suptitle("Alignment path overlay on the real tail: true vs beam search vs flat anchor")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"saved: {out_path}")


def fig_rmse_distribution(results_short: list[dict], results_real_tail: list[dict], out_path: str) -> None:
    """現行gate(prefix holdout 30%代用)と本物のtail（本番統合と同じ区間）でのper-well RMSE分布を比較。"""
    def per_well_rmse(results):
        return np.array([np.sqrt(np.mean(r["beam_err"] ** 2)) for r in results
                          if np.isfinite(r["beam_err"]).any()])

    short_rmse = per_well_rmse(results_short)
    tail_rmse = per_well_rmse(results_real_tail)

    fig, axes = plt.subplots(1, 2, figsize=(11, 5))

    ax = axes[0]
    ax.boxplot([short_rmse, tail_rmse], tick_labels=["prefix holdout 30%\n(current gate, proxy)", "real tail\n(production)"])
    ax.axhline(FLAT_ANCHOR_RMSE, color="gray", linestyle="--", label=f"flat anchor ({FLAT_ANCHOR_RMSE}ft)")
    ax.set_ylabel("per-well RMSE (ft)")
    ax.set_yscale("log")
    ax.set_title("RMSE distribution: gate proxy vs real tail (log scale)")
    ax.legend()
    ax.grid(alpha=0.3)

    ax = axes[1]
    ax.hist(short_rmse, bins=20, alpha=0.6, label="prefix holdout 30%", color="steelblue")
    ax.hist(tail_rmse, bins=20, alpha=0.6, label="real tail", color="crimson")
    ax.axvline(FLAT_ANCHOR_RMSE, color="gray", linestyle="--", label=f"flat anchor ({FLAT_ANCHOR_RMSE}ft)")
    ax.set_xlabel("per-well RMSE (ft)")
    ax.set_ylabel("well count")
    ax.set_title("RMSE distribution histogram")
    ax.legend()
    ax.grid(alpha=0.3)

    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"saved: {out_path}")

    print(f"\nprefix holdout 30% (gate proxy): mean={short_rmse.mean():.2f} median={np.median(short_rmse):.2f} "
          f"frac<flat_anchor={(short_rmse < FLAT_ANCHOR_RMSE).mean():.1%}")
    print(f"real tail (production): mean={tail_rmse.mean():.2f} median={np.median(tail_rmse):.2f} "
          f"frac<flat_anchor={(tail_rmse < FLAT_ANCHOR_RMSE).mean():.1%}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-dir", default=os.environ.get("ROGII_TRAIN_DIR", "data/raw/train"))
    parser.add_argument("--n-wells", type=int, default=60)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)

    well_ids = list_well_ids(args.train_dir)
    rng = np.random.default_rng(args.seed)
    sample = rng.choice(well_ids, size=min(args.n_wells, len(well_ids)), replace=False)

    print(f"running beam search on {len(sample)} wells (real tail, same as production beam_alignment_features)...")
    results_real_tail = []
    for well_id in sample:
        r = run_real_tail(well_id, args.train_dir)
        if r is not None:
            results_real_tail.append(r)
    print(f"  -> {len(results_real_tail)} wells succeeded")

    print(f"running beam search on {len(sample)} wells (prefix holdout=30%, current gate proxy)...")
    results_short = []
    for well_id in sample:
        r = run_one_well(well_id, args.train_dir, holdout_frac=0.3)
        if r is not None:
            results_short.append(r)
    print(f"  -> {len(results_short)} wells succeeded")

    fig_drift_vs_step(results_real_tail, os.path.join(OUT_DIR, "pm001_drift_vs_step.png"))
    fig_path_overlay(results_real_tail, os.path.join(OUT_DIR, "pm001_path_overlay.png"))
    fig_rmse_distribution(results_short, results_real_tail, os.path.join(OUT_DIR, "pm001_rmse_distribution.png"))


if __name__ == "__main__":
    main()
