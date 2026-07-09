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


def _smooth_gr_for_beam(values: np.ndarray, fallback: float, radius: int) -> np.ndarray:
    series = pd.Series(values, dtype="float64").interpolate(limit_direction="both").fillna(fallback)
    if radius <= 0:
        return series.to_numpy(dtype=float)
    return series.rolling(radius * 2 + 1, center=True, min_periods=1).mean().to_numpy(dtype=float)


def _nearest_sorted_index(sorted_values: np.ndarray, target: float) -> int:
    if len(sorted_values) == 0:
        return 0
    idx = int(np.searchsorted(sorted_values, target, side="left"))
    if idx >= len(sorted_values):
        return len(sorted_values) - 1
    if idx > 0 and abs(sorted_values[idx - 1] - target) <= abs(sorted_values[idx] - target):
        return idx - 1
    return idx


def beam_typewell_path(
    gr_values: np.ndarray,
    tw_tvt: np.ndarray,
    tw_gr: np.ndarray,
    start_tvt: float,
    beam_size: int = 10,
    move_cost: float = 20.0,
    emit_scale: float = 144.0,
    radius: int = 2,
) -> tuple[np.ndarray, np.ndarray]:
    """anchor制約付き beam search（ビタビ風DP）で hw の GR 系列を typewell に整列する。

    pilkwang Notebook（research/rogii-eda-target-free-alignment-for-tvt.ipynb, cell 69）の
    `beam_typewell_path` を移植。素朴な全系列DTW（exp001、anchor制約・局所遷移なし）が
    prefix RMSE 50〜260ft で破綻したのに対し、(1) start_tvt 近傍から探索を開始する anchor制約、
    (2) 1ステップあたり typewell index を ±1 までしか動かさない局所遷移、
    (3) コスト上位 beam_size 個のみ残す枝刈り、の3点で探索の暴走を防ぐ。

    Returns:
        matched_tvt: 各 hw 行に対応する typewell TVT（anchor近傍からの整列結果）
        matched_gr: 整列先の typewell GR 値（残差特徴用）
    """
    tw_tvt = np.asarray(tw_tvt, dtype=float)
    tw_gr = np.asarray(tw_gr, dtype=float)
    valid_tw = np.isfinite(tw_tvt) & np.isfinite(tw_gr)
    tw_tvt = tw_tvt[valid_tw]
    tw_gr = tw_gr[valid_tw]
    order = np.argsort(tw_tvt)
    tw_tvt = tw_tvt[order]
    tw_gr = tw_gr[order]

    n = len(gr_values)
    if n == 0 or len(tw_tvt) < 2 or not np.isfinite(start_tvt):
        return np.full(n, np.nan), np.full(n, np.nan)

    fallback = float(np.nanmean(tw_gr)) if np.isfinite(np.nanmean(tw_gr)) else 0.0
    smoothed_gr = _smooth_gr_for_beam(np.asarray(gr_values, dtype=float), fallback=fallback, radius=radius)
    start_idx = _nearest_sorted_index(tw_tvt, start_tvt)
    states = {start_idx: 0.0}
    backpointers: list[dict[int, int]] = []

    for gr_value in smoothed_gr:
        if not np.isfinite(gr_value):
            gr_value = fallback
        candidates: dict[int, float] = {}
        parents: dict[int, int] = {}
        for idx, cost in states.items():
            for delta in (-1, 0, 1):
                next_idx = idx + delta
                if next_idx < 0 or next_idx >= len(tw_tvt):
                    continue
                emit_cost = ((gr_value - tw_gr[next_idx]) ** 2) / max(emit_scale, 1e-6)
                total_cost = cost + emit_cost + move_cost * abs(delta)
                if next_idx not in candidates or total_cost < candidates[next_idx]:
                    candidates[next_idx] = float(total_cost)
                    parents[next_idx] = idx
        kept = sorted(candidates.items(), key=lambda item: item[1])[:beam_size]
        if not kept:
            return np.full(n, np.nan), np.full(n, np.nan)
        states = {idx: cost for idx, cost in kept}
        backpointers.append({idx: parents[idx] for idx, _ in kept})

    final_idx = min(states, key=states.get)
    path = [final_idx]
    for step in range(len(backpointers) - 1, 0, -1):
        path.append(backpointers[step][path[-1]])
    path.reverse()
    path_arr = np.asarray(path, dtype=int)
    return tw_tvt[path_arr], tw_gr[path_arr]


