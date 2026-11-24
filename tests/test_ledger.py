"""Tests for skills/cumulative-flow/scripts/ledger.py, with a real git repository and a fake `gh`.

Run from the repository root: uv run python -m unittest discover tests
"""

import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "skills" / "cumulative-flow" / "scripts" / "ledger.py"
CFD = ROOT / "skills" / "cumulative-flow" / "scripts" / "cfd.py"
HEADER = "id\ttitle\tkind\tfound\tstarted\tlanded\tcommits\tnote"

FAKE_GH = '''#!/usr/bin/env python3
import json, os, sys
data = json.load(open(os.environ["FAKE_GH_DATA"]))
args = sys.argv[1:]
if args[:2] == ["issue", "list"]:
    print(json.dumps(data["issues"][args[args.index("-R") + 1]]))
elif args[0] == "api" and args[-1].endswith("/timeline"):
    print(json.dumps([data["timelines"].get(args[-1], [])]))
elif args[0] == "api" and "/commits/" in args[1]:
    time = data["commits"].get(args[1])
    if time is None:
        sys.exit(1)
    print(time)
else:
    sys.exit(2)
'''


def issue(number, title="An item", labels=(), opened="2026-01-01T00:00:00Z", closed=None, reason=None, assignees=()):
    return {"number": number, "title": title, "labels": [{"name": name} for name in labels],
            "assignees": [{"login": login} for login in assignees],
            "createdAt": opened, "closedAt": closed, "stateReason": reason}


