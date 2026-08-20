#!/usr/bin/env python3
"""コンペの状況を 1 枚の HTML ダッシュボードに集約する。

目的: md ファイルは「Claude と git のための正本」に徹し、人間が判断するための
情報はこの 1 画面に集約する。`docs/{competition}/*.md` をパースし、
**ゲート宣言（gates.md のチェック）と機械計測の食い違い**を検出して出力する。

    uv run python scripts/build_dashboard.py            # 自動検出して生成
    uv run python scripts/build_dashboard.py --open     # 生成してブラウザで開く
    uv run python scripts/build_dashboard.py -c rogii2026 -o outputs/dash.html

標準ライブラリのみ。パースできない箇所はクラッシュせず「未パース」として表示する
（ダッシュボードが黙って嘘をつかないことを優先する）。
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# CLAUDE.md 第3節のゲート定義（ID -> フェーズ）
PHASES: list[tuple[str, str, list[str]]] = [
    ("Phase 1", "リサーチ", ["R1", "R2", "R3", "R4", "R5", "R6"]),
    ("Phase 2", "E2E 提出", ["S1", "S2", "S3"]),
    ("Phase 3", "二系統並走", ["T1"]),
    ("Phase 4", "終盤", ["F1", "F2", "F3"]),
]


# --------------------------------------------------------------------------
# markdown パース
# --------------------------------------------------------------------------
def read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def split_sections(text: str) -> dict[str, str]:
    """`## 見出し` で本文を分割する。見出し名 -> 本文。"""
    out: dict[str, str] = {}
    current = ""
    buf: list[str] = []
    for line in text.splitlines():
        m = re.match(r"^##\s+(.*)$", line)
        if m:
            if current:
                out[current] = "\n".join(buf)
            current = m.group(1).strip()
            buf = []
        else:
            buf.append(line)
    if current:
        out[current] = "\n".join(buf)
    return out


def find_section(sections: dict[str, str], *keywords: str) -> str | None:
    for name, body in sections.items():
        if any(k in name for k in keywords):
            return body
    return None


def parse_table(block: str | None) -> list[dict[str, str]]:
    """最初の markdown 表を行の辞書リストにする。見つからなければ空リスト。"""
    if not block:
        return []
    lines = [ln.strip() for ln in block.splitlines()]
    header: list[str] | None = None
    rows: list[dict[str, str]] = []
    for i, ln in enumerate(lines):
        if not ln.startswith("|"):
            if header:
                break
            continue
        cells = [c.strip() for c in ln.strip("|").split("|")]
        if header is None:
            # 次行が区切り行なら見出しとみなす
            nxt = lines[i + 1] if i + 1 < len(lines) else ""
            if re.match(r"^\|[\s:|-]+\|?$", nxt):
                header = cells
            continue
        if re.match(r"^\|[\s:|-]+\|?$", ln):
            continue
        if len(cells) < len(header):
            cells += [""] * (len(header) - len(cells))
        rows.append(dict(zip(header, cells[: len(header)])))
    return rows


def strip_md(s: str) -> str:
    s = re.sub(r"`([^`]*)`", r"\1", s)
    s = re.sub(r"\*\*([^*]*)\*\*", r"\1", s)
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
    return s.strip()


def first_float(s: str) -> float | None:
    m = re.search(r"-?\d+\.\d+|-?\d+", s.replace(",", ""))
    if not m:
        return None
    try:
        return float(m.group(0))
    except ValueError:
        return None


def first_date(s: str) -> dt.date | None:
    m = re.search(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", s)
    if not m:
        return None
    try:
        return dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def is_placeholder(s: str) -> bool:
    s = strip_md(s)
    return (not s) or s in {"-", "—", "?", "??"} or "YYYY" in s or s.startswith("{")


# --------------------------------------------------------------------------
# 収集
# --------------------------------------------------------------------------
@dataclass
class Warning_:
    level: str  # critical / serious / warning
    title: str
    detail: str
    action: str


@dataclass
class Snapshot:
    competition: str
    docs: Path
    meta: dict[str, str] = field(default_factory=dict)
    gates: list[dict[str, str]] = field(default_factory=list)
    budget: dict[str, str] = field(default_factory=dict)
    experiments: list[dict[str, str]] = field(default_factory=list)
    cvlb: list[dict[str, str]] = field(default_factory=list)
    formulations: list[dict[str, str]] = field(default_factory=list)
    measured: dict[str, object] = field(default_factory=dict)
    warnings: list[Warning_] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    focus: str = ""


def collect(docs: Path, competition: str) -> Snapshot:
    snap = Snapshot(competition=competition, docs=docs)

    def load(rel: str) -> str | None:
        text = read(docs / rel)
        if text is None:
            snap.missing.append(f"docs/{competition}/{rel}")
        return text

    # --- competition_overview.md -----------------------------------------
    ov = load("competition_overview.md")
    if ov:
        rows = parse_table(find_section(split_sections(ov), "基本情報"))
        for r in rows:
            k = strip_md(next(iter(r.values())))
            v = strip_md(list(r.values())[1]) if len(r) > 1 else ""
            if k:
                snap.meta[k] = v

    # --- gates.md ---------------------------------------------------------
    gt = load("gates.md")
    if gt:
        for body in split_sections(gt).values():
            for r in parse_table(body):
                gid = strip_md(r.get("ID", ""))
                if re.fullmatch(r"[RSTF]\d", gid):
                    snap.gates.append(
                        {
                            "id": gid,
                            "done": "x" in r.get("済", "").lower(),
                            "cond": strip_md(r.get("完了条件", "")),
                            "evidence": strip_md(
                                r.get("根拠（ファイル・件数・実測値）", "") or r.get("根拠", "")
                            ),
                        }
                    )

    # --- strategy.md ------------------------------------------------------
    st = load("strategy.md")
    if st:
        m = re.search(r"```\s*\n(.*?)```", st, re.S)
        if m:
            for line in m.group(1).splitlines():
                if ":" in line:
                    k, _, v = line.partition(":")
                    snap.budget[k.strip()] = v.strip()

    # --- experiments.md ---------------------------------------------------
    ex = load("experiments.md")
    if ex:
        secs = split_sections(ex)
        snap.experiments = parse_table(find_section(secs, "実験一覧"))
        snap.cvlb = parse_table(find_section(secs, "CV-LB"))
        focus = find_section(secs, "現在のフォーカス") or ""
        snap.focus = "\n".join(
            strip_md(ln) for ln in focus.splitlines()
            if ln.strip() and not ln.lstrip().startswith(">")
        ).strip()

    # --- formulations.md --------------------------------------------------
    fm = load("formulations.md")
    if fm:
        snap.formulations = [
            r
            for r in parse_table(find_section(fm and split_sections(fm), "候補一覧"))
            if re.search(r"F\d", strip_md(next(iter(r.values()), "")))
        ]

    # --- 機械計測 ----------------------------------------------------------
    disc = read(docs / "research" / "discussions.md") or ""
    nbs = read(docs / "research" / "public_notebooks.md") or ""
    eda_dir = docs / "eda"
    eda_files = (
        [p for p in eda_dir.glob("*.md") if p.name.lower() != "readme.md"]
        if eda_dir.is_dir()
        else []
    )
    model_dir = ROOT / "conf" / "model"
    archs = sorted(p.stem for p in model_dir.glob("*.yaml")) if model_dir.is_dir() else []

    snap.measured = {
        "unread_discussions": disc.count("[ ]"),
        "unchecked_notebooks": nbs.count("[ ]"),
        "eda_findings": len(eda_files),
        "formulation_count": len(snap.formulations),
        "arch_families": archs,
        "submissions_total": len(snap.cvlb),
        "submissions_7d": _recent_submissions(snap.cvlb, 7),
        "streak": _formulation_streak(snap.experiments),
        "days_left": _days_left(snap.meta),
    }
    _evaluate(snap)
    return snap


def _recent_submissions(cvlb: list[dict[str, str]], days: int) -> int | None:
    today = dt.date.today()
    dated = 0
    hits = 0
    for r in cvlb:
        d = first_date(strip_md(r.get("日付", "")))
        if d:
            dated += 1
            if (today - d).days <= days:
                hits += 1
    return hits if dated else None


def _formulation_streak(exps: list[dict[str, str]]) -> tuple[int, str]:
    """末尾から見て、同一定式化で連続している「改善しなかった実験」の本数。"""
    key_f = next((k for k in (exps[0] if exps else {}) if "定式化" in k), None)
    key_l = next((k for k in (exps[0] if exps else {}) if "失敗の層" in k), None)
    if not key_f or not key_l:
        return (0, "")
    streak = 0
    target = ""
    for r in reversed(exps):
        layer = strip_md(r.get(key_l, ""))
        form = strip_md(r.get(key_f, ""))
        form = (re.search(r"F\d", form) or [""])[0] if re.search(r"F\d", form) else form
        if not layer or layer in {"-", "—"}:
            continue  # 分析回など、判定対象外
        if layer == "該当なし":
            break  # 改善した実験に当たったら連続は途切れる
        if target and form != target:
            break
        target = form
        streak += 1
    return (streak, target)


def _days_left(meta: dict[str, str]) -> int | None:
    for k, v in meta.items():
        if "締切" in k or "終了" in k:
            d = first_date(v)
            if d:
                return (d - dt.date.today()).days
    return None


def _evaluate(snap: Snapshot) -> None:
    m = snap.measured
    claimed = {g["id"]: g["done"] for g in snap.gates}

    def conflict(gid: str, msg: str) -> None:
        if claimed.get(gid):
            snap.conflicts.append(f"{gid} にチェックが入っているが、{msg}")

    if m["unread_discussions"]:
        conflict("R2", f"discussions.md に未読 {m['unread_discussions']} 件が残っている")
    if m["unchecked_notebooks"]:
        conflict("R4", f"public_notebooks.md に未チェック {m['unchecked_notebooks']} 件がある")
    if m["formulation_count"] < 3:
        conflict("R5", f"formulations.md の候補が {m['formulation_count']} 案しかない")
    if m["eda_findings"] < 3:
        conflict("R6", f"eda/ の発見が {m['eda_findings']} 本しかない")
    if len(m["arch_families"]) < 2:
        conflict("T1", f"conf/model/ が {len(m['arch_families'])} 系統しかない")
    if not m["submissions_total"]:
        conflict("S1", "CV-LB 表に提出記録が 1 件も無い")

    W = snap.warnings.append
    streak, form = m["streak"]
    if streak >= 3:
        W(Warning_("critical", f"同一定式化 {streak} 連続ゼロ改善",
                   f"{form or '同一定式化'} で {streak} 本続けて改善していない（CLAUDE.md 第11節の禁止事項）",
                   "直ちに停止し、formulations.md の別案に移る"))
    elif streak == 2:
        W(Warning_("serious", f"2 ストライク（{form or '同一定式化'}）",
                   "同一定式化で 2 連続ゼロ改善。次の 1 実験は別定式化に充てる規定",
                   "formulations.md の未着手案から次の 1 本を選ぶ"))

    if len(m["arch_families"]) < 2:
        W(Warning_("serious", "アーキテクチャ族が 1 系統のみ",
                   f"conf/model/: {', '.join(m['arch_families']) or 'なし'}（Gate T1 未達）",
                   "2 系統目を立ち上げる。NN 系なら依存の uv add から"))

    s7 = m["submissions_7d"]
    if s7 == 0:
        W(Warning_("serious", "今週の提出 0 回",
                   "CV-LB 表に直近 7 日の提出が無い（下限は週 1 回）",
                   "現時点の best で 1 本出し、CV-LB 表に追記する"))
    elif s7 is None and not m["submissions_total"]:
        W(Warning_("warning", "提出記録なし",
                   "CV-LB 表が空。LB との対応が 1 点も取れていない",
                   "Phase 2 の S1/S2 を先に済ませる"))

    if m["unread_discussions"]:
        W(Warning_("critical", f"未読 Discussion {m['unread_discussions']} 件",
                   "Gate R2 未達。前回コンペで唯一完全に崩れたゲート",
                   "claude-in-chrome で本文とコメント欄を読む（WebFetch は SPA で失敗する）"))

    if m["formulation_count"] < 3:
        W(Warning_("serious", f"定式化候補が {m['formulation_count']} 案",
                   "Gate R5 は 3 案以上。候補が少ないのはリサーチ不足のサイン",
                   "R2/R3/R4 の成果から定式化候補を洗い出す"))

    plan = first_float(snap.budget.get("計画中の実験段数", "") or "")
    cap = first_float(snap.budget.get("残り実験可能数", "") or "")
    if plan and cap and plan > cap:
        W(Warning_("warning", "計画段数が残り実験可能数を超過",
                   f"計画 {plan:g} 本 > 実行可能 {cap:g} 本",
                   "ロードマップの段数を減らす"))

    for c in snap.conflicts:
        W(Warning_("critical", "宣言と実測の食い違い", c,
                   "gates.md のチェックを外すか、実物を埋める"))


def current_phase(snap: Snapshot) -> tuple[str, str, list[str]]:
    claimed = {g["id"]: g["done"] for g in snap.gates}
    conflicted = {c.split()[0] for c in snap.conflicts}
    for label, name, ids in PHASES:
        unmet = [i for i in ids if not claimed.get(i) or i in conflicted]
        if unmet:
            return label, name, unmet
    return "完了", "全ゲート達成", []


# --------------------------------------------------------------------------
# 描画
# --------------------------------------------------------------------------
STATUS = {"critical": "#d03b3b", "serious": "#ec835a", "warning": "#fab219", "good": "#0ca30c"}
ICON = {"critical": "✕", "serious": "▲", "warning": "！", "good": "✓"}

CSS = """
*,*::before,*::after{box-sizing:border-box}
:root{
  color-scheme:light;
  --page:#f9f9f7; --surface:#fcfcfb;
  --ink:#0b0b0b; --ink2:#52514e; --muted:#898781;
  --grid:#e1e0d9; --axis:#c3c2b7; --border:rgba(11,11,11,.10);
  --series:#2a78d6; --chip:rgba(11,11,11,.05);
}
@media (prefers-color-scheme:dark){:root{
  color-scheme:dark;
  --page:#0d0d0d; --surface:#1a1a19;
  --ink:#fff; --ink2:#c3c2b7; --muted:#898781;
  --grid:#2c2c2a; --axis:#383835; --border:rgba(255,255,255,.10);
  --series:#3987e5; --chip:rgba(255,255,255,.06);
}}
body{margin:0;background:var(--page);color:var(--ink);
  font:15px/1.6 system-ui,-apple-system,"Segoe UI",sans-serif;
  -webkit-font-smoothing:antialiased}
