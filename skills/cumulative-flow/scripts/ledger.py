# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Keep the ledger that cfd.py draws: one command for each thing that happens to a work item.

The ledger is a tab-separated file with a header row:
  id  title  kind  found  started  landed  commits  note
This script writes the times, so nobody edits rows by hand or reads the commit log for them.
"""

import argparse
import csv
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

COLUMNS = ["id", "title", "kind", "found", "started", "landed", "commits", "note"]
KINDS = ["defect", "broken-build", "feature", "tooling", "example", "research", "upstream"]
LABEL_KINDS = {"bug": "defect", "enhancement": "feature", "documentation": "tooling"}


def fail(code, message):
    print(f"ledger.py: {message}", file=sys.stderr)
    sys.exit(code)


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def moment(stamp):
    return datetime.fromisoformat(stamp.replace("Z", "+00:00"))


def clean(text):
    return " ".join(text.split())


def read(path, create=False):
    if not path.is_file():
        if create:
            return []
        fail(3, f"no ledger at {path}; `add` creates it with its first row")
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle, delimiter="\t", quoting=csv.QUOTE_NONE))
    if not rows or rows[0] != COLUMNS:
        fail(3, f"{path}: the first row must be exactly: " + "\t".join(COLUMNS))
    items = []
    for number, row in enumerate(rows[1:], start=2):
        if not any(cell.strip() for cell in row):
            continue
        if len(row) != len(COLUMNS):
            fail(3, f"{path} line {number}: {len(row)} fields, expected {len(COLUMNS)}")
        items.append(dict(zip(COLUMNS, row)))
    return items


def write(path, items):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    lines = ["\t".join(COLUMNS)] + ["\t".join(clean(item[column]) for column in COLUMNS) for item in items]
    temporary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    temporary.replace(path)


def find(items, wanted, path):
    for item in items:
        if item["id"] == wanted:
            return item
    known = ", ".join(item["id"] for item in items) or "none"
    fail(3, f"no row with id '{wanted}' in {path}; add it first. Ids there: {known}")


def annotate(item, text):
    if text and text not in item["note"]:
        item["note"] = "; ".join(part for part in (item["note"], text) if part)


def keep_order(item):
    """A start recorded after the landing commit was made can't be drawn: move it to the landing."""
    if item["started"] and item["landed"] and moment(item["started"]) > moment(item["landed"]):
        item["started"] = item["landed"]
        annotate(item, "approx: started after landing")


def run(command, code, what):
    try:
        return subprocess.run(command, capture_output=True, text=True, check=True).stdout
    except (subprocess.CalledProcessError, OSError) as error:
        detail = error.stderr.strip() if isinstance(error, subprocess.CalledProcessError) else str(error)
        fail(code, f"{what} failed: `{' '.join(command[:4])}`. {detail}")


def add(args):
    items = read(args.ledger, create=True)
    if any(item["id"] == args.id for item in items):
        print(f"{args.id}: already in the ledger, left as it is")
        return
    title = clean(" ".join(args.title))
    found, note = now(), clean(args.note)
    if args.found:
        try:
            given = moment(args.found)
        except ValueError:
            given = None
        if given is None or given.tzinfo is None:
            fail(2, f"--found '{args.found}' is not an ISO 8601 time with a zone, such as 2026-11-22T13:30:00Z")
        found = given.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        note = "; ".join(part for part in (note, "approx: found time given afterwards") if part)
    items.append({"id": args.id, "title": title, "kind": args.kind, "found": found, "started": "", "landed": "",
                  "commits": "", "note": note})
    write(args.ledger, items)
    print(f"{args.id}: found {items[-1]['found']}")


def start(args):
    items = read(args.ledger)
    for wanted in args.ids:
        item = find(items, wanted, args.ledger)
        if item["started"]:
            print(f"{wanted}: already started {item['started']}, left as it is")
        else:
            item["started"] = now()
            print(f"{wanted}: started {item['started']}")
    write(args.ledger, items)


