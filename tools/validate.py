"""Check the content files before publishing. Run from the repo root: python tools/validate.py"""
import json
import pathlib
import re
import sys
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent / "v1"
COLORS = {"red", "orange", "yellow", "green", "mint", "teal", "cyan", "blue", "indigo", "purple", "pink", "brown", "grey"}
ICONS = {"assessment", "show_chart", "payments", "store", "construction", "balance", "business_center", "campaign",
         "account_balance", "trending_up", "trending_down", "savings", "home", "elderly", "school", "medical", "shield",
         "eco", "bolt", "work", "public", "info", "calendar", "flag", "gavel", "receipt"}
ROUTES = {"overview", "economy_pulse", "revenue", "spending", "debt", "global_comparison", "spotlight", "calculator",
          "cost_of_living", "heatmaps", "simulator", "pound_health", "data_sources", "faq", "spotlight_immigration",
          "spotlight_nhs", "spotlight_defence", "spotlight_climate", "spotlight_housing", "spotlight_brexit",
          "spotlight_taxation", "spotlight_education", "spotlight_pensions"}
WIDGETS = {"savings_rent_tax_estimator"}
BLOCK_FIELDS = {
    "card": ["title", "blocks"], "heading": ["title"], "text": ["text"], "row": ["label", "value"], "divider": [],
    "bullet": ["title", "text"], "bar": ["label", "value", "max", "valueText"], "note": ["text"], "source": ["text"],
    "myth": ["myth", "reality"], "stats": ["items"], "link": ["title", "action"], "widget": ["widget", "params"],
    "table": ["columns", "rows"], "line_chart": ["labels", "series"], "factcheck": ["claim", "verdict", "summary"],
}
VERDICTS = {"accurate", "mostly_accurate", "missing_context", "misleading", "false", "unproven"}

errors, warnings = [], []
spotlight_ids = set()
tracker_ids = set()


def err(where, msg):
    errors.append(f"{where}: {msg}")


def load(rel):
    p = ROOT / rel
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except FileNotFoundError:
        err(rel, "file not found")
    except json.JSONDecodeError as e:
        err(rel, f"invalid JSON: {e}")
    return None


def check_color(where, c):
    if c is not None and c not in COLORS and not re.fullmatch(r"#[0-9A-Fa-f]{6}", str(c)):
        err(where, f"unknown color '{c}'")


def check_icon(where, i):
    if i is not None and i not in ICONS:
        warnings.append(f"{where}: unknown icon '{i}' (will show a default icon)")


def check_action(where, a):
    t = a.get("type")
    if t == "spotlight":
        if a.get("id") not in spotlight_ids:
            err(where, f"links to spotlight '{a.get('id')}' which isn't in the manifest")
    elif t == "tracker":
        if a.get("id") not in tracker_ids:
            err(where, f"links to tracker '{a.get('id')}' which isn't in the manifest")
    elif t == "route":
        if a.get("route") not in ROUTES:
            err(where, f"unknown route '{a.get('route')}'")
    elif t == "url":
        if not str(a.get("url", "")).startswith("https://"):
            err(where, "url actions must be https://")
    else:
        err(where, f"unknown action type '{t}'")


def check_blocks(where, blocks, depth=0):
    if not isinstance(blocks, list):
        err(where, "blocks must be a list")
        return
    for i, b in enumerate(blocks):
        w = f"{where}[{i}]"
        t = b.get("type")
        if t not in BLOCK_FIELDS:
            warnings.append(f"{w}: unknown block type '{t}' (apps will skip it)")
            continue
        for f in BLOCK_FIELDS[t]:
            if f not in b:
                err(w, f"{t} block is missing '{f}'")
        if t == "card":
            if depth > 0:
                err(w, "cards can't be nested inside cards")
            check_blocks(f"{w}.blocks", b.get("blocks", []), depth + 1)
        elif t == "bar":
            try:
                if float(b["max"]) <= 0:
                    err(w, "bar max must be above 0")
                if float(b["value"]) > float(b["max"]):
                    warnings.append(f"{w}: bar value is larger than max (will show full)")
            except (KeyError, TypeError, ValueError):
                err(w, "bar value and max must be numbers")
            check_color(w, b.get("color"))
        elif t == "link":
            check_action(w, b.get("action", {}))
        elif t == "widget":
            if b.get("widget") not in WIDGETS:
                err(w, f"unknown widget '{b.get('widget')}' (needs an app release first)")
            elif b["widget"] == "savings_rent_tax_estimator":
                p = b.get("params", {})
                steps = len(p.get("steps", []))
                for band in p.get("bands", []):
                    if len(band.get("rates", [])) != steps + 1:
                        err(w, f"band '{band.get('band')}' needs {steps + 1} rates (today + one per step)")
        elif t == "table":
            n = len(b.get("columns", []))
            for j, row in enumerate(b.get("rows", [])):
                if len(row) != n:
                    err(f"{w}.rows[{j}]", f"has {len(row)} cells but the table has {n} columns")
        elif t == "line_chart":
            n = len(b.get("labels", []))
            for j, ser in enumerate(b.get("series", [])):
                if len(ser.get("values", [])) != n:
                    err(f"{w}.series[{j}]", f"has {len(ser.get('values', []))} values but there are {n} labels")
                check_color(f"{w}.series[{j}]", ser.get("color"))
        elif t == "factcheck":
            if b.get("verdict") not in VERDICTS:
                err(w, f"verdict must be one of {sorted(VERDICTS)}")
        elif t == "stats":
            for j, it in enumerate(b.get("items", [])):
                if "value" not in it or "label" not in it:
                    err(f"{w}.items[{j}]", "stat needs value and label")


