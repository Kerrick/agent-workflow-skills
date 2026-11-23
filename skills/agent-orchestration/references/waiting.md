# Waiting without blocking

Ask of every agent that is waiting: **"if this passes, is the agent completely done?"** If not, it shouldn't be waiting. It should be doing the rest.

## The two failure modes

- **Polling:** an agent wakes every minute to check a run, and each wake costs tokens twice, its own and the orchestrator's notification. The fix is not to block.
- **Blocking:** an agent sits inside one long wait. It does nothing meanwhile, and it cannot hear messages until the wait ends, which on a shared CI queue can be hours. An orchestrator can't redirect it, only stop it.

The cure for both: **start the wait in the background,** so its end notifies the agent, and **carry on optimistically** with every piece of work that doesn't depend on the result. If the result comes back red, revert first, then fix.

A message to a blocked agent waits until its current tool call ends. To reach it sooner, end what it is waiting on: cancel a CI run nobody needs any more, and the wait returns. Stopping the agent loses its context, so check its working copy for unpushed work first.

## Work that fills a wait

- Docs, changelog entries, and the next commit, on top of at most the one being proven. A deeper stack means the build is too slow: fix the build.
- Proof on private machines or devices that doesn't need the result.
- Investigating an anomaly the run's early jobs already show.
- Preparing the landing: rebasing, the commit message, the report.

## Waits that aren't legitimate at all

- **A push made to find out whether CI passes,** on any branch. Check the change yourself first, with the narrow check its brief names. The full build is CI's, on the trunk, after the push, with a red trunk reverted at once; a branch pushed to try it holds proven work back and starves the trunk's own runs.
- **Runs made to see what happens.** Firing a build or gate with no hypothesis, rerunning without reading the log, or pushing to let a hook find out wastes a shared pool the way push-and-poll wastes CI. When debugging, state the hypothesis and run the narrowest check that tests it (one test, one step). Before a push, run the project's build once, and on a named system only what is that system's own; then push and carry on. Checks can run in the background while the agent carries on; only the run before a push has to be waited for.
- **A fix pushed for a failure nobody has reproduced.** It is a push made to find out, with the red trunk as the test bench. A failure that shows on one system is reproduced on that system, on the user's machines, and the fix proven there; if that can't be done within minutes, the breaking commit is reverted.
- **A branch run kept alive after nobody needs it.** On a shared queue it starves the trunk's own runs.
- **Waiting for the trunk to go quiet.** Releases pick a proven commit wherever the trunk is.

## When shared machines fail

A queue that is down, a node that is away, a disk that is full: none of it is for each agent to wait out or retry into on its own. Every retry is a run that fails for a reason outside the change, and every agent told of the failure pays its whole context to hear it. One change was pushed eight times in an evening, against a stray file, a dead queue, and a node that had lost its tools, and none of the eight landed.

- **Agents stop.** The brief's stop rule covers it: write the state down, report once, don't retry.
- **One watcher waits:** a bounded background check of the orchestrator's own. It calls the machines back only after several answers in a row. One orchestrator called a queue back on a single answer and woke three agents into a dead one.
- **Tell the user what is waiting, and ask how to go on.** Whether to push without the machines, with CI as the check, is the user's to say, and it holds only for what they name and while the machines are down.
- **Then the orchestrator restarts the work:** it pushes a commit an agent left proven, as SKILL.md's one exception allows, and briefs fresh agents for the rest.

## Work that must happen on schedule

Something that must happen at a time, whether or not anyone is at a keyboard (keeping a file upstream replaces nightly, a nightly check), never depends on the user's computer, its cron, or a session's own scheduler: the user clears them, sessions end, and laptops sleep. Put it in the project's CI as a scheduled job, which runs, logs, and alerts without anyone's machine. A session's scheduler is a stopgap until that job has run once.

## A wait is not what keeps the orchestrator working

A background wait that ends may not wake an orchestrator whose user is away: one waited five hours on a watcher that had finished, while the run it needed sat green and unread, with a queue of open work and most of its budget unspent. An agent's report does wake it. So while the user is away and work is open, keep agents in flight; watch each run that matters with its own wait, named for the run and not for "the next one"; and never stop starting work to save context for a report. An agent that sets a monitor on something its orchestrator is already watching is woken by it again and again at the price of its whole context: tell agents to set none.

## Every background job is bounded

Give every background job a hard timeout. A run that hangs never calls back, and a forgotten loop burns a machine for days; one `pgrep` loop matched its own command line and slept for 66 hours. Kill the actual process, not a wrapper subshell: a killed wrapper once left a device tool attached to a phone for nine minutes.
