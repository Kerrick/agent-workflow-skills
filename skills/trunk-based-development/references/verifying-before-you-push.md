# Verifying before you push

Matters most before any push your workstation can't fully check, when you send work to other machines, when a result looks wrong, and when the build machines can't be reached.

## Before you leave a check for after the push

When a check needs something your workstation lacks, such as another operating system, a GPU, or a service you can't run, you'll want to call it something only CI can show, push, and report it as unverified on those systems. If you can run on machines beyond your workstation, first give it a short trial there. A limit nobody has tried is not a limit. Neither is one that someone could lift in a few minutes by installing a tool, logging in, or approving a runner: ask for that step instead of deferring the check. If, after all that, a check really has no home before the push, make it part of the automation every push passes through, a merge queue or pull-request job, rather than something you trigger by hand; don't wait for it, let full trunk CI run as usual afterwards, and revert straight away if the trunk goes red. Whatever is still unverified, report as unverified and give the reason; never describe it as something only CI could show.

Your habit is to use only your workstation unless someone tells you otherwise. If the repository or the user's instructions mention build machines you haven't been told how to use, ask the user once; otherwise use your workstation. Before pushing, any remote machine you control may cover a system, runtime version, or hardware your workstation lacks, or split the suite across machines, so that you never push just to learn a result.

If you can run on machines beyond your workstation, those runs are yours alone, not part of shared CI, and they start from a switch in the normal build script, not from a separate workflow that only CI runs. When you set this up, put the switch in the build script and tell every agent about it; without it, agents fall back on push-and-poll.

## Sending work to shared build machines

If your project shares build machines among agents, every request runs one check, on whichever machine is free. You'll want to send each commit's complete build to every operating system and wait for all of them, which feels thorough; it backs the machines up until every agent is waiting. Name a particular system only for something that exists on it alone, such as code that runs only on that system or a failure seen only there. When a change touches system-specific code for more than one system, send each system its own request carrying only its part. Never run the same check on a second system to be sure, never rerun hoping for a different result, and never push a branch to find out. The limit is per request, so checking a second, different thing is a new request and is allowed.

For example, a change edits a shared config parser and the Windows and macOS clipboard backends. The parser's tests run once, on any machine. The Windows backend's tests run on Windows and the macOS backend's tests on macOS, each as its own run, and nothing goes to every system wholesale.

When a check that should pass everywhere fails on one system, it has found a defect, and fixing that defect is the project's job. Never respond by sending the check only to systems where it passes.

If you can run on machines beyond your workstation, the same rule applies there. Let Test Impact Analysis choose the tests; send them to a system you lack only when the change or the failure is specific to that system, and run anything any system can show once, on whichever machine is free. Never run the whole suite on each system.

## Trusting a result

A build that reused outputs whose inputs had changed proves nothing about the current commit: a workspace that skipped a rebuild, or a cache key that leaves out a dependency, can hand back an earlier commit's result, green or red. If a build finishes far faster than builds of its kind usually do, rebuild from clean before you trust it either way.

## When the build machines are unreachable

If you normally verify on machines beyond your workstation and they are down, you'll want to stop landing work until they're back, which feels like caution. Stopping piles verified work up unpushed and widens every agent's distance from the trunk for as long as the outage lasts. Run whatever your workstation can, push when that passes, and keep working, with post-push CI and quick reverts covering the rest. Don't push branches to have checks run somewhere else. This holds only while the machines are unreachable: the workstation part of the gate still runs, and a gate that is merely slow never qualifies.

## Choosing the tests

Never pick the tests by guessing from the diff. The diff doesn't show dependencies that never appear as direct references in its text, so breakage through those paths slips past.

An agent can write a test that passes whether or not the code works, so check agent-written tests objectively: confirm each new test fails on the parent commit, and run mutation testing.

Use coverage data to link each test to the source files it executes. Before pushing, run only the tests linked to the files you changed, and let CI run all of them. Rebuild the map periodically, daily or after a set number of commits; CI catches whatever a stale map misses. Until a project has a map or a tier, use the selection its test runner already offers, which follows the dependency graph from the files you changed (`jest --findRelatedTests <files>`, `vitest related <files> --run`), together with the compile or type check; that counts as impact analysis. Fall back to the full suite before the push only when no runner offers such selection, and in both cases report the slow gate as a fault to fix.

Sort tests by cost, cheapest first: compiling and in-memory unit tests lead, and tests that cross a process or network boundary should be rare and rewritten as in-memory tests where they can be. Before the push, run the smoke tier. CI runs the whole suite, and the longest-running suites run on a schedule rather than for every commit.