.wrap{max-width:1080px;margin:0 auto;padding:32px 20px 64px}
h1{font-size:24px;margin:0 0 4px;letter-spacing:-.01em}
h2{font-size:13px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);
  margin:0 0 12px;font-weight:600}
.sub{color:var(--ink2);font-size:14px;margin:0 0 28px}
.card{background:var(--surface);border:1px solid var(--border);border-radius:12px;
  padding:20px;margin-bottom:20px}
.row{display:flex;flex-wrap:wrap;gap:20px}
.row>.card{flex:1 1 300px;margin-bottom:0}
.grid{display:grid;gap:20px;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));
  margin-bottom:20px}
.stat{font:600 30px/1.15 system-ui,sans-serif;letter-spacing:-.02em}
.stat small{font-size:14px;font-weight:400;color:var(--ink2);letter-spacing:0}
.label{font-size:12px;color:var(--muted);margin-bottom:6px}
.meter{height:8px;border-radius:4px;background:var(--chip);overflow:hidden;margin-top:12px}
.meter>i{display:block;height:100%;border-radius:4px;background:var(--series)}
.warn{display:flex;gap:12px;padding:14px 16px;border-radius:10px;
  border:1px solid var(--border);background:var(--surface);margin-bottom:10px}
.warn .ic{flex:none;width:22px;height:22px;border-radius:50%;display:grid;place-items:center;
  color:#fff;font-size:12px;font-weight:700}
.warn b{display:block;font-size:14px;margin-bottom:2px}
.warn p{margin:0;font-size:13px;color:var(--ink2)}
.warn .do{margin-top:6px;font-size:13px;color:var(--ink)}
.warn .do::before{content:"→ ";color:var(--muted)}
.chips{display:flex;flex-wrap:wrap;gap:8px}
.chip{display:inline-flex;align-items:center;gap:6px;padding:5px 11px;border-radius:999px;
  font-size:13px;font-weight:600;border:1px solid var(--border);background:var(--chip);
  font-variant-numeric:tabular-nums}
.chip .d{width:8px;height:8px;border-radius:50%}
table{width:100%;border-collapse:collapse;font-size:13px}
th{text-align:left;font-weight:600;color:var(--muted);font-size:12px;
  padding:0 10px 8px 0;border-bottom:1px solid var(--grid);white-space:nowrap}
td{padding:9px 10px 9px 0;border-bottom:1px solid var(--grid);vertical-align:top;
  color:var(--ink2)}
td:first-child{color:var(--ink);font-weight:600;white-space:nowrap}
td.num{font-variant-numeric:tabular-nums;text-align:right;padding-right:16px;color:var(--ink)}
.pill{display:inline-block;padding:2px 8px;border-radius:999px;font-size:11px;font-weight:600;
  border:1px solid var(--border)}
.scroll{overflow-x:auto;-webkit-overflow-scrolling:touch}
.note{font-size:12px;color:var(--muted);margin-top:12px}
.foot{color:var(--muted);font-size:12px;border-top:1px solid var(--grid);padding-top:16px;
  margin-top:32px}
code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.92em;
  background:var(--chip);padding:1px 5px;border-radius:4px}
