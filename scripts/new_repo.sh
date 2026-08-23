#!/usr/bin/env bash
# 新しいコンペ用リポジトリを、このリポジトリの「汎用の仕組み」だけから作る。
#
#   bash scripts/new_repo.sh ~/Documents/code/xxx_kaggle [past-comp-dir ...]
#
# コピーするもの : CLAUDE.md / .claude/ / docs/_templates/ / build_dashboard.py /
#                  Docker まわり / pyproject.toml / conf の骨格 / README / .gitignore
# コピーしないもの: src/ scripts/{train,make_submission,analyze_*,visualize_*} /
#                  kaggle_kernel/ / conf/{data,train} / notebooks/ / data/ / outputs/
#                  （前コンペ固有の実装。参照したくなったら旧リポジトリの git 履歴から引く）
#
# 第2引数以降にコンペ名を渡すと、その docs/{名前}/ を docs/_archive/{名前}/ として
# 知識だけ持っていく（`_` 始まりなのでダッシュボードの自動判定からは除外される）。
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${1:-}"
if [[ -z "$DEST" ]]; then
  echo "usage: bash scripts/new_repo.sh <dest-dir> [past-comp-dir ...]" >&2
  exit 1
fi
shift || true

if [[ -e "$DEST" && -n "$(ls -A "$DEST" 2>/dev/null)" ]]; then
  echo "エラー: $DEST が空ではありません。空のディレクトリを指定してください。" >&2
  exit 1
fi

mkdir -p "$DEST"/{conf/model,conf/data,conf/train,src,scripts,notebooks,docs,outputs,data/raw}

# --- 汎用の仕組み -----------------------------------------------------------
cp "$SRC/CLAUDE.md"                 "$DEST/"
cp "$SRC/README.md"                 "$DEST/"
cp "$SRC/.gitignore"                "$DEST/"
cp "$SRC/.dockerignore"             "$DEST/"
cp "$SRC/Dockerfile"                "$DEST/"
cp "$SRC/Dockerfile.mac"            "$DEST/"
cp "$SRC/docker-compose.yml"        "$DEST/"
cp "$SRC/docker-compose.mac.yml"    "$DEST/"
cp "$SRC/pyproject.toml"            "$DEST/"
cp "$SRC/conf/config.yaml"          "$DEST/conf/"
cp "$SRC/conf/model/lgbm.yaml"      "$DEST/conf/model/"   # 出発点として
cp "$SRC/scripts/build_dashboard.py" "$DEST/scripts/"
cp "$SRC/scripts/new_repo.sh"       "$DEST/scripts/"   # 次のコンペでも使えるように
cp -R "$SRC/.claude"                "$DEST/"
# settings.json から前コンペ固有の permission を落とす
python3 - "$DEST/.claude/settings.json" <<'PY'
import json, sys
p = sys.argv[1]
d = json.load(open(p))
allow = d.get("permissions", {}).get("allow", [])
d["permissions"]["allow"] = [
    a for a in allow if "notebooks/" not in a and "data/raw" not in a
]
json.dump(d, open(p, "w"), indent=2, ensure_ascii=False)
open(p, "a").write("\n")
PY
cp -R "$SRC/docs/_templates"        "$DEST/docs/"

# --- 過去コンペの知識（markdown のみ）---------------------------------------
for comp in "$@"; do
  [[ -d "$SRC/docs/$comp" ]] || { echo "警告: docs/$comp が無いのでスキップ" >&2; continue; }
  mkdir -p "$DEST/docs/_archive/$comp"
  # 転用が効くものだけ。eda/ と experiments/ はコンペ固有なので持っていかない
  for item in postmortems formulations.md gates.md research/top_solutions.md \
              research/past_solutions.md strategy.md experiments.md; do
    if [[ -e "$SRC/docs/$comp/$item" ]]; then
      mkdir -p "$DEST/docs/_archive/$comp/$(dirname "$item")"
      cp -R "$SRC/docs/$comp/$item" "$DEST/docs/_archive/$comp/$(dirname "$item")/"
    fi
  done
done

# --- 前コンペ固有の設定が混ざらないように空にする ---------------------------
cat > "$DEST/src/__init__.py" <<'PY'
PY
touch "$DEST/data/raw/.gitkeep"

echo "作成しました: $DEST"
echo
echo "次にやること:"
echo "  1. cd $DEST && git init && git add -A && git commit -m 'init from template'"
echo "  2. .env を作る（KAGGLE_USERNAME / KAGGLE_KEY / WANDB_API_KEY）"
echo "  3. pyproject.toml の依存を見直す（前コンペ固有のものを外す）→ uv lock"
echo "  4. Claude Code を起動して /kaggle-new <competition-slug>"
