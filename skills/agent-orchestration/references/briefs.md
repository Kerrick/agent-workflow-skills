# Briefs

A brief is the only context a sub-agent has, and it taints that context for good: what it presumes, the agent believes. Write it as you would for a capable peer who has seen nothing of the conversation.

## What a brief carries

- **The goal and what done looks like,** all the way to landed: proven, committed, pushed by the agent itself, and reported. A brief that ends at "get CI green", or at "send me the commit", leaves the agent idle at the moment it matters.
- **The skills it works under, by path,** with "read every file in full": the trunk-based-development skill and all its references for anyone who commits. A brief that names only the project's rules leaves the agent to guess how to integrate.
- **What has been ruled out,** and what has already been decided, with the user's exact words where they matter, marked as private to the brief: the agent acts on them and copies them into nothing others can read.
- **Where to read,** by path, rather than retyping what the files say. Name sources by what they say, and only ones the user has endorsed.
- **What to do while anything runs:** "run waits in the background and carry on with everything that doesn't depend on the result."
- **The proof expected:** the project's own build, the one CI runs, kept fast: its tests chosen by tier or impact analysis, not by the agent's guess at what is narrow enough. One request, on whichever system is free, for everything that is not literally one system's own; a named system only for a part that is that system's alone, one request for each such system, each running its own part; never the same check on a second system to be sure, and no rerun to see what happens. Say what is left to CI after the push, and why it cannot run before. A brief that names no check sends unproven work to the trunk. When the change is to something many jobs or systems consume (a tool pin, a setup script, a shared step), the check is of each distinct way it is consumed, found by reading its callers or a map of them, not only the way the change was made for. A convention every fixture must follow becomes a check the fast build runs. A new test is seen failing before it is seen passing.
- **Coordination:** which other agents touch nearby files, so each says what it will touch before it does; nobody sets a landing order, and whoever lands second rebases.
- **The stop rule:** if the trunk is red for a reason that isn't yours, push nothing, say so, and keep working from the last commit the full build passed. A test that fails for no reason of yours is reported at once, to be fixed or quarantined, not retried. If a check fails on something your change does not contain (a file you never made, a machine that can't be reached, a tool that is missing), stop, write your state down, and report once; don't retry into it. Where a tool's own skill or documentation gives a retry rule for its own failures, as the instructions for a project's remote build machines may, follow that rule instead, and stop when it says to stop.
- **Refusals:** "if a tool refuses something that blocks you, message me at once with exactly what was refused, and carry on with what isn't blocked."
- **Decisions:** write no decision record; report each decision the work needs, with every option weighed and its evidence, and each recorded decision or design line the change makes untrue, with the line and proposed text. A technical departure is pushed, and reported. A departure from a decision the project reserves for the user (its public interface, product scope, licensing, or what its rules name) waits for the user's answer before it is pushed.
- **Its own space:** a scratch folder of its own, its own ports, databases, and container names where it runs anything, and no `git stash`, whose one list every worktree of a repository shares. On a shared machine, what a run writes goes in the run's own temporary folder, never in the project's workspace there, where the next push's checks find it.
- **The hard rules,** verbatim: what may never run where, what may never be pushed, published, deleted, or force-pushed, and the form of a command the user's allow rules accept, when they match only a command that starts with the allowed program.
- **The report:** what changed, the evidence, the commit IDs, and what's left.

## What a brief leaves out

- **Your guess at the answer.** "X is the cause" or "Y is the source of truth" sends the agent to confirm it. State the question.
- **Your own nits,** when the brief asks for a principled review: let the review find what matters.
- **A model to imitate** the user hasn't endorsed. It can't be unseen without a restart.
- **Private details the agent doesn't need,** and anything that would leak them into a shared project.
- **A limit you have not tested.** "That machine cannot run X" and "only CI can show this" are believed and never checked, and the agent then pushes to CI to find out. Write "untested: find out with the narrowest run on that system" instead.

## Wording that backfires

- **"Wait with one blocking command"** cures polling and causes blocking. Say "wait in the background".
- **"Don't push"** without saying when it may push leaves finished work stranded. Say what unlocks the push.
- **"Stop early"** when priorities change interrupts work in flight. Say "no new scope" instead.
- **"Run everything everywhere"** queues the same full build many times over. Name the build and one run, and a system only for what is its alone.

## Keeping agents within their context

Long runs exhaust context. Ask agents to keep tool output short (`tail`, `grep`, counts rather than dumps), keep their unpushed work small, and write their state down so a fresh agent can take over mid-task.

Every message to an agent makes it read its whole context again, so an agent's size is the price of each word sent to it. After an outage or a rate limit, resume a small agent with a message: its work is kept, and it is relaunched only if it can't be resumed. An agent that has grown large is not woken for a small errand, a status relay least of all: a commit it left proven is pushed by the orchestrator, and a new task goes to a fresh agent. Work it is in the middle of stays with it. One orchestrator woke three agents of 200,000 to 300,000 tokens six to ten times each, to pass on news of a queue they could do nothing about.