"""


def esc(s: object) -> str:
    return html.escape(str(s), quote=True)


def meter(frac: float) -> str:
    return f'<div class="meter"><i style="width:{max(0.0, min(1.0, frac)) * 100:.1f}%"></i></div>'


def oof_chart(exps: list[dict[str, str]]) -> str:
    """OOF の推移（単一系列の折れ線）。凡例なし・選択的な直接ラベル。"""
    key_id = next((k for k in (exps[0] if exps else {}) if k in ("ID", "exp")), None)
    key_oof = next((k for k in (exps[0] if exps else {}) if "OOF" in k), None)
    if not key_id or not key_oof:
        return '<p class="note">OOF 列が見つからないため描画できません。</p>'
    pts = []
    for r in exps:
        v = first_float(strip_md(r.get(key_oof, "")))
        if v is not None:
            pts.append((strip_md(r[key_id]), v))
    skipped = [
        strip_md(r[key_id]) for r in exps
        if first_float(strip_md(r.get(key_oof, ""))) is None and strip_md(r.get(key_id, ""))
    ]
    note = (f'<p class="note">数値が読めず除外: {esc(", ".join(skipped))}</p>' if skipped else "")
    if len(pts) < 2:
        return '<p class="note">データ点が 2 未満のため描画しません。</p>' + note

    W, H = 640, 190
    L, R, T, B = 44, 56, 16, 30
    vals = [v for _, v in pts]
    lo, hi = min(vals), max(vals)
    pad = (hi - lo) * 0.25 or max(abs(hi) * 0.05, 0.5)
    lo, hi = lo - pad, hi + pad
    xs = [L + (W - L - R) * i / (len(pts) - 1) for i in range(len(pts))]
    ys = [T + (H - T - B) * (1 - (v - lo) / (hi - lo)) for _, v in pts]
    best = min(range(len(pts)), key=lambda i: pts[i][1])

    g = []
    for k in range(3):
        v = lo + (hi - lo) * k / 2
        y = T + (H - T - B) * (1 - k / 2)
        g.append(f'<line x1="{L}" y1="{y:.1f}" x2="{W - R}" y2="{y:.1f}" stroke="var(--grid)"/>')
        g.append(f'<text x="{L - 8}" y="{y + 4:.1f}" text-anchor="end" font-size="11" '
                 f'fill="var(--muted)">{v:.1f}</text>')
    path = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}" for i, (x, y) in enumerate(zip(xs, ys)))
    g.append(f'<path d="{path}" fill="none" stroke="var(--series)" stroke-width="2" '
             f'stroke-linejoin="round" stroke-linecap="round"/>')
    for i, ((name, v), x, y) in enumerate(zip(pts, xs, ys)):
        g.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="var(--series)" '
                 f'stroke="var(--surface)" stroke-width="2"><title>{esc(name)}: {v:g}</title></circle>')
        g.append(f'<text x="{x:.1f}" y="{H - 10}" text-anchor="middle" font-size="10" '
                 f'fill="var(--muted)">{esc(name)}</text>')
        if i in (0, len(pts) - 1, best):
            g.append(f'<text x="{x:.1f}" y="{y - 12:.1f}" text-anchor="middle" font-size="11" '
                     f'font-weight="600" fill="var(--ink)">{v:g}</text>')
    return (f'<div class="scroll"><svg viewBox="0 0 {W} {H}" width="100%" style="min-width:520px" '
            f'role="img" aria-label="実験ごとの OOF 推移">{"".join(g)}</svg></div>' + note)


def md_table(rows: list[dict[str, str]], num_cols: tuple[str, ...] = ()) -> str:
    if not rows:
        return '<p class="note">記録がありません。</p>'
    heads = list(rows[0].keys())
    th = "".join(f"<th>{esc(h)}</th>" for h in heads)
    body = []
    for r in rows:
        tds = []
        for h in heads:
            cls = ' class="num"' if any(n in h for n in num_cols) else ""
            tds.append(f"<td{cls}>{esc(strip_md(r.get(h, '')))}</td>")
        body.append("<tr>" + "".join(tds) + "</tr>")
    return f'<div class="scroll"><table><thead><tr>{th}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'


def render(snap: Snapshot) -> str:
    m = snap.measured
    phase, phase_name, unmet = current_phase(snap)
    claimed = {g["id"]: g["done"] for g in snap.gates}
    conflicted = {c.split()[0] for c in snap.conflicts}
    title = snap.meta.get("URL", "").rstrip("/").split("/")[-1] or snap.competition

    # ---- ヘッダ統計
    days = m["days_left"]
    cap = first_float(snap.budget.get("残り実験可能数", "") or "")
    plan = first_float(snap.budget.get("計画中の実験段数", "") or "")
    best = first_float(snap.budget.get("現在の best", "") or "")
    goal = first_float(snap.budget.get("目標", "") or "")

    stats = []
    stats.append(f'<div class="card"><div class="label">フェーズ</div>'
                 f'<div class="stat">{esc(phase)} <small>{esc(phase_name)}</small></div>'
                 f'<div class="note">未達ゲート: {esc(", ".join(unmet)) if unmet else "なし"}</div></div>')
    if days is not None:
        head = f"{days} <small>日</small>" if days >= 0 else "<small>終了済み</small>"
        stats.append(f'<div class="card"><div class="label">締切まで</div>'
                     f'<div class="stat">{head}</div>'
                     f'<div class="note">実行可能 {("%g" % cap) if cap is not None else "?"} 本 / '
                     f'計画 {("%g" % plan) if plan is not None else "?"} 本</div></div>')
    if best is not None and goal is not None and best != goal:
        # 目標に対してどこまで来たか（小さいほど良い指標を想定し、null からの前進を測る）
        frac = 0.0
        null = first_float(snap.budget.get("null", "") or "")
        if null and null != goal:
            frac = (null - best) / (null - goal)
        stats.append(f'<div class="card"><div class="label">スコア</div>'
                     f'<div class="stat">{best:g} <small>→ 目標 {goal:g}</small></div>'
                     f'{meter(frac) if null else ""}'
                     f'<div class="note">残距離 {abs(best - goal):g}</div></div>')
    sub7 = m["submissions_7d"]
    stats.append(f'<div class="card"><div class="label">提出</div>'
                 f'<div class="stat">{m["submissions_total"]} <small>回（累計）</small></div>'
                 f'<div class="note">直近 7 日: {sub7 if sub7 is not None else "日付未記入"}'
                 f'{"（下限は週 1 回）" if sub7 == 0 else ""}</div></div>')

    # ---- 警告
    if snap.warnings:
        cards = []
        order = {"critical": 0, "serious": 1, "warning": 2}
        for w in sorted(snap.warnings, key=lambda w: order.get(w.level, 9)):
            c = STATUS[w.level]
            cards.append(
                f'<div class="warn"><div class="ic" style="background:{c}">{ICON[w.level]}</div>'
                f'<div><b>{esc(w.title)}</b><p>{esc(w.detail)}</p>'
                f'<div class="do">{esc(w.action)}</div></div></div>')
        warn_html = f'<h2>要対応 {len(snap.warnings)} 件</h2>{"".join(cards)}'
    else:
        warn_html = ('<h2>要対応</h2><div class="warn">'
                     f'<div class="ic" style="background:{STATUS["good"]}">{ICON["good"]}</div>'
                     '<div><b>警告なし</b><p>ゲート・提出頻度・定式化の多様性すべて基準内。</p></div></div>')

    # ---- ゲート
    chips = []
    for _, _, ids in PHASES:
        for gid in ids:
            ok = claimed.get(gid) and gid not in conflicted
            bad_claim = claimed.get(gid) and gid in conflicted
            color = STATUS["good"] if ok else (STATUS["critical"] if bad_claim else STATUS["warning"])
            mark = "✓" if ok else ("✕" if bad_claim else "—")
            chips.append(f'<span class="chip" title="{esc(next((g["cond"] for g in snap.gates if g["id"] == gid), ""))}">'
                         f'<span class="d" style="background:{color}"></span>{gid} {mark}</span>')
    gate_note = ('<p class="note">✓ 達成 / — 未達 / <b>✕ 宣言と実測が食い違い</b>'
                 '（gates.md にチェックがあるが実物が伴っていない）</p>')

    # ---- 計測
    measured_rows = [
        ("未読 Discussion", m["unread_discussions"], "件", "R2"),
        ("未チェック 公開NB", m["unchecked_notebooks"], "件", "R4"),
        ("定式化候補", m["formulation_count"], "案（3 案以上）", "R5"),
        ("EDA の発見", m["eda_findings"], "本（3 本以上）", "R6"),
        ("アーキテクチャ族", len(m["arch_families"]), f"系統（{', '.join(m['arch_families']) or 'なし'}）", "T1"),
        ("同一定式化の連続ゼロ改善", m["streak"][0], f"本（{m['streak'][1] or '—'}）", "第4節"),
    ]
    mrows = "".join(
        f"<tr><td>{esc(n)}</td><td class='num'>{v}</td><td>{esc(u)}</td>"
        f"<td><span class='pill'>{esc(g)}</span></td></tr>"
        for n, v, u, g in measured_rows)

    missing = ""
    if snap.missing:
        missing = ('<p class="note">未作成: ' +
                   ", ".join(f"<code>{esc(p)}</code>" for p in snap.missing) + "</p>")

    focus = f'<div class="card"><h2>現在のフォーカス</h2><p style="margin:0;white-space:pre-wrap">{esc(snap.focus)}</p></div>' if snap.focus else ""

    return f"""<!doctype html>
