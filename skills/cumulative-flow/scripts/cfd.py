# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Draw a cumulative flow diagram from a ledger of work items.

The ledger is a tab-separated file with a header row:
  id  title  kind  found  started  landed  commits  note
Times are ISO 8601 (2026-11-22T13:30:00Z). An empty time means unknown.
"""

import argparse
import csv
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from xml.sax.saxutils import escape

COLUMNS = ["id", "title", "kind", "found", "started", "landed", "commits", "note"]
BANDS = [
    ("Done (landed)", "#4a7c59"),
    ("In progress (started)", "#c08a2d"),
    ("Queue (found, not started)", "#8a94a6"),
]


def fail(code, message):
    print(f"cfd.py: {message}", file=sys.stderr)
    sys.exit(code)


def parse_time(text, where):
    text = text.strip()
    if not text:
        return None
    try:
        moment = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        fail(3, f"{where}: '{text}' is not an ISO 8601 time such as 2026-11-22T13:30:00Z")
    if moment.tzinfo is None:
        fail(3, f"{where}: '{text}' has no time zone; end it with Z or an offset")
    return moment.astimezone(timezone.utc)


def read_ledger(path):
    if not path.is_file():
        fail(3, f"no ledger at {path}; create it with the header row: " + "\t".join(COLUMNS))
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle, delimiter="\t", quoting=csv.QUOTE_NONE))
    if not rows or rows[0] != COLUMNS:
        fail(3, f"{path}: the first row must be exactly: " + "\t".join(COLUMNS))
    items, problems, seen = [], [], set()
    for number, row in enumerate(rows[1:], start=2):
        if not any(cell.strip() for cell in row):
            continue
        if len(row) != len(COLUMNS):
            problems.append(f"line {number}: {len(row)} fields, expected {len(COLUMNS)} (empty fields still need their tabs)")
            continue
        item = dict(zip(COLUMNS, row))
        where = f"line {number} ({item['id']})"
        if item["id"] in seen:
            problems.append(f"{where}: the id is used twice")
        seen.add(item["id"])
        found, started, landed = (parse_time(item[key], f"{where} {key}") for key in ("found", "started", "landed"))
        if found and started and started < found:
            problems.append(f"{where}: started before found")
        if started and landed and landed < started:
            problems.append(f"{where}: landed before started")
        if found and landed and landed < found:
            problems.append(f"{where}: landed before found")
        dated = [moment for moment in (found, started, landed) if moment]
        if not dated:
            problems.append(f"{where}: no time at all; give found at least")
            continue
        items.append({"id": item["id"], "kind": item["kind"], "enter": min(dated), "found": found,
                      "started": started, "landed": landed, "approx": "approx" in item["note"].lower()})
    if problems:
        fail(3, f"{path} has {len(problems)} problem(s):\n  " + "\n  ".join(problems))
    if not items:
        fail(3, f"{path} has no rows")
    return items


def read_markers(path):
    if path is None:
        return []
    if not path.is_file():
        fail(3, f"no markers file at {path}")
    markers = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) != 2:
            fail(3, f"{path} line {number}: expected a time, a tab, and a label")
        markers.append((parse_time(parts[0], f"{path} line {number}"), parts[1]))
    return markers


def count(items, moment):
    done = sum(1 for item in items if item["landed"] and item["landed"] <= moment)
    progress = sum(1 for item in items if item["started"] and item["started"] <= moment
                   and not (item["landed"] and item["landed"] <= moment))
    entered = sum(1 for item in items if item["enter"] <= moment)
    return {"queue": entered - done - progress, "in_progress": progress, "done": done}


def floor_to(moment, step):
    seconds = int(moment.timestamp())
    return datetime.fromtimestamp(seconds - seconds % int(step.total_seconds()), timezone.utc)


def draw(steps, counts, markers, title, offset_hours, total):
    width, height, left, right, top, bottom = 1180, 560, 60, 140, 50, 110
    plot_w, plot_h = width - left - right, height - top - bottom
    start, end = steps[0], steps[-1]
    span = max((end - start).total_seconds(), 1)
    y_max = max(10, -(-total // 10) * 10)

    def x(moment):
        return left + plot_w * (moment - start).total_seconds() / span

    def y(value):
        return top + plot_h - plot_h * value / y_max

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
           f'font-family="sans-serif" font-size="12" fill="currentColor">',
           f"<title>{escape(title)}</title>",
           f'<text x="{left}" y="24" font-size="16" font-weight="bold">{escape(title)}</text>']
    grid = max(1, y_max // 10)
    for value in range(0, y_max + 1, grid):
        out.append(f'<line x1="{left}" x2="{left + plot_w}" y1="{y(value):.1f}" y2="{y(value):.1f}" stroke="currentColor" stroke-opacity="0.15"/>')
        out.append(f'<text x="{left - 6}" y="{y(value) + 4:.1f}" text-anchor="end">{value}</text>')
    out.append(f'<text transform="translate(14,{top + plot_h / 2}) rotate(-90)" text-anchor="middle">work items (cumulative)</text>')
    stacked = [(c["done"], c["done"] + c["in_progress"], c["done"] + c["in_progress"] + c["queue"]) for c in counts]
    for layer in (2, 1, 0):
        name, color = BANDS[layer]
        upper = [s[layer] for s in stacked]
        lower = [0] * len(stacked) if layer == 0 else [s[layer - 1] for s in stacked]
        points = [f"{x(steps[k]):.1f},{y(upper[k]):.1f}" for k in range(len(steps))]
        points += [f"{x(steps[k]):.1f},{y(lower[k]):.1f}" for k in reversed(range(len(steps)))]
        out.append(f'<polygon points="{" ".join(points)}" fill="{color}" fill-opacity="0.9" stroke="currentColor" '
                   f'stroke-opacity="0.5" stroke-width="0.6"><title>{name}</title></polygon>')
    out.append(f'<line x1="{left}" x2="{left + plot_w}" y1="{y(0):.1f}" y2="{y(0):.1f}" stroke="currentColor"/>')
    out.append(f'<line x1="{left}" x2="{left}" y1="{top}" y2="{y(0):.1f}" stroke="currentColor"/>')
    hours = span / 3600
    tick_hours = next(h for h in (1, 3, 6, 12, 24, 48, 168, 336) if hours / h <= 10 or h == 336)
    tick = floor_to(start, timedelta(hours=tick_hours))
    local = timezone(timedelta(hours=offset_hours))
    sign = "+" if offset_hours >= 0 else "-"
    zone = f"UTC{sign}{abs(offset_hours):g}"
    while tick <= end:
        if tick >= start:
            out.append(f'<line x1="{x(tick):.1f}" x2="{x(tick):.1f}" y1="{y(0):.1f}" y2="{y(0) + 5:.1f}" stroke="currentColor"/>')
            out.append(f'<text x="{x(tick):.1f}" y="{y(0) + 19:.1f}" text-anchor="middle">{tick:%d %H:%M}Z</text>')
            if offset_hours:
                out.append(f'<text x="{x(tick):.1f}" y="{y(0) + 33:.1f}" text-anchor="middle" fill-opacity="0.7">'
                           f'{tick.astimezone(local):%d %H:%M} ({zone})</text>')
        tick += timedelta(hours=tick_hours)
    for index, (moment, label) in enumerate(markers):
        if start <= moment <= end:
            out.append(f'<line x1="{x(moment):.1f}" x2="{x(moment):.1f}" y1="{top}" y2="{y(0):.1f}" stroke="currentColor" '
                       f'stroke-width="1.2" stroke-dasharray="5,3"/>')
            out.append(f'<text x="{x(moment) + 3:.1f}" y="{top + 12 + (index % 2) * 13}" font-size="11">{escape(label)}</text>')
    last = counts[-1]
    edge = left + plot_w + 12
    out.append(f'<text x="{edge}" y="{y(last["done"] / 2) + 4:.1f}" font-weight="bold">{last["done"]} done</text>')
    out.append(f'<text x="{edge}" y="{y(last["done"] + last["in_progress"] / 2) + 4:.1f}" font-weight="bold">{last["in_progress"]} in progress</text>')
    out.append(f'<text x="{edge}" y="{y(last["done"] + last["in_progress"] + last["queue"] / 2) + 4:.1f}" font-weight="bold">{last["queue"]} queue</text>')
    out.append(f'<text x="{edge}" y="{top - 6}">total {total}</text>')
    for index, (name, color) in enumerate(BANDS):
        at = left + index * 250
        out.append(f'<rect x="{at}" y="{height - 32}" width="14" height="14" fill="{color}" stroke="currentColor" stroke-opacity="0.5"/>')
        out.append(f'<text x="{at + 20}" y="{height - 21}">{name}</text>')
    out.append("</svg>")
    return "\n".join(out) + "\n"


def main():
    parser = argparse.ArgumentParser(
        prog="uv run scripts/cfd.py",
        description="Draw a cumulative flow diagram (SVG) from a ledger of work items, and print the counts now and a while ago.",
        epilog="Exit codes: 0 drawn; 2 bad arguments; 3 the ledger or markers file is missing or invalid (each problem is listed).\n"
               "Example: uv run scripts/cfd.py work/ledger.tsv --out work/cfd.svg --title 'Road to 1.0' --utc-offset -6",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("ledger", type=Path, help="tab-separated ledger: " + " ".join(COLUMNS))
    parser.add_argument("--out", type=Path, help="SVG to write (default: cfd.svg beside the ledger)")
    parser.add_argument("--title", default="Cumulative flow of work items", help="the chart's heading")
    parser.add_argument("--step-minutes", type=int, default=30, help="how often to count (default 30)")
    parser.add_argument("--utc-offset", type=float, default=0, help="hours from UTC for a second row of axis labels, such as -6")
    parser.add_argument("--markers", type=Path, help="tab-separated file of TIME<TAB>LABEL lines to draw as vertical marks")
    parser.add_argument("--compare-hours", type=float, default=6, help="also report the counts this many hours ago (default 6)")
    parser.add_argument("--json", action="store_true", help="print the summary as JSON")
    args = parser.parse_args()
    if args.step_minutes < 1:
        parser.error(f"--step-minutes must be 1 or more. Received: {args.step_minutes}")

    items = read_ledger(args.ledger)
    markers = read_markers(args.markers)
    step = timedelta(minutes=args.step_minutes)
    start = floor_to(min(item["enter"] for item in items), step)
    latest = max(moment for item in items for moment in (item["enter"], item["started"], item["landed"]) if moment)
    end = floor_to(max(datetime.now(timezone.utc), latest), step) + step
    steps = []
    moment = start
    while moment <= end:
        steps.append(moment)
        moment += step
    counts = [count(items, moment) for moment in steps]
    out = args.out or args.ledger.with_name("cfd.svg")
    out.write_text(draw(steps, counts, markers, args.title, args.utc_offset, len(items)), encoding="utf-8")

    earlier = count(items, end - timedelta(hours=args.compare_hours))
    kinds = {}
    for item in items:
        kinds[item["kind"]] = kinds.get(item["kind"], 0) + 1
    summary = {
        "at": end.strftime("%Y-%m-%dT%H:%M:%SZ"), "rows": len(items), "now": counts[-1],
        f"{args.compare_hours:g}h_ago": earlier, "by_kind": dict(sorted(kinds.items())),
        "rows_without_found": sum(1 for item in items if not item["found"]),
        "rows_marked_approx": sum(1 for item in items if item["approx"]), "svg": str(out),
    }
    if args.json:
        print(json.dumps(summary, indent=2))
        return
    now = counts[-1]
    print(f"{summary['at']}: queue {now['queue']}, in progress {now['in_progress']}, done {now['done']} ({len(items)} rows)")
    print(f"{args.compare_hours:g} h ago: queue {earlier['queue']}, in progress {earlier['in_progress']}, done {earlier['done']}")
    print("by kind: " + ", ".join(f"{kind} {number}" for kind, number in summary["by_kind"].items()))
    print(f"rows with no found time: {summary['rows_without_found']}; rows marked approx: {summary['rows_marked_approx']}")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
