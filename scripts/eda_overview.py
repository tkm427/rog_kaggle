"""
EDA Overview: データ全体の俯瞰
- ウェル数・行数・カラム確認
- TVT/TVT_input の欠損パターン（prefix/tail 境界）
- GR 分布（水平 vs タイプウェル）
- TVT 変化率分布（稀少レジームの閾値候補）
- 座標 (X, Y) の空間分布
"""
import os
import glob
import json
import numpy as np
import pandas as pd

TRAIN_DIR = "/workspace/data/raw/train"
TEST_DIR = "/workspace/data/raw/test"

# ──────────────────────────────────────────
# 1. ウェル一覧取得
# ──────────────────────────────────────────
train_hw_files = sorted(glob.glob(f"{TRAIN_DIR}/*__horizontal_well.csv"))
test_hw_files = sorted(glob.glob(f"{TEST_DIR}/*__horizontal_well.csv"))

train_well_ids = [os.path.basename(f).replace("__horizontal_well.csv", "") for f in train_hw_files]
test_well_ids = [os.path.basename(f).replace("__horizontal_well.csv", "") for f in test_hw_files]

print(f"Train wells: {len(train_well_ids)}")
print(f"Test wells: {len(test_well_ids)}")
print(f"Test well IDs: {test_well_ids}")
print()

# ──────────────────────────────────────────
# 2. カラム確認（1本で代表）
# ──────────────────────────────────────────
sample_hw = pd.read_csv(train_hw_files[0])
sample_tw = pd.read_csv(f"{TRAIN_DIR}/{train_well_ids[0]}__typewell.csv")

print("=== horizontal_well columns ===")
print(sample_hw.dtypes.to_string())
print()
print("=== typewell columns ===")
print(sample_tw.dtypes.to_string())
print()

# ──────────────────────────────────────────
# 3. 全 train ウェルを読んで集計
# ──────────────────────────────────────────
stats = []
all_tvt_diff = []

print("Loading all train wells (may take a moment)...")
for well_id, fpath in zip(train_well_ids, train_hw_files):
    df = pd.read_csv(fpath)
    df["well_id"] = well_id

    n_total = len(df)
    n_prefix = df["TVT_input"].notna().sum()
    n_tail = df["TVT_input"].isna().sum()
    n_tvt_known = df["TVT"].notna().sum()

    # TVT 変化率（tail のラベルがある行のみ）
    tail_df = df[df["TVT"].notna()].copy()
    if len(tail_df) > 1:
        diffs = tail_df["TVT"].diff().abs().dropna()
        all_tvt_diff.append(diffs)

    stats.append({
        "well_id": well_id,
        "n_total": n_total,
        "n_prefix": n_prefix,
        "n_tail": n_tail,
        "tail_ratio": n_tail / n_total if n_total > 0 else 0,
        "tvt_min": df["TVT"].min(),
        "tvt_max": df["TVT"].max(),
        "gr_mean": df["GR"].mean(),
        "gr_std": df["GR"].std(),
        "x_mean": df["X"].mean(),
        "y_mean": df["Y"].mean(),
    })

stats_df = pd.DataFrame(stats)

print("=== Row counts ===")
print(f"Total train rows: {stats_df['n_total'].sum():,}")
print(f"Total prefix (known TVT_input) rows: {stats_df['n_prefix'].sum():,}")
print(f"Total tail (hidden TVT_input) rows: {stats_df['n_tail'].sum():,}")
print(f"Tail ratio mean: {stats_df['tail_ratio'].mean():.3f} ± {stats_df['tail_ratio'].std():.3f}")
print()

print("=== Well length distribution ===")
print(stats_df["n_total"].describe().round(1).to_string())
print()

print("=== TVT range ===")
print(f"Global min TVT: {stats_df['tvt_min'].min():.1f}")
print(f"Global max TVT: {stats_df['tvt_max'].max():.1f}")
print()

print("=== GR stats ===")
print(f"GR mean across wells: {stats_df['gr_mean'].mean():.1f}")
print(f"GR std across wells: {stats_df['gr_std'].mean():.1f}")
print()

# ──────────────────────────────────────────
# 4. TVT 変化率 → 稀少レジーム閾値候補
# ──────────────────────────────────────────
all_diffs = pd.concat(all_tvt_diff)
print("=== TVT absolute diff per row (ft) ===")
print(all_diffs.describe(percentiles=[0.5, 0.75, 0.9, 0.95, 0.99]).round(4).to_string())
p95 = all_diffs.quantile(0.95)
p99 = all_diffs.quantile(0.99)
print(f"\n95th percentile: {p95:.4f} ft")
print(f"99th percentile: {p99:.4f} ft")
print(f"Rows above p95: {(all_diffs > p95).sum():,} ({(all_diffs > p95).mean()*100:.2f}%)")
print(f"Rows above p99: {(all_diffs > p99).sum():,} ({(all_diffs > p99).mean()*100:.2f}%)")
print()

# ──────────────────────────────────────────
# 6. typewell 確認（1本詳細）
# ──────────────────────────────────────────
print("=== typewell sample (first well) ===")
print(sample_tw.head(3).to_string())
print(f"typewell rows: {len(sample_tw)}")
print(f"typewell TVT range: {sample_tw['TVT'].min():.1f} - {sample_tw['TVT'].max():.1f}")
print()

# ──────────────────────────────────────────
# 7. Prefix / Tail の境界パターン確認
# ──────────────────────────────────────────
print("=== Prefix/Tail boundary pattern (first well) ===")
hw = sample_hw.copy()
hw["is_prefix"] = hw["TVT_input"].notna()
transitions = (hw["is_prefix"] != hw["is_prefix"].shift()).sum()
print(f"Number of prefix<->tail transitions: {transitions}")
last_prefix_idx = hw[hw["is_prefix"]].index[-1] if hw["is_prefix"].any() else None
first_tail_idx = hw[~hw["is_prefix"]].index[0] if (~hw["is_prefix"]).any() else None
print(f"Last prefix row idx: {last_prefix_idx}")
print(f"First tail row idx: {first_tail_idx}")
if last_prefix_idx is not None:
    print(f"Last prefix TVT_input: {hw.loc[last_prefix_idx, 'TVT_input']:.2f}")
print()

# ──────────────────────────────────────────
# 8. TVT_input == TVT チェック（prefix）
# ──────────────────────────────────────────
prefix_df = hw[hw["is_prefix"]].copy()
match = (prefix_df["TVT_input"] == prefix_df["TVT"]).mean()
print(f"=== TVT_input == TVT in prefix? ===")
print(f"Match ratio: {match:.4f} (should be ~1.0)")
print()

print("Done.")
