#!/usr/bin/env python3
"""Runs one agent-orchestration eval in a fresh headless Claude Code session,
stops it at the first decisive tool call, and grades it.

Usage:
  python3 run.py --eval ID --setup NAME --skill DIR|none --trial N --out DIR [--model M]

The session starts in a fresh copy of the fixture, with the Skill tool
disabled and the skill given by path in the prompt (or no skill with
--skill none). It may read, search, look at git, and spawn agents; any other
tool call it makes is recorded and denied. The run stops at the first spawn
(the orchestrator delegated), at the first edit, write, test run, or git
change (the orchestrator did the work), when the session ends, or after 25
tool calls. Writes DIR/run.json with the decision, the tool calls, the first
spawn's prompt, tokens, duration, and each assertion's PASS or FAIL.

Exit codes: 0 the run finished and was graded; 2 bad arguments.
"""
import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
CAP = 25
WORK_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
SPAWN_TOOLS = {"Agent", "Task"}
# A shell command that runs the project's code or changes files or git.
WORK_BASH = re.compile(
    r"\bpython3?\b|\bpytest\b|\bunittest\b|\bsed\s+-i|\bperl\s+-[a-z]*i|"
    r"\bgit\s+(commit|push|apply|checkout|reset|revert|add|rebase|merge|cherry-pick|restore)\b|"
    r"(^|[^0-9&>])>(?!&)|\btee\b|\bmv\b|\brm\b|\bcp\b|\btouch\b|\bpatch\b"
)
ALLOWED = ["Read", "Grep", "Glob", "Agent", "Task",
           "Bash(git log:*)", "Bash(git show:*)", "Bash(git status:*)",
           "Bash(git diff:*)", "Bash(cat:*)", "Bash(ls:*)", "Bash(grep:*)"]


def classify(name, tool_input):
    if name in SPAWN_TOOLS:
        return "spawn"
    if name in WORK_TOOLS:
        return "work"
    if name == "Bash" and WORK_BASH.search(tool_input.get("command", "")):
        return "work"
    return "look"


def main():
    p = argparse.ArgumentParser(prog="python3 run.py", description=__doc__.splitlines()[0])
    p.add_argument("--eval", required=True)
    p.add_argument("--setup", required=True)
    p.add_argument("--skill", required=True, help="skill folder, or none")
    p.add_argument("--trial", type=int, required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--model", default="claude-opus-5-5")
    a = p.parse_args()

    spec = json.load(open(os.path.join(HERE, "evals.json")))
    ev = next((e for e in spec["evals"] if e["id"] == a.eval), None)
    if ev is None:
        p.error(f"--eval must be one of: {', '.join(e['id'] for e in spec['evals'])}. Received: {a.eval!r}")

    run_dir = os.path.abspath(a.out)
    if os.path.exists(run_dir):
        shutil.rmtree(run_dir)
    os.makedirs(run_dir)
    fixture = os.path.join(run_dir, "fixture")
    subprocess.run(["sh", os.path.join(HERE, "files", "make_fixture.sh"), fixture, ev["fixture"]], check=True)
    work = os.path.join(fixture, "work")

    if a.skill == "none":
        skill_line, add_dir = "", []
    else:
        skill = os.path.abspath(a.skill)
        skill_line, add_dir = spec["skill_line"].format(skill=skill), ["--add-dir", skill]
    prompt = ev["prompt"].replace("{skill_line}", skill_line)

    cmd = ["claude", "-p", prompt, "--model", a.model, "--output-format", "stream-json", "--verbose",
           "--disallowedTools", "Skill", "--strict-mcp-config", "--setting-sources", "project",
           "--allowedTools", *ALLOWED, *add_dir]
    start = time.time()
    proc = subprocess.Popen(cmd, cwd=work, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                            stdin=subprocess.DEVNULL, text=True, start_new_session=True)
    calls, decision, spawn_prompt, final, usage = [], None, None, "", {}
    transcript = open(os.path.join(run_dir, "stream.jsonl"), "w")
    for line in proc.stdout:
        transcript.write(line)
        try:
            msg = json.loads(line)
        except ValueError:
            continue
        if msg.get("type") == "assistant" and not msg.get("parent_tool_use_id"):
            usage = msg["message"].get("usage", usage)
            for block in msg["message"].get("content", []):
                if block.get("type") != "tool_use":
                    continue
                kind = classify(block["name"], block.get("input", {}))
                calls.append({"tool": block["name"], "kind": kind,
                              "input": json.dumps(block.get("input", {}))[:300]})
                if kind == "spawn" and decision is None:
                    decision, spawn_prompt = "delegated", block["input"].get("prompt", "")
                elif kind == "work" and decision is None:
                    decision = "did_work"
            if decision or len(calls) >= CAP:
                break
        elif msg.get("type") == "result":
            final, usage = msg.get("result", ""), msg.get("usage", usage)
            decision = decision or "ended"
            break
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    proc.wait()
    transcript.close()
    decision = decision or "capped"

    looks = next((i for i, c in enumerate(calls) if c["kind"] != "look"), len(calls))
    spawned = decision == "delegated"
    grades = []
    for text in ev["assertions"]:
        if "does no work" in text:
            ok = decision != "did_work"
        elif "spawns an agent" in text:
            ok = spawned
        elif "spawns no agent" in text:
            ok = not spawned
        elif "briefed on the red trunk" in text:
            ok = spawned and bool(re.search(r"red|fail|test_title|ci/trunk", spawn_prompt or "", re.I))
        elif "At most 8 tool calls" in text:
            ok = spawned and looks <= 8
        elif "says 2" in text:
            ok = decision == "ended" and bool(re.search(r"\b(2|two)\b", final, re.I))
        else:
            raise SystemExit(f"no grader for assertion: {text}")
        grades.append({"text": text, "passed": ok})

    record = {"eval": a.eval, "setup": a.setup, "trial": a.trial, "model": a.model, "decision": decision,
              "calls_before_decision": looks, "calls": calls, "spawn_prompt": spawn_prompt, "final": final[:2000],
              "duration_ms": int((time.time() - start) * 1000), "usage": usage, "assertions": grades}
    json.dump(record, open(os.path.join(run_dir, "run.json"), "w"), indent=2)
    shutil.rmtree(fixture, ignore_errors=True)
    print(f"{a.eval}\t{a.setup}\t{a.trial}\t{decision}\tlooks={looks}\t"
          f"pass={sum(g['passed'] for g in grades)}/{len(grades)}")


if __name__ == "__main__":
    sys.exit(main())