# tight/conservative/loose の3設定で探索の厳しさを変え、合意度を confidence 特徴として使う。
# conservative はpilkwangのデフォルト値そのもの。tight は move_cost/emit_scale を下げてGRに
# 追従しやすくし、loose は逆に上げて anchor 近傍に留まりやすくする。
_BEAM_PRESETS = {
    "tight": {"beam_size": 10, "move_cost": 10.0, "emit_scale": 80.0, "radius": 2},
    "cons": {"beam_size": 10, "move_cost": 20.0, "emit_scale": 144.0, "radius": 2},
    "loose": {"beam_size": 10, "move_cost": 40.0, "emit_scale": 250.0, "radius": 2},
}


def beam_alignment_features(hw: pd.DataFrame, tw: pd.DataFrame, gr_cal: pd.Series) -> pd.DataFrame:
    """tail 行に対し anchor制約付き beam search を3設定で実行し、整列特徴を返す（exp002）。

    Offline policy: hw の GR は未来 covariate を含む全シーケンスを使ってよいが、
    typewell 側の TVT/GR のみを参照し tail の TVT は読まない。
    """
    tail_mask = hw["is_tail"].to_numpy()
    n = len(hw)
    cols = [
        "beam_tight_delta", "beam_cons_delta", "beam_loose_delta",
        "beam_spread", "beam_step", "gr_minus_beam_cons", "gr_minus_beam_loose",
    ]
    if tail_mask.sum() == 0:
        return pd.DataFrame({c: np.full(n, np.nan) for c in cols}, index=hw.index)

    anchor = float(hw["last_known_TVT"].iloc[0])
    gr_tail = gr_cal.to_numpy()[tail_mask]
    tw_tvt = tw["TVT"].to_numpy()
    tw_gr = tw["GR"].to_numpy()

    paths = {}
    for name, params in _BEAM_PRESETS.items():
        matched_tvt, matched_gr = beam_typewell_path(gr_tail, tw_tvt, tw_gr, anchor, **params)
        paths[name] = (matched_tvt, matched_gr)

    tight_tvt, _ = paths["tight"]
    cons_tvt, cons_gr = paths["cons"]
    loose_tvt, loose_gr = paths["loose"]

    stacked = np.vstack([tight_tvt, cons_tvt, loose_tvt])
    spread = np.nanmax(stacked, axis=0) - np.nanmin(stacked, axis=0)
    step = np.diff(cons_tvt, prepend=cons_tvt[0] if len(cons_tvt) else np.nan)

    tail_feat = pd.DataFrame({
        "beam_tight_delta": tight_tvt - anchor,
        "beam_cons_delta": cons_tvt - anchor,
        "beam_loose_delta": loose_tvt - anchor,
        "beam_spread": spread,
        "beam_step": step,
        "gr_minus_beam_cons": gr_tail - cons_gr,
        "gr_minus_beam_loose": gr_tail - loose_gr,
    }, index=hw.index[tail_mask])

    return tail_feat.reindex(hw.index)


