"""LightGBM 残差モデル: target は常に TVT - last_known_TVT（anchor からの残差）。"""
import lightgbm as lgb
import numpy as np
import pandas as pd


class LGBMResidualModel:
    def __init__(self, params: dict, num_boost_round: int, early_stopping_rounds: int):
        self.params = params
        self.num_boost_round = num_boost_round
        self.early_stopping_rounds = early_stopping_rounds
        self.model: lgb.Booster | None = None
        self.feature_names: list[str] | None = None

    def fit(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: pd.DataFrame,
        y_val: pd.Series,
        categorical_feature: list[str] | None = None,
    ) -> None:
        self.feature_names = list(X_train.columns)
        cat_feat = categorical_feature or []
        train_set = lgb.Dataset(X_train, label=y_train, categorical_feature=cat_feat)
        val_set = lgb.Dataset(X_val, label=y_val, categorical_feature=cat_feat, reference=train_set)

        self.model = lgb.train(
            self.params,
            train_set,
            num_boost_round=self.num_boost_round,
            valid_sets=[train_set, val_set],
            valid_names=["train", "val"],
            callbacks=[
                lgb.early_stopping(self.early_stopping_rounds, verbose=False),
                lgb.log_evaluation(period=0),
            ],
        )

    def predict_resid(self, X: pd.DataFrame) -> np.ndarray:
        assert self.model is not None, "fit() を先に呼ぶ必要があります"
        return self.model.predict(X, num_iteration=self.model.best_iteration)

    def predict_tvt(self, X: pd.DataFrame, anchor: pd.Series) -> np.ndarray:
        return anchor.to_numpy() + self.predict_resid(X)

    def save(self, path: str) -> None:
        assert self.model is not None
        self.model.save_model(path)