def check_iso(where, s):
    try:
        datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except ValueError:
        err(where, f"'{s}' isn't an ISO date-time like 2026-10-31T09:00:00Z")


manifest = load("manifest.json")
if manifest:
    for s in manifest.get("spotlights", []):
        spotlight_ids.add(s.get("id"))
    for tr in manifest.get("trackers", []):
        tracker_ids.add(tr.get("id"))
    for key in ("feed", "figures"):
        entry = manifest.get(key, {})
        data = load(entry.get("path", f"{key}.json"))
        if data and data.get("version") != entry.get("version"):
            err(f"{key}", f"version in file ({data.get('version')}) doesn't match manifest ({entry.get('version')})")
    seen = set()
    for s in manifest.get("spotlights", []):
        w = f"manifest spotlight '{s.get('id')}'"
        for f in ("id", "title", "subtitle", "path", "version", "access"):
            if f not in s:
                err(w, f"missing '{f}'")
        if s.get("id") in seen:
            err(w, "duplicate id")
        seen.add(s.get("id"))
        if s.get("access") not in ("free", "plus"):
            err(w, "access must be 'free' or 'plus'")
        check_color(w, s.get("color"))
        check_icon(w, s.get("icon"))
        doc = load(s.get("path", ""))
        if not doc:
            continue
        if doc.get("id") != s.get("id"):
            err(s["path"], f"id '{doc.get('id')}' doesn't match manifest id '{s.get('id')}'")
        if doc.get("version") != s.get("version"):
            err(s["path"], f"version in file ({doc.get('version')}) doesn't match manifest ({s.get('version')})")
        for f in ("theme", "hero", "tabs"):
            if f not in doc:
                err(s["path"], f"missing '{f}'")
        for c in ("primary", "deep", "light"):
            check_color(f"{s['path']} theme.{c}", doc.get("theme", {}).get(c))
        for i, tab in enumerate(doc.get("tabs", [])):
            check_icon(f"{s['path']} tabs[{i}]", tab.get("icon"))
            check_blocks(f"{s['path']} tabs[{i}] '{tab.get('title')}'", tab.get("blocks", []))

    for tr in manifest.get("trackers", []):
        w = f"manifest tracker '{tr.get('id')}'"
        for f in ("id", "title", "path", "version"):
            if f not in tr:
                err(w, f"missing '{f}'")
        check_icon(w, tr.get("icon"))
        check_color(w, tr.get("color"))
        doc = load(tr.get("path", ""))
        if not doc:
            continue
        if doc.get("id") != tr.get("id"):
            err(tr["path"], f"id '{doc.get('id')}' doesn't match manifest id '{tr.get('id')}'")
        if doc.get("version") != tr.get("version"):
            err(tr["path"], f"version in file ({doc.get('version')}) doesn't match manifest ({tr.get('version')})")
        check_color(f"{tr['path']} theme.primary", doc.get("theme", {}).get("primary"))
        metric_ids = set()
        for i, sec in enumerate(doc.get("sections", [])):
            for j, mt in enumerate(sec.get("metrics", [])):
                w2 = f"{tr['path']} sections[{i}].metrics[{j}]"
                for f in ("id", "label", "value", "asOf", "source"):
                    if f not in mt:
                        err(w2, f"missing '{f}'")
                if mt.get("id") in metric_ids:
                    err(w2, "duplicate metric id")
                metric_ids.add(mt.get("id"))
                ch = mt.get("change")
                if ch:
                    if ch.get("direction") not in ("up", "down", "flat"):
                        err(w2, "change.direction must be up, down or flat")
                    if ch.get("sentiment", "neutral") not in ("good", "bad", "neutral"):
                        err(w2, "change.sentiment must be good, bad or neutral")
                ser = mt.get("series")
                if ser and len(ser.get("labels", [])) != len(ser.get("values", [])):
                    err(w2, "series labels and values must be the same length")
        check_blocks(f"{tr['path']} blocks", doc.get("blocks", []))

feed = load("feed.json")
if feed:
    ids = set()
    for i, p in enumerate(feed.get("posts", [])):
        w = f"feed post {i} '{p.get('id')}'"
        for f in ("id", "publishedAt", "title", "summary"):
            if f not in p:
                err(w, f"missing '{f}'")
        if p.get("id") in ids:
            err(w, "duplicate id")
        ids.add(p.get("id"))
        check_iso(w, p.get("publishedAt"))
        if "expiresAt" in p:
            check_iso(w, p["expiresAt"])
        check_color(w, p.get("color"))
        check_icon(w, p.get("icon"))
        check_blocks(w, p.get("blocks", []))

figures = load("figures.json")
if figures:
    br = figures.get("bankRate", {})
    if not isinstance(br.get("rate"), (int, float)):
        err("figures.json", "bankRate.rate must be a number")

for w in warnings:
    print("warning:", w)
for e in errors:
    print("ERROR:", e)
print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)")
sys.exit(1 if errors else 0)