<html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} — ダッシュボード</title>
<style>{CSS}</style></head><body><div class="wrap">
<h1>{esc(title)}</h1>
<p class="sub">{esc(snap.meta.get("ホスト", ""))} ・ 締切 {esc(snap.meta.get("最終提出締切", "?"))}
 ・ 生成 {dt.datetime.now():%Y-%m-%d %H:%M}</p>

<div class="grid">{"".join(stats)}</div>

{warn_html}

{focus}

<div class="card"><h2>ゲート</h2><div class="chips">{"".join(chips)}</div>{gate_note}</div>

<div class="row">
<div class="card"><h2>機械計測</h2>
<table><tbody>{mrows}</tbody></table>
<p class="note">gates.md の自己申告ではなく、ファイルを数えた実測値。</p>{missing}</div>
</div>

<div class="card"><h2>OOF の推移</h2>{oof_chart(snap.experiments)}</div>

<div class="card"><h2>定式化ボード</h2>{md_table(snap.formulations)}</div>

<div class="card"><h2>実験一覧</h2>{md_table(snap.experiments, ("OOF", "LB"))}</div>

<div class="card"><h2>CV-LB</h2>{md_table(snap.cvlb, ("OOF", "LB", "差"))}</div>

<p class="foot">出典: <code>docs/{esc(snap.competition)}/</code>（gates.md / strategy.md /
experiments.md / formulations.md / research/ / eda/）と <code>conf/model/</code>。<br>
再生成: <code>uv run python scripts/build_dashboard.py --open</code></p>
</div></body></html>"""


# --------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("-c", "--competition", help="docs/ 配下のコンペ名（省略時は自動検出）")
    ap.add_argument("-o", "--out", default="outputs/dashboard.html")
    ap.add_argument("--open", action="store_true", help="生成後にブラウザで開く")
    a = ap.parse_args()

    docs_root = ROOT / "docs"
    if a.competition:
        comp = a.competition
    else:
        cands = sorted(
            (p for p in docs_root.iterdir() if p.is_dir() and not p.name.startswith("_")),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if not cands:
            print("docs/ にコンペディレクトリがありません。", file=sys.stderr)
            return 1
        comp = cands[0].name

    docs = docs_root / comp
    if not docs.is_dir():
        print(f"{docs} がありません。", file=sys.stderr)
        return 1

    snap = collect(docs, comp)
    out = ROOT / a.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(snap), encoding="utf-8")

    phase, name, unmet = current_phase(snap)
    print(f"{comp}: {phase}（{name}） / 未達ゲート {', '.join(unmet) or 'なし'} / "
          f"警告 {len(snap.warnings)} 件")
    print(f"→ {out}")
    if a.open:
        subprocess.run(["open", str(out)], check=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
