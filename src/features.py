"""特徴量エンジニアリング: GR calibration, rolling統計。

リーク管理（docs/rogii2026/competition_overview.md / research/public_notebooks.md pilkwang Section 0,5,11 参照）:
- GR affine calibration は prefix 行のみでフィットする。
- train-only な地層サーフェス列（ANCC等）は使わない。

note: dtw_align / dtw_alignment_quality は exp001 で「素朴な全系列GR DTW」を検証した結果、
prefix 区間の再現RMSEが 50〜260ft（flat anchor の 12.8ft より悪化）かつ 1well=最大239秒
（773well で約51時間）で実用不可と判明したため build_feature_frame からは外している。
pilkwang Notebook の PF/beam search・anchor制約等のガードレールを踏まえて再設計する
exp002 まで一時的に保留（関数自体はそのまま残す）。
"""
import numpy as np
import pandas as pd
from fastdtw import fastdtw
from scipy.spatial.distance import euclidean


def calibrate_gr(hw: pd.DataFrame, tw: pd.DataFrame) -> pd.Series:
    """affine GR calibration（gr_calibration.md の式）。prefix 行のみでフィット。

    hw_GR_cal = hw_GR + (tw_GR_mean(prefix TVT range) - hw_GR_mean(prefix))
    """
    prefix_mask = ~hw["is_tail"]
    hw_gr_filled = hw["GR"].interpolate(limit_direction="both")

    prefix_tvt_range = hw.loc[prefix_mask, "TVT_input"]
    if prefix_mask.sum() == 0 or prefix_tvt_range.isna().all():
        return hw_gr_filled

    tvt_lo, tvt_hi = prefix_tvt_range.min(), prefix_tvt_range.max()
    tw_in_range = tw[(tw["TVT"] >= tvt_lo) & (tw["TVT"] <= tvt_hi)]
    if len(tw_in_range) == 0:
        return hw_gr_filled

    hw_prefix_mean = hw_gr_filled[prefix_mask].mean()
    tw_mean = tw_in_range["GR"].mean()
    shift = tw_mean - hw_prefix_mean
    return hw_gr_filled + shift


def rolling_gr_features(hw: pd.DataFrame, gr_cal: pd.Series, windows: list[int]) -> pd.DataFrame:
    """trailing rolling mean/std + 1次差分（gradient）。FORCE2020/SEG2016 由来の核特徴量。"""
    out = {}
    grad = gr_cal.diff().fillna(0.0)
    out["gr_cal"] = gr_cal
    out["gr_gradient"] = grad
    for w in windows:
        out[f"gr_roll_mean_{w}"] = gr_cal.rolling(w, min_periods=1).mean()
        out[f"gr_roll_std_{w}"] = gr_cal.rolling(w, min_periods=1).std().fillna(0.0)
    return pd.DataFrame(out, index=hw.index)


def dtw_align(hw: pd.DataFrame, tw: pd.DataFrame, gr_cal: pd.Series, radius: int = 200) -> pd.DataFrame:
    """hw の calibrated GR 系列と typewell の GR 系列を DTW で整列し、
    各行に対する typewell マッチ（matched_tvt, dtw_cost, matched_geology）を返す。

    Offline policy: hw の GR は未来 covariate を含む全シーケンスを使ってよい。
    tail の TVT は参照していない（typewell 側の TVT/GR/Geology のみ使用）。
    """
    hw_seq = gr_cal.to_numpy()
    tw_seq = tw["GR"].to_numpy()

    if len(hw_seq) == 0 or len(tw_seq) == 0 or np.all(np.isnan(hw_seq)):
        n = len(hw)
        return pd.DataFrame(
            {
                "dtw_matched_tvt": np.full(n, np.nan),
                "dtw_cost": np.full(n, np.nan),
                "matched_geology": pd.Series([None] * n, dtype="object"),
            },
            index=hw.index,
        )

    _, path = fastdtw(hw_seq.reshape(-1, 1), tw_seq.reshape(-1, 1), radius=radius, dist=euclidean)

    n = len(hw_seq)
    matched_tvt = np.full(n, np.nan)
    dtw_cost = np.full(n, np.nan)
    matched_geology = np.full(n, None, dtype=object)

    # path は (hw_idx, tw_idx) のペアのリスト。同じ hw_idx に複数マッチがある場合は平均を取る。
    matches: dict[int, list[int]] = {}
    for i, j in path:
        matches.setdefault(i, []).append(j)

    tw_tvt = tw["TVT"].to_numpy()
    tw_gr = tw["GR"].to_numpy()
    tw_geology = tw["Geology"].to_numpy() if "Geology" in tw.columns else None

    for i, js in matches.items():
        js_arr = np.array(js)
        matched_tvt[i] = tw_tvt[js_arr].mean()
        dtw_cost[i] = np.abs(hw_seq[i] - tw_gr[js_arr]).mean()
        if tw_geology is not None:
            matched_geology[i] = tw_geology[js_arr[0]]

    return pd.DataFrame(
        {
            "dtw_matched_tvt": matched_tvt,
            "dtw_cost": dtw_cost,
            "matched_geology": pd.Series(matched_geology, dtype="object"),
        },
        index=hw.index,
    )


def dtw_alignment_quality(hw: pd.DataFrame, dtw_feat: pd.DataFrame) -> float:
    """prefix 区間で dtw_matched_tvt と既知の TVT_input の誤差を測る sanity check（eda/dtw_alignment_quality.md 用）。"""
    prefix_mask = ~hw["is_tail"]
    err = dtw_feat.loc[prefix_mask, "dtw_matched_tvt"] - hw.loc[prefix_mask, "TVT_input"]
    return float(np.sqrt((err**2).mean())) if prefix_mask.any() else float("nan")


def build_feature_frame(hw: pd.DataFrame, tw: pd.DataFrame, gr_rolling_windows: list[int]) -> pd.DataFrame:
    """1 well 分の行レベル特徴量フレームを構築する。train の場合は resid（学習ターゲット）も付与する。

    DTW は exp002 まで保留（モジュール docstring 参照）。v1 は anchor + trajectory（X,Y,Z 変位, -Z）
    + GR calibration/rolling/gradient 特徴のみ。
    """
    gr_cal = calibrate_gr(hw, tw)
    rolling_feat = rolling_gr_features(hw, gr_cal, gr_rolling_windows)

    feat = pd.concat([hw[["well_id", "row_index", "MD", "X", "Y", "Z", "delta_MD",
                          "delta_X", "delta_Y", "delta_Z", "neg_Z",
                          "is_tail", "last_known_TVT"]], rolling_feat], axis=1)

    if "TVT" in hw.columns:
        feat["TVT"] = hw["TVT"]
        feat["resid"] = feat["TVT"] - feat["last_known_TVT"]

    return feat
