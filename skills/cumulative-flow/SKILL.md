---
name: cumulative-flow
description: >-
  Use when someone asks how far along a body of work is, whether it is
  converging, or what percent done it is; when reporting progress toward a
  release, a candidate, a milestone, or a migration over hours or days; when
  the user mentions a cumulative flow diagram, CFD, burn-up, burndown, kanban
  flow, work in progress, or "is the bug list shrinking"; or when an
  orchestrator starts a long stretch of work with many items and several
  agents. Keeps a plain-text ledger of work items with the times each was
  found, started, and landed, and draws a cumulative flow diagram from it with
  bundled scripts. Not for charts of other data (use dataviz), and not for
  planning what to do next.
compatibility: Requires uv to run the bundled scripts, and git to record a landing. The GitHub CLI is needed only to fill the ledger from GitHub issues.
license: CC0-1.0
metadata:
  author: Kerrick's AI Agent(s)
  version: "0.2.0"
---

# Cumulative flow

You already know what a cumulative flow diagram is and how to read one. This skill adds what makes one trustworthy when agents do the work: a ledger kept as the work happens, rules for what counts as an item and when, and scripts that write the ledger's times and draw the chart, so no model is needed for either. Where a rule here conflicts with advice you would usually follow, follow the rule here.

An estimate of "percent done" says nothing about whether the work is converging. The chart does: it shows items found against items landed over time.

## Keep the ledger as the work happens

1. **Start the ledger when the work starts.** Put it with the work's private state, not in the project's repository, unless the project's own rules give it a place. It is one tab-separated file with this header row:
   ```
   id	title	kind	found	started	landed	commits	note
   ```
2. **Add a row the moment an item is found,** before starting anything about it. An item logged later gets a guessed time, and a batch of late rows reads as a queue that just grew.
   ```bash
   uv run scripts/ledger.py add path/to/ledger.tsv D7 defect The importer drops the last row
   ```
   The first `add` creates the file. The id is yours to choose; the kind is one of the set under **What a row is**.
3. **Record the start when someone begins the item,** in the same step that hands it to an agent:
   ```bash
   uv run scripts/ledger.py start path/to/ledger.tsv D7
   ```
4. **Record the landing from the commit, not from memory:**
   ```bash
   uv run scripts/ledger.py land path/to/ledger.tsv D7 4f2a9c1 --repo path/to/repository
   ```
   It takes the time from the commit and writes its short hash. An item reverted and done again lands at the final commit: run `land` again with that one.

   `ledger.py` writes every time itself, from the clock or from the commit. Don't edit rows by hand, and don't read the commit log to fill them in.
5. **Redraw** whenever you report progress, and after a batch of changes:
   ```bash
   uv run scripts/cfd.py path/to/ledger.tsv --title "Road to 1.0" --utc-offset -6
   ```
   It writes `cfd.svg` beside the ledger and prints the counts now and six hours ago. `--markers FILE` draws vertical marks from a file of `TIME<TAB>LABEL` lines: add one when a release is tagged or the build breaks. `--help` lists the rest.
6. **Report from the script's output:** the three counts, how each moved over the comparison window, and one sentence on whether the queue is growing, flat, or shrinking. Say how many rows have a missing or approximate time.

## What a row is

- **One row per work item that stands between here and the goal,** not one per commit and not one per agent. A defect, a break of the build, a feature the goal needs, a piece of tooling.
- **`kind` is one of:** `defect`, `broken-build`, `feature`, `tooling`, `example`, `research`, `upstream` (someone else's to fix). Keep to the set, so the counts by kind compare over time.
- **A row is found when anyone learns the item exists,** including an item that a proof, a review, or a probe turns up while doing something else. Those are the rows that show whether looking still finds more than fixing closes.
- **Never invent a time.** Leave the field empty when it is unknown. When a time comes from a note written afterwards, write `approx` in `note`. The script counts both.
- **An item nobody will do is not deleted.** Drop it, with the reason (`uv run scripts/ledger.py drop path/to/ledger.tsv D7 --note "why"`), which lands it now, or move it to `upstream`.

## When the work is tracked in GitHub issues

Skip this section when the project keeps no issues, or doesn't use them for its work. The ledger and the three commands above are all the chart needs.

Where each work item is an issue, fill the ledger from them before each redraw:

```bash
uv run scripts/ledger.py sync path/to/ledger.tsv owner/repository
```

Every issue the ledger lacks becomes a row with the id `repository#number`, found when the issue was opened. Every closed issue lands at the time of the commit that closed it. Issues labeled `question` are left out, since they wait on a person and are not work items. Name several repositories to chart them together. To use another program than `gh`, set `GH`.

- **Still run `start` when you hand an issue to an agent** (`start path/to/ledger.tsv repository#12`). One commit often both begins and finishes an issue, and then nothing but the recorded start shows the item was ever in progress.
- **An issue with no recorded start** takes the time it was first assigned to someone, if it was. A closed issue with neither starts when it landed.
- **Never add a row by hand for something that is an issue.** Open the issue; the next `sync` brings it in.

## Reading it

- **Queue growing while done grows:** the work is still in discovery. A percentage means little here; say so.
- **In progress wide and flat:** items are started and not finished. Look for work that is waiting on something.
- **Queue flat or shrinking, done rising:** converging. Only now is a date worth estimating, from the slope of done.
- **A step up in the queue just after a build breaks or a probe runs** is the cost of that event; the markers make it visible.

## Backfilling a ledger that was not kept

When asked for a chart of work already under way, build the ledger from the notes and the commit history once, then keep it by the rules above. Take `landed` from commit times. Take `found` and `started` only where the notes give a time (`ledger.py add --found TIME` records a past found time and marks the row `approx`), and report the share of rows that are approximate with the chart. Read the notes and one log listing; do not re-read the work itself.

## Gotchas

- Logging items in batches from memory, so `found` times bunch up and the queue seems to jump.
- Taking `landed` from a status note. Notes written during the work run ahead of the commits they describe.
- One row per commit, which makes the chart a commit graph and hides the items still open.
- Leaving discovered defects out because they were fixed quickly. They are the evidence of how much is still being found.
- Quoting a percent done while the queue is growing.
- Asking a model to redraw the chart, or drawing one by hand. `cfd.py` does it from the ledger.
- Editing the ledger by hand or with a one-line script, or running `git log` for each landing. `ledger.py` does each in one command and keeps the file valid.
- Running a script through a tool runner that changes directory, with relative paths. Give the ledger, `--repo` and `--out` as absolute paths.
