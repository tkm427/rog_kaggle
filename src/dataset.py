"""データロード: horizontal_well.csv + typewell.csv の読み込みと prefix/tail 境界の付与。

リーク管理（docs/rogii2026/competition_overview.md 参照）:
- train のみに存在する地層サーフェス列（ANCC等）はここでは読み込むが、
  features.py 側で直接特徴量として使わないことを徹底する。
- prefix/tail の境界は TVT_input の非欠損→欠損の単一遷移点（data_structure.md で確認済み）。
"""
import glob
import os

import pandas as pd

TRAIN_FORMATION_COLS = ["ANCC", "ASTNU", "ASTNL", "EGFDU", "EGFDL", "BUDA"]


def list_well_ids(split_dir: str) -> list[str]:
    hw_files = sorted(glob.glob(os.path.join(split_dir, "*__horizontal_well.csv")))
    return [os.path.basename(f).replace("__horizontal_well.csv", "") for f in hw_files]


def load_well(well_id: str, split_dir: str) -> pd.DataFrame:
    hw_path = os.path.join(split_dir, f"{well_id}__horizontal_well.csv")
    df = pd.read_csv(hw_path)
    df = df.sort_values("MD").reset_index(drop=True)
    df["well_id"] = well_id
    df["row_index"] = df.index
    return attach_prefix_tail(df)


def load_typewell(well_id: str, split_dir: str) -> pd.DataFrame:
    tw_path = os.path.join(split_dir, f"{well_id}__typewell.csv")
    tw = pd.read_csv(tw_path).sort_values("TVT").reset_index(drop=True)
    return tw


def attach_prefix_tail(df: pd.DataFrame) -> pd.DataFrame:
    """TVT_input の非欠損→欠損の遷移点を見つけ、is_tail / last_known_TVT を付与する。"""
    known = df["TVT_input"].notna()
    transitions = known.astype(int).diff().fillna(0)
    n_breaks = (transitions == -1).sum()
    assert n_breaks <= 1, (
        f"prefix->tail の遷移が複数回検出された (well の構造が想定と異なる, n_breaks={n_breaks})"
    )

    df = df.copy()
    df["is_tail"] = ~known
    if known.any():
        anchor_row = df.loc[known].iloc[-1]
    else:
        anchor_row = df.iloc[0]
    df["last_known_TVT"] = anchor_row["TVT_input"] if known.any() else float("nan")
    df["delta_MD"] = df["MD"] - anchor_row["MD"]
    # prediction start からの軌跡変位（trajectory displacement）。-Z は TVT の近似値として有効
    # (tvt_regime.md: Corr(TVT, -Z) = 0.917)。
    df["delta_X"] = df["X"] - anchor_row["X"]
    df["delta_Y"] = df["Y"] - anchor_row["Y"]
    df["delta_Z"] = df["Z"] - anchor_row["Z"]
    df["neg_Z"] = -df["Z"]
    return df