def beam_alignment_quality(hw: pd.DataFrame, tw: pd.DataFrame, gr_cal: pd.Series, holdout_frac: float = 0.3) -> float:
    """prefix 区間の後半 holdout_frac を「仮の tail」として切り出し、本番と同じ向き
    （カットオフ位置を anchor として手前から GR 順方向に beam search）で整列した結果と
    既知 TVT_input との RMSE を測る sanity check。

    flat anchor（12.8ft）を下回らない限り build_feature_frame に統合しない（exp002必須ゲート）。
    """
    prefix_mask = ~hw["is_tail"].to_numpy()
    prefix_idx = np.where(prefix_mask)[0]
    if len(prefix_idx) < 10:
        return float("nan")

    cutoff = int(len(prefix_idx) * (1 - holdout_frac))
    cutoff = max(cutoff, 1)
    anchor_pos = prefix_idx[cutoff - 1]
    holdout_pos = prefix_idx[cutoff:]
    if len(holdout_pos) < 2:
        return float("nan")

    anchor = float(hw["TVT_input"].iloc[anchor_pos])
    gr_holdout = gr_cal.to_numpy()[holdout_pos]
    tw_tvt = tw["TVT"].to_numpy()
    tw_gr = tw["GR"].to_numpy()

    matched_tvt, _ = beam_typewell_path(gr_holdout, tw_tvt, tw_gr, anchor, **_BEAM_PRESETS["cons"])
    true_tvt = hw["TVT_input"].to_numpy()[holdout_pos]
    err = matched_tvt - true_tvt
    valid = np.isfinite(err)
    return float(np.sqrt(np.mean(err[valid] ** 2))) if valid.any() else float("nan")