def land(args):
    items = read(args.ledger)
    item = find(items, args.id, args.ledger)
    git = ["git", "-C", str(args.repo)]
    stamp = run(git + ["log", "-1", "--format=%cI", args.commits[-1]], 1, "reading the commit's time").strip()
    hashes = [run(git + ["rev-parse", "--short", commit], 1, "reading the commit").strip() for commit in args.commits]
    landed = moment(stamp).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if item["found"] and moment(landed) < moment(item["found"]):
        fail(3, f"{args.id} was found at {item['found']}, but commit {hashes[-1]} was made at {landed}. An item can't "
                "land before it was found. Give the commit that finished it. If the row was added after the work was "
                "done, the ledger has the wrong found time: add such rows with `add --found TIME`.")
    item["landed"] = landed
    item["commits"] = ",".join(hashes)
    keep_order(item)
    write(args.ledger, items)
    print(f"{args.id}: landed {item['landed']} ({item['commits']})")


def drop(args):
    items = read(args.ledger)
    item = find(items, args.id, args.ledger)
    item["landed"] = now()
    annotate(item, f"dropped: {clean(args.note)}")
    write(args.ledger, items)
    print(f"{args.id}: dropped {item['landed']}")


def kind_of(labels):
    return (next((label for label in labels if label in KINDS), None)
            or next((LABEL_KINDS[label] for label in labels if label in LABEL_KINDS), None)
            or "feature")


def timeline(gh, repo, issue):
    pages = json.loads(run([gh, "api", "--paginate", "--slurp", f"repos/{repo}/issues/{issue['number']}/timeline"],
                           1, "reading the issue's timeline") or "[]")
    return [event for page in pages for event in page]


def first_assignment(events):
    return next((event.get("created_at") or "" for event in events if event.get("event") == "assigned"), "")


def landing(gh, repo, issue):
    """Return (landed, commit, started, note) for a closed issue, from its timeline."""
    events = timeline(gh, repo, issue)
    assigned = first_assignment(events)
    closed = [event for event in events if event.get("event") == "closed"]
    referenced = [event for event in events if event.get("event") == "referenced" and event.get("commit_id")]
    sha = (closed[-1].get("commit_id") if closed else None) or (referenced[-1]["commit_id"] if referenced else None)
    if sha:
        # A closing commit may be gone (rebased away): then fall back to the close time.
        try:
            stamp = subprocess.run([gh, "api", f"repos/{repo}/commits/{sha}", "--jq", ".commit.committer.date"],
                                   capture_output=True, text=True, check=True).stdout.strip()
        except (subprocess.CalledProcessError, OSError):
            stamp = ""
        if stamp:
            return stamp, sha[:8], assigned, ""
    note = "dropped: closed as not planned" if issue.get("stateReason") == "NOT_PLANNED" else "approx: closed without a commit"
    return issue["closedAt"], "", assigned, note


def sync(args):
    gh = os.environ.get("GH", "gh")
    items = read(args.ledger, create=True)
    by_id = {item["id"]: item for item in items}
    added = landed = reopened = questions = 0
    for repo in args.repos:
        if repo.count("/") != 1:
            fail(2, f"'{repo}' is not OWNER/REPO")
        listing = run([gh, "issue", "list", "-R", repo, "--state", "all", "--limit", "1000", "--json",
                       "number,title,labels,assignees,createdAt,closedAt,stateReason"], 1, "listing the issues")
        for issue in sorted(json.loads(listing or "[]"), key=lambda entry: entry["number"]):
            labels = [label["name"] for label in issue["labels"]]
            if "question" in labels:
                questions += 1
                continue
            ident = f"{repo.split('/')[1]}#{issue['number']}"
            item = by_id.get(ident)
            if item is None:
                item = {"id": ident, "title": clean(issue["title"]), "kind": kind_of(labels), "found": issue["createdAt"],
                        "started": "", "landed": "", "commits": "", "note": ""}
                items.append(item)
                by_id[ident] = item
                added += 1
            if issue["closedAt"] and not item["landed"]:
                item["landed"], item["commits"], assigned, note = landing(gh, repo, issue)
                if moment(item["landed"]) < moment(item["found"]):
                    # The closing commit was made before the issue was opened: the issue's own close time is the landing.
                    item["landed"], note = issue["closedAt"], "approx: the closing commit is older than the issue"
                if assigned and moment(assigned) < moment(item["found"]):
                    assigned = ""
                annotate(item, note)
                if not item["started"]:
                    # Nobody recorded a start: take the assignment if there was one, or else the landing.
                    item["started"] = assigned or item["landed"]
                keep_order(item)
                landed += 1
            elif not issue["closedAt"] and item["landed"]:
                item["landed"] = item["commits"] = ""
                reopened += 1
            if not issue["closedAt"] and not item["started"] and issue.get("assignees"):
                # Someone was assigned and no start was recorded here: the assignment is the start.
                item["started"] = first_assignment(timeline(gh, repo, issue))
    write(args.ledger, items)
    print(f"{added} added, {landed} landed, {reopened} reopened, {questions} questions left out; {len(items)} rows")


