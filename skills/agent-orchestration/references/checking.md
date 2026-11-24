# Checking agents

Agents report "done" with gaps, and report "waiting" while idle. Read every report critically, and look at the evidence yourself before passing anything on.

## What to check

- **Its commits and runs, not its report.** A sub-agent whose context fills can freeze mid-task. When one has stopped answering, start a fresh agent from its state file, commits, and runs rather than wait for its report. Size short of that is no reason to replace it.
- **Its actual activity:** the processes it started, the runs it queued on shared machines, changes in its working copy and scratch folders, and its unpushed commits. A status line says nothing about these. Look in all of its places before concluding it's idle; work outside its working copy is easy to miss.
- **What it ran, from its tool calls,** not from a search of its transcript. A transcript holds every file the agent read, so a search for a forbidden flag finds the rule that forbids it. When a harness flags an agent, list the commands it ran.
- **Its claims of proof:** which checks ran, on which machine, against which commit. "The hook passed" means nothing if the hook silently ran nothing. Have an agent test that a failing check actually blocks. When an agent says a commit wasn't checked alone, or that it didn't see the whole output, brief another agent to run the check on that commit and revert it if it fails; a gate that passes on Linux can still fail on macOS, so a green gate on one machine proves only that machine. A build that reused output whose inputs changed, such as a warm workspace that did not rebuild, proves nothing about this commit; a build much faster than its kind is the tell.
- **Its commits' metadata,** with a command, not by eye: trailers, authorship lines, and that each commit sits on the trunk you expect. A trailer separated by a blank line isn't a trailer.
- **Work done to a standard** (a skill, a style guide, a format): read a sample in full yourself, and for large changes have a second agent that wrote none of it review the result against that standard, given the state before and after, and told not to defend the work. A document of record is read whole, not sampled, as SKILL.md says.
- **Its reading of a run's output:** check the totals a test runner prints (runs, failures, errors, skips) before believing a list of failures. Skips and failures can print in the same form, and one agent reported a dozen skips as failures.
- **What it left unverified:** tests skipped because a machine was busy, holes "left open on purpose", platforms "not yet run". Say so to the user plainly.
- **Images and output** at full size, yourself.
- **Its leftovers:** processes, folders on shared machines, branches, and device sessions. Before anything is deleted, check it for unpushed work, check that no process is still working in it, and archive what isn't safe elsewhere. Delete your own agents' folders when their work is done; deleting anything else on a shared machine is the user's call, or its owner's.

## Anchoring

Agents patch their first draft rather than rethink it, and defend earlier work when challenged; a long chain of corrections compounds both. When a design is wrong at the root, a fresh agent with one clean brief, or a cold review by a second agent given the code rather than your conclusion, beats another correction.

## Briefing a reviewer

A review is only as independent as its brief.

- **Say who is briefing.** When the agent that made the work, or commissioned it, also briefs its reviewer, the brief says so, and says what part that agent played in each thing under review.
- **The standard comes from the user or the project's rules,** in their words. A maker's own summary of the standard grades the work against its own instructions.
- **Describe the pieces of work evenly.** "Written alone" beside "written with the user, following a named method" tilts the reviewer before it reads either.
- **Agreement between agents that share a source is one finding, not two.** Agents briefed by the same agent, or running the same model over the same files, repeat each other. Have the agreed claims checked as well as the disputed ones.

## Mistakes of the orchestrator's own

Own them plainly, with what changes so they don't recur: a brief clause, a skill edit, a check. The user cares about the fix, not the apology.