def trajectory_gr_disagreement_features(
    hw: pd.DataFrame,
    tw: pd.DataFrame,
    gr_cal: pd.Series,
    windows: list[int],
    groups: list[int] | None = None,
) -> pd.DataFrame:
    """H10: trajectory(-Z)とGRベース整列の不一致度を特徴量化（exp004）。

    exp003でLightGBMがtrajectory系を94%使用しGRをほぼ無視と判明。
    worst 10ウェルの4/10でtraj(-Z)とTVTのネット変位符号が逆転 → このシグナルを特徴量化。

    Group 1 (4特徴): prefix内でのneg_Z/GRとTVTの相関 → ウェルレベルでbroadcast
    Group 2 (3特徴): rolling窓でのGRとneg_Z勾配の相関 → 行レベル
    Group 3 (2特徴): typewell GR最近傍マッチングTVT → 行レベル（trajectory非依存推定値）

    リーク管理: Group 1はprefix TVT_input（既知値）のみ使用。Group 2はTVT未使用。
    Group 3はtypewell TVT/GR（参照ウェル）のみ使用。
    """
    n = len(hw)
    active = set(groups) if groups is not None else {1, 2, 3}

    out: dict[str, np.ndarray] = {}

    # --- Group 1: prefix-level correlations ---
    if 1 in active:
        prefix_mask = ~hw["is_tail"]
        prefix_negz = hw.loc[prefix_mask, "neg_Z"]
        prefix_gr = gr_cal[prefix_mask]
        prefix_tvt = hw.loc[prefix_mask, "TVT_input"]

        if prefix_mask.sum() >= 5:
            corr_negz_tvt = float(prefix_negz.corr(prefix_tvt))
            corr_gr_tvt = float(prefix_gr.corr(prefix_tvt))
            tvt_diff = prefix_tvt.diff().dropna()
            valid_idx = tvt_diff.index
            negz_diff = prefix_negz.diff()[valid_idx]
            gr_diff_p = prefix_gr.diff()[valid_idx]
            corr_negz_tvt_diff = float(negz_diff.corr(tvt_diff)) if len(tvt_diff) >= 3 else 0.0
            corr_gr_tvt_diff = float(gr_diff_p.corr(tvt_diff)) if len(tvt_diff) >= 3 else 0.0
        else:
            corr_negz_tvt = corr_gr_tvt = corr_negz_tvt_diff = corr_gr_tvt_diff = 0.0

        out["prefix_corr_negz_tvt"] = np.full(n, corr_negz_tvt if np.isfinite(corr_negz_tvt) else 0.0)
        out["prefix_corr_gr_tvt"] = np.full(n, corr_gr_tvt if np.isfinite(corr_gr_tvt) else 0.0)
        out["prefix_corr_negz_tvt_diff"] = np.full(n, corr_negz_tvt_diff if np.isfinite(corr_negz_tvt_diff) else 0.0)
        out["prefix_corr_gr_tvt_diff"] = np.full(n, corr_gr_tvt_diff if np.isfinite(corr_gr_tvt_diff) else 0.0)

    # --- Group 2: rolling GR vs neg_Z gradient correlation ---
    if 2 in active:
        gr_diff_all = gr_cal.diff().fillna(0.0)
        negz_diff_all = hw["neg_Z"].diff().fillna(0.0)
        for w in windows:
            roll_corr = gr_diff_all.rolling(w, min_periods=max(w // 3, 5)).corr(negz_diff_all).fillna(0.0)
            out[f"gr_negz_roll_corr_{w}"] = roll_corr.to_numpy()

    # --- Group 3: typewell GR nearest-neighbor TVT ---
    if 3 in active:
        tw_gr_raw = tw["GR"].to_numpy()
        tw_tvt_raw = tw["TVT"].to_numpy()
        valid = np.isfinite(tw_gr_raw) & np.isfinite(tw_tvt_raw)
        tw_gr_v = tw_gr_raw[valid]
        tw_tvt_v = tw_tvt_raw[valid]
        gr_arr = gr_cal.fillna(gr_cal.mean()).to_numpy()

        if len(tw_gr_v) >= 2:
            sorted_idx = np.argsort(tw_gr_v)
            tw_gr_s = tw_gr_v[sorted_idx]
            tw_tvt_s = tw_tvt_v[sorted_idx]

            pos = np.searchsorted(tw_gr_s, gr_arr).clip(0, len(tw_gr_s) - 1)
            pos_m1 = np.maximum(pos - 1, 0)
            dist_pos = np.abs(tw_gr_s[pos] - gr_arr)
            dist_m1 = np.abs(tw_gr_s[pos_m1] - gr_arr)
            best = np.where(dist_pos <= dist_m1, pos, pos_m1)

            gr_nn_tvt = tw_tvt_s[best]
            gr_nn_cost = np.where(dist_pos <= dist_m1, dist_pos, dist_m1)
        else:
            gr_nn_tvt = np.full(n, np.nan)
            gr_nn_cost = np.full(n, np.nan)

        out["gr_nn_tvt_delta"] = gr_nn_tvt - hw["last_known_TVT"].to_numpy()
        out["gr_nn_cost"] = gr_nn_cost

    return pd.DataFrame(out, index=hw.index)


def build_feature_frame(
    hw: pd.DataFrame,
    tw: pd.DataFrame,
    gr_rolling_windows: list[int],
    enable_beam_features: bool = False,
    enable_disagreement_features: bool = False,
    disagreement_groups: list[int] | None = None,
) -> pd.DataFrame:
    """1 well 分の行レベル特徴量フレームを構築する。train の場合は resid（学習ターゲット）も付与する。

    v1 は anchor + trajectory（X,Y,Z 変位, -Z）+ GR calibration/rolling/gradient 特徴。
    `enable_beam_features=True` で exp002 の anchor制約付き beam search 整列特徴を追加する
    （`beam_alignment_quality` のprefix-holdout sanity checkでflat anchorを下回ることを確認済み）。
    `enable_disagreement_features=True` で exp004 の trajectory-GR不一致度特徴を追加する。
    `disagreement_groups` で有効化するグループ（1/2/3）を絞り込める（Noneは全グループ）。
    素朴な全系列DTW（dtw_align）は exp001 で実用不可と判明したため未使用のまま保持。
    """
    gr_cal = calibrate_gr(hw, tw)
    rolling_feat = rolling_gr_features(hw, gr_cal, gr_rolling_windows)

    parts = [hw[["well_id", "row_index", "MD", "X", "Y", "Z", "delta_MD",
                "delta_X", "delta_Y", "delta_Z", "neg_Z",
                "is_tail", "last_known_TVT"]], rolling_feat]
    if enable_beam_features:
        parts.append(beam_alignment_features(hw, tw, gr_cal))
    if enable_disagreement_features:
        parts.append(trajectory_gr_disagreement_features(hw, tw, gr_cal, gr_rolling_windows, groups=disagreement_groups))

    feat = pd.concat(parts, axis=1)

    if "TVT" in hw.columns:
        feat["TVT"] = hw["TVT"]
        feat["resid"] = feat["TVT"] - feat["last_known_TVT"]

    return feat