def main():
    parser = argparse.ArgumentParser(
        prog="uv run scripts/ledger.py",
        description="Keep the ledger that cfd.py draws. Each command records one thing that happened to a work "
                    "item and writes the time itself.",
        epilog="Exit codes: 0 done; 1 git or the GitHub CLI failed; 2 bad arguments; 3 a problem with the ledger.\n"
               "Examples:\n"
               "  uv run scripts/ledger.py add work/ledger.tsv D7 defect The importer drops the last row\n"
               "  uv run scripts/ledger.py start work/ledger.tsv D7\n"
               "  uv run scripts/ledger.py land work/ledger.tsv D7 4f2a9c1 --repo ~/code/app\n"
               "  uv run scripts/ledger.py sync work/ledger.tsv owner/app",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    one = commands.add_parser("add", help="an item was found: add its row, with found set to now")
    one.add_argument("ledger", type=Path)
    one.add_argument("id")
    one.add_argument("kind", choices=KINDS, metavar="KIND", help="one of: " + ", ".join(KINDS))
    one.add_argument("title", nargs="+")
    one.add_argument("--note", default="")
    one.add_argument("--found", metavar="TIME", help="for an item logged after the fact: when it was found "
                     "(ISO 8601 with a zone); the row is marked approx")
    one.set_defaults(run=add)

    one = commands.add_parser("start", help="someone began the item: set started to now, once")
    one.add_argument("ledger", type=Path)
    one.add_argument("ids", nargs="+", metavar="ID")
    one.set_defaults(run=start)

    one = commands.add_parser("land", help="the item is finished: set landed to the time of its last commit")
    one.add_argument("ledger", type=Path)
    one.add_argument("id")
    one.add_argument("commits", nargs="+", metavar="COMMIT", help="the item's commits, the finishing one last")
    one.add_argument("--repo", type=Path, default=Path("."), help="the repository the commits are in (default: here)")
    one.set_defaults(run=land)

    one = commands.add_parser("drop", help="nobody will do the item: land it now, with the reason")
    one.add_argument("ledger", type=Path)
    one.add_argument("id")
    one.add_argument("--note", required=True, help="why it was dropped")
    one.set_defaults(run=drop)

    one = commands.add_parser(
        "sync", help="bring the ledger up to date from GitHub issues: new issues become rows, closed ones land",
        description="For each repository, add a row for every issue the ledger lacks (found is when it was opened) "
                    "and land every closed issue at the time of the commit that closed it. Starts recorded with "
                    "`start` are kept; an issue with no recorded start takes its first assignment, or else, once "
                    "closed, its landing. Issues labeled `question` are left out. Reads GitHub through the GitHub CLI: set GH "
                    "to name another program than gh.")
    one.add_argument("ledger", type=Path)
    one.add_argument("repos", nargs="+", metavar="OWNER/REPO")
    one.set_defaults(run=sync)

    args = parser.parse_args()
    args.run(args)


if __name__ == "__main__":
    main()
