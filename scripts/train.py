"""学習エントリポイント（Hydra）。

GroupKFold(well_id) で OOF を作り、overall / rare / common RMSE を計算して W&B に記録する。
exp001: Anchor + trajectory(X,Y,Z変位, -Z) + GR calibration/rolling/gradient 特徴 + LightGBM 残差モデル。
DTW Target-Free Alignment は実用不可と判明したため exp002 まで保留（src/features.py docstring 参照）。
"""
import os
import sys

import hydra
import numpy as np
import pandas as pd
import wandb
from omegaconf import DictConfig, OmegaConf
from sklearn.model_selection import GroupKFold

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.dataset import list_well_ids, load_well, load_typewell
from src.features import build_feature_frame
from src.model import LGBMResidualModel

NON_FEATURE_COLS = ["well_id", "row_index", "is_tail", "TVT", "resid", "tvt_diff_abs"]


def build_all_features(train_dir: str, gr_rolling_windows: list[int]) -> pd.DataFrame:
    well_ids = list_well_ids(train_dir)
    frames = []
    for well_id in well_ids:
        hw = load_well(well_id, train_dir)
        tw = load_typewell(well_id, train_dir)
        feat = build_feature_frame(hw, tw, gr_rolling_windows)
        feat["tvt_diff_abs"] = hw["TVT"].diff().abs().to_numpy()
        frames.append(feat)
    return pd.concat(frames, ignore_index=True)


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


@hydra.main(version_base=None, config_path="../conf", config_name="config")
def main(cfg: DictConfig) -> None:
    print(OmegaConf.to_yaml(cfg))

    wandb.init(
        project=cfg.wandb.project,
        name=cfg.wandb.run_name,
        config=OmegaConf.to_container(cfg, resolve=True),
    )

    df = build_all_features(cfg.data.train_dir, cfg.train.gr_rolling_windows)

    feature_cols = [c for c in df.columns if c not in NON_FEATURE_COLS]

    tail_df = df[df["is_tail"]].reset_index(drop=True)

    gkf = GroupKFold(n_splits=cfg.data.n_folds)
    oof_pred = np.full(len(tail_df), np.nan)

    model_params = OmegaConf.to_container(cfg.model.params, resolve=True)

    for fold, (train_idx, val_idx) in enumerate(gkf.split(tail_df, groups=tail_df["well_id"])):
        train_fold = tail_df.iloc[train_idx]
        val_fold = tail_df.iloc[val_idx]

        model = LGBMResidualModel(
            params=model_params,
            num_boost_round=cfg.model.num_boost_round,
            early_stopping_rounds=cfg.model.early_stopping_rounds,
        )
        model.fit(
            train_fold[feature_cols], train_fold["resid"],
            val_fold[feature_cols], val_fold["resid"],
        )

        val_pred_tvt = model.predict_tvt(val_fold[feature_cols], val_fold["last_known_TVT"])
        oof_pred[val_idx] = val_pred_tvt

        train_pred_resid = model.predict_resid(train_fold[feature_cols])
        fold_train_loss = rmse(train_fold["resid"].to_numpy(), train_pred_resid)
        fold_val_loss = rmse(val_fold["TVT"].to_numpy(), val_pred_tvt)

        os.makedirs("outputs/models", exist_ok=True)
        model.save(f"outputs/models/fold{fold}.txt")

        wandb.log({"train_loss": fold_train_loss, "val_loss": fold_val_loss}, step=fold)
        print(f"[fold {fold}] train_resid_rmse={fold_train_loss:.4f} val_tvt_rmse={fold_val_loss:.4f}")

    tail_df["oof_pred"] = oof_pred
    rare_mask = tail_df["tvt_diff_abs"] > cfg.train.rare_threshold

    val_score = rmse(tail_df["TVT"].to_numpy(), tail_df["oof_pred"].to_numpy())
    val_score_rare = rmse(tail_df.loc[rare_mask, "TVT"].to_numpy(), tail_df.loc[rare_mask, "oof_pred"].to_numpy())
    val_score_common = rmse(tail_df.loc[~rare_mask, "TVT"].to_numpy(), tail_df.loc[~rare_mask, "oof_pred"].to_numpy())

    print(f"OOF RMSE overall={val_score:.4f} rare={val_score_rare:.4f} common={val_score_common:.4f}")
    wandb.log({
        "val_score": val_score,
        "val_score_rare": val_score_rare,
        "val_score_common": val_score_common,
    })

    os.makedirs("outputs", exist_ok=True)
    tail_df[["well_id", "row_index", "TVT", "oof_pred", "tvt_diff_abs"]].to_parquet("outputs/oof.parquet")

    artifact = wandb.Artifact("oof", type="oof")
    artifact.add_file("outputs/oof.parquet")
    wandb.log_artifact(artifact)

    wandb.finish()


if __name__ == "__main__":
    main()