class LedgerTest(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp())
        self.ledger = self.folder / "work" / "ledger.tsv"

    def run_script(self, *args, env=None, expect=0):
        done = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True,
                              env={**os.environ, **(env or {})})
        self.assertEqual(done.returncode, expect, done.stderr + done.stdout)
        return done

    def rows(self):
        lines = self.ledger.read_text().splitlines()
        self.assertEqual(lines[0], HEADER)
        return {line.split("\t")[0]: dict(zip(HEADER.split("\t"), line.split("\t"))) for line in lines[1:]}

    def repository(self):
        repo = self.folder / "repo"
        repo.mkdir()
        env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com", "GIT_COMMITTER_NAME": "t",
               "GIT_COMMITTER_EMAIL": "t@example.com", "GIT_COMMITTER_DATE": "2026-03-04T05:06:07+01:00",
               "GIT_AUTHOR_DATE": "2026-03-04T05:06:07+01:00"}
        for command in (["init", "-q"], ["commit", "-q", "--allow-empty", "-m", "the fix"]):
            subprocess.run(["git", "-C", str(repo), *command], check=True, env=env, capture_output=True)
        sha = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], check=True, capture_output=True, text=True)
        return repo, sha.stdout.strip()

    def gh(self, data):
        program = self.folder / "gh"
        program.write_text(FAKE_GH)
        program.chmod(program.stat().st_mode | stat.S_IEXEC)
        store = self.folder / "gh.json"
        store.write_text(json.dumps(data))
        return {"GH": str(program), "FAKE_GH_DATA": str(store)}

    def test_add_creates_the_ledger_and_sets_found(self):
        self.run_script("add", self.ledger, "D1", "defect", 'The "importer"', "drops\ta row")
        row = self.rows()["D1"]
        self.assertEqual((row["title"], row["kind"]), ('The "importer" drops a row', "defect"))
        self.assertRegex(row["found"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")
        self.assertEqual((row["started"], row["landed"]), ("", ""))

    def test_add_twice_leaves_the_row_alone(self):
        self.run_script("add", self.ledger, "D1", "defect", "First")
        before = self.ledger.read_text()
        done = self.run_script("add", self.ledger, "D1", "feature", "Second")
        self.assertIn("already in the ledger", done.stdout)
        self.assertEqual(self.ledger.read_text(), before)

    def test_add_refuses_a_kind_outside_the_set(self):
        done = self.run_script("add", self.ledger, "D1", "chore", "Tidy", expect=2)
        self.assertIn("broken-build", done.stderr)

    def test_start_sets_started_once(self):
        self.run_script("add", self.ledger, "D1", "defect", "One")
        self.run_script("start", self.ledger, "D1")
        first = self.rows()["D1"]["started"]
        self.assertTrue(first)
        done = self.run_script("start", self.ledger, "D1")
        self.assertIn("already started", done.stdout)
        self.assertEqual(self.rows()["D1"]["started"], first)

    def test_start_names_the_ids_when_the_row_is_missing(self):
        self.run_script("add", self.ledger, "D1", "defect", "One")
        done = self.run_script("start", self.ledger, "D9", expect=3)
        self.assertIn("D1", done.stderr)

    def test_land_takes_the_time_from_the_commit(self):
        repo, sha = self.repository()
        self.ledger.parent.mkdir(parents=True)
        self.ledger.write_text(HEADER + "\nD1\tOne\tdefect\t2026-03-01T00:00:00Z\t2026-03-02T00:00:00Z\t\t\t\n")
        self.run_script("land", self.ledger, "D1", sha, "--repo", repo)
        row = self.rows()["D1"]
        self.assertEqual(row["landed"], "2026-03-04T04:06:07Z")
        self.assertEqual(row["commits"], sha[:len(row["commits"])])
        self.assertEqual(row["started"], "2026-03-02T00:00:00Z")

    def test_land_moves_a_start_recorded_after_the_commit(self):
        repo, sha = self.repository()
        self.ledger.parent.mkdir(parents=True)
        self.ledger.write_text(HEADER + "\nD1\tOne\tdefect\t2026-03-01T00:00:00Z\t2026-03-05T00:00:00Z\t\t\t\n")
        self.run_script("land", self.ledger, "D1", sha, "--repo", repo)
        row = self.rows()["D1"]
        self.assertEqual(row["started"], row["landed"])
        self.assertIn("approx", row["note"])

    def test_land_refuses_a_commit_older_than_the_item_and_changes_nothing(self):
        repo, sha = self.repository()
        self.run_script("add", self.ledger, "D1", "defect", "Found today")
        before = self.ledger.read_text()
        done = self.run_script("land", self.ledger, "D1", sha, "--repo", repo, expect=3)
        self.assertIn("can't land before it was found", done.stderr)
        self.assertEqual(self.ledger.read_text(), before)

    def test_add_takes_a_found_time_for_an_item_logged_afterwards(self):
        repo, sha = self.repository()
        self.run_script("add", self.ledger, "D1", "defect", "Logged late", "--found", "2026-03-01T00:00:00+01:00")
        row = self.rows()["D1"]
        self.assertEqual(row["found"], "2026-02-28T23:00:00Z")
        self.assertIn("approx", row["note"])
        self.run_script("land", self.ledger, "D1", sha, "--repo", repo)
        self.run_script("add", self.ledger, "D2", "defect", "Bad", "--found", "yesterday", expect=2)

    def test_land_fails_plainly_for_an_unknown_commit(self):
        repo, _ = self.repository()
        self.run_script("add", self.ledger, "D1", "defect", "One")
        done = self.run_script("land", self.ledger, "D1", "0000000", "--repo", repo, expect=1)
        self.assertIn("reading the commit", done.stderr)

    def test_drop_lands_the_item_with_its_reason(self):
        self.run_script("add", self.ledger, "D1", "defect", "One")
        self.run_script("drop", self.ledger, "D1", "--note", "not worth doing")
        row = self.rows()["D1"]
        self.assertTrue(row["landed"])
        self.assertIn("dropped: not worth doing", row["note"])

    def test_sync_adds_issues_lands_closed_ones_and_skips_questions(self):
        env = self.gh({
            "issues": {"o/app": [
                issue(1, "Open one", ["defect"]),
                issue(2, "Closed by a commit", ["bug"], closed="2026-01-09T00:00:00Z"),
                issue(3, "For the maintainer", ["question"]),
                issue(4, "Closed by hand", closed="2026-01-05T00:00:00Z", reason="NOT_PLANNED"),
            ]},
            "timelines": {
                "repos/o/app/issues/2/timeline": [
                    {"event": "assigned", "created_at": "2026-01-02T00:00:00Z"},
                    {"event": "closed", "commit_id": "abcdef1234567890", "created_at": "2026-01-09T00:00:00Z"}],
                "repos/o/app/issues/4/timeline": [{"event": "closed", "commit_id": None}],
            },
            "commits": {"repos/o/app/commits/abcdef1234567890": "2026-01-08T12:00:00Z"},
        })
        done = self.run_script("sync", self.ledger, "o/app", env=env)
        self.assertIn("3 added, 2 landed, 0 reopened, 1 questions left out", done.stdout)
        rows = self.rows()
        self.assertEqual(sorted(rows), ["app#1", "app#2", "app#4"])
        self.assertEqual((rows["app#1"]["kind"], rows["app#1"]["started"], rows["app#1"]["landed"]), ("defect", "", ""))
        self.assertEqual(rows["app#2"]["kind"], "defect")
        self.assertEqual(rows["app#2"]["started"], "2026-01-02T00:00:00Z")
        self.assertEqual((rows["app#2"]["landed"], rows["app#2"]["commits"]), ("2026-01-08T12:00:00Z", "abcdef12"))
        self.assertEqual(rows["app#4"]["started"], rows["app#4"]["landed"])
        self.assertIn("dropped", rows["app#4"]["note"])

    def test_sync_keeps_a_start_recorded_by_hand_and_runs_twice_without_change(self):
        data = {"issues": {"o/app": [issue(1, "One")]}, "timelines": {}, "commits": {}}
        env = self.gh(data)
        self.run_script("sync", self.ledger, "o/app", env=env)
        self.run_script("start", self.ledger, "app#1")
        started = self.rows()["app#1"]["started"]
        data["issues"]["o/app"] = [issue(1, "One", closed="2026-12-31T00:00:00Z")]
        data["timelines"]["repos/o/app/issues/1/timeline"] = [{"event": "closed", "commit_id": "feedface00000000"}]
        data["commits"]["repos/o/app/commits/feedface00000000"] = "2026-12-30T00:00:00Z"
        env = self.gh(data)
        self.run_script("sync", self.ledger, "o/app", env=env)
        self.assertEqual(self.rows()["app#1"]["started"], started)
        self.assertEqual(self.rows()["app#1"]["landed"], "2026-12-30T00:00:00Z")
        before = self.ledger.read_text()
        self.run_script("sync", self.ledger, "o/app", env=env)
        self.assertEqual(self.ledger.read_text(), before)

    def test_sync_takes_an_open_issues_start_from_its_assignment(self):
        env = self.gh({
            "issues": {"o/app": [issue(1, "Assigned", assignees=["someone"]), issue(2, "Not assigned")]},
            "timelines": {"repos/o/app/issues/1/timeline": [{"event": "assigned", "created_at": "2026-01-02T00:00:00Z"}]},
            "commits": {},
        })
        self.run_script("sync", self.ledger, "o/app", env=env)
        rows = self.rows()
        self.assertEqual(rows["app#1"]["started"], "2026-01-02T00:00:00Z")
        self.assertEqual(rows["app#2"]["started"], "")

    def test_sync_lands_at_the_close_when_the_closing_commit_is_older_than_the_issue(self):
        env = self.gh({
            "issues": {"o/app": [issue(1, "Filed after the fix", opened="2026-02-01T00:00:00Z", closed="2026-02-02T00:00:00Z")]},
            "timelines": {"repos/o/app/issues/1/timeline": [{"event": "closed", "commit_id": "0ld0ld0ld0ld0ld0"}]},
            "commits": {"repos/o/app/commits/0ld0ld0ld0ld0ld0": "2026-01-15T00:00:00Z"},
        })
        self.run_script("sync", self.ledger, "o/app", env=env)
        row = self.rows()["app#1"]
        self.assertEqual((row["started"], row["landed"]), ("2026-02-02T00:00:00Z", "2026-02-02T00:00:00Z"))
        self.assertIn("approx", row["note"])
        done = subprocess.run([sys.executable, str(CFD), str(self.ledger), "--json"], capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)

    def test_sync_clears_the_landing_of_a_reopened_issue(self):
        self.ledger.parent.mkdir(parents=True)
        self.ledger.write_text(HEADER + "\napp#1\tOne\tfeature\t2026-01-01T00:00:00Z\t2026-01-02T00:00:00Z\t2026-01-03T00:00:00Z\tabc\t\n")
        env = self.gh({"issues": {"o/app": [issue(1, "One")]}, "timelines": {}, "commits": {}})
        done = self.run_script("sync", self.ledger, "o/app", env=env)
        self.assertIn("1 reopened", done.stdout)
        self.assertEqual((self.rows()["app#1"]["landed"], self.rows()["app#1"]["commits"]), ("", ""))

    def test_sync_says_what_failed_when_the_github_cli_is_missing(self):
        done = self.run_script("sync", self.ledger, "o/app", env={"GH": str(self.folder / "absent")}, expect=1)
        self.assertIn("listing the issues failed", done.stderr)

    def test_cfd_draws_what_the_ledger_commands_wrote(self):
        repo, sha = self.repository()
        self.ledger.parent.mkdir(parents=True)
        self.ledger.write_text(HEADER + "\nD1\tOne\tdefect\t2026-03-01T00:00:00Z\t\t\t\t\n")
        self.run_script("start", self.ledger, "D1")
        self.run_script("land", self.ledger, "D1", sha, "--repo", repo)
        self.run_script("add", self.ledger, "D2", "feature", "Two")
        done = subprocess.run([sys.executable, str(CFD), str(self.ledger), "--json"], capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("light-dark(", (self.ledger.parent / "cfd.svg").read_text())


if __name__ == "__main__":
    unittest.main()
