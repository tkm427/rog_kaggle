"""exp003: ウェル別残差分析。

`outputs/oof.parquet`（scripts/train.py 出力）からウェル別RMSE（overall/rare/common）を集計し、
外れ値ウェルを抽出する。tail長・rare行比率とウェル別RMSEの相関を見て、baselineモデル
（trajectory+GR特徴のみ）がどのウェル群で系統的に弱いかを特定する。

使い方:
    docker compose exec workspace python scripts/analyze_per_well_rmse.py
"""
import argparse
import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "docs", "rogii2026", "eda", "fig")


def per_well_table(oof: pd.DataFrame, rare_threshold: float) -> pd.DataFrame:
    rows = []
    for well_id, g in oof.groupby("well_id"):
        err = (g["TVT"] - g["oof_pred"]).to_numpy()
        rare_mask = g["tvt_diff_abs"].to_numpy() > rare_threshold
        rmse_overall = float(np.sqrt(np.mean(err ** 2)))
        rmse_rare = float(np.sqrt(np.mean(err[rare_mask] ** 2))) if rare_mask.any() else np.nan
        rmse_common = float(np.sqrt(np.mean(err[~rare_mask] ** 2))) if (~rare_mask).any() else np.nan
        rows.append({
            "well_id": well_id,
            "n_rows": len(g),
            "rare_frac": float(rare_mask.mean()),
            "rmse_overall": rmse_overall,
            "rmse_rare": rmse_rare,
            "rmse_common": rmse_common,
        })
    return pd.DataFrame(rows).sort_values("rmse_overall", ascending=False).reset_index(drop=True)


def fig_rmse_histogram(table: pd.DataFrame, out_path: str) -> None:
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.hist(table["rmse_overall"], bins=30, color="steelblue", alpha=0.8)
    ax.axvline(table["rmse_overall"].mean(), color="crimson", linestyle="--",
               label=f"mean={table['rmse_overall'].mean():.2f}")
    ax.axvline(table["rmse_overall"].median(), color="darkorange", linestyle="--",
               label=f"median={table['rmse_overall'].median():.2f}")
    ax.set_xlabel("per-well RMSE (ft)")
    ax.set_ylabel("well count")
    ax.set_title("exp003: per-well RMSE distribution")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"saved: {out_path}")


def fig_scatter(table: pd.DataFrame, x_col: str, x_label: str, out_path: str) -> None:
    corr = table[[x_col, "rmse_overall"]].corr().iloc[0, 1]
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(table[x_col], table["rmse_overall"], alpha=0.6, color="steelblue")
    ax.set_xlabel(x_label)
    ax.set_ylabel("per-well RMSE (ft)")
    ax.set_title(f"exp003: RMSE vs {x_label} (corr={corr:.3f})")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"saved: {out_path} (corr={corr:.3f})")


def fig_worst_wells(oof: pd.DataFrame, table: pd.DataFrame, out_path: str, n_examples: int = 4) -> None:
    """RMSE最悪のウェルでtrue vs predicted TVTを直接見る。"""
    worst = table.head(n_examples)
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    for ax, (_, row) in zip(axes.flat, worst.iterrows()):
        g = oof[oof["well_id"] == row["well_id"]].sort_values("row_index")
        ax.plot(g["row_index"], g["TVT"], label="true TVT", color="black", linewidth=2)
        ax.plot(g["row_index"], g["oof_pred"], label="oof pred", color="crimson", linewidth=1.2)
        ax.set_title(f"{row['well_id']} (n={row['n_rows']:.0f}, RMSE={row['rmse_overall']:.1f}ft)")
        ax.set_xlabel("row_index (tail)")
        ax.set_ylabel("TVT")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)
    fig.suptitle("exp003: worst wells by OOF RMSE (true vs predicted TVT)")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"saved: {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--oof-path", default="outputs/oof.parquet")
    parser.add_argument("--rare-threshold", type=float, default=0.91)
    parser.add_argument("--top-n", type=int, default=10)
    args = parser.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)

    oof = pd.read_parquet(args.oof_path)
    table = per_well_table(oof, args.rare_threshold)

    overall_rmse = float(np.sqrt(np.mean((oof["TVT"] - oof["oof_pred"]) ** 2)))
    print(f"overall OOF RMSE (all wells, all rows): {overall_rmse:.4f}")
    print(f"n_wells={len(table)}")
    print(f"\nper-well RMSE: mean={table['rmse_overall'].mean():.2f} "
          f"median={table['rmse_overall'].median():.2f} "
          f"p90={table['rmse_overall'].quantile(0.9):.2f} "
          f"max={table['rmse_overall'].max():.2f}")

    print(f"\ntop {args.top_n} worst wells:")
    print(table.head(args.top_n).to_string(index=False))

    table.to_csv(os.path.join(OUT_DIR, "exp003_per_well_rmse.csv"), index=False)
    print(f"\nsaved: {os.path.join(OUT_DIR, 'exp003_per_well_rmse.csv')}")

    fig_rmse_histogram(table, os.path.join(OUT_DIR, "exp003_rmse_histogram.png"))
    fig_scatter(table, "n_rows", "tail length (n_rows)", os.path.join(OUT_DIR, "exp003_rmse_vs_tail_length.png"))
    fig_scatter(table, "rare_frac", "rare row fraction", os.path.join(OUT_DIR, "exp003_rmse_vs_rare_frac.png"))
    fig_worst_wells(oof, table, os.path.join(OUT_DIR, "exp003_worst_wells.png"))


if __name__ == "__main__":
    main()
