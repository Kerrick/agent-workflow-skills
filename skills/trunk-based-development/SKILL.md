---
name: trunk-based-development
description: >-
  Use whenever you are about to commit, push, land, merge, or wrap up a change,
  and whenever the user says "commit this", "push it", "land this", or "is CI
  green yet?", or says "ship it" or "wrap up", which mean land on the trunk, not
  release; even if nobody says "trunk": choosing a branch, pull request, or
  worktree; the build before a push; CI or a pre-push build that is red, slow,
  or still running; tempted to wait on CI or a build machine, push a branch to
  test it, or hold, batch, or order other agents' pushes; a red trunk; a
  release, tag, or release branch; or orchestrating sub-agents that commit: how
  their work lands and what their briefs must say. Anyone who will commit, push,
  or integrate must first open and read every file in references/ by path;
  loading the skill brings in this page only. Someone only learning the practice
  reads this page alone. Not for the rest of briefing, choosing models, or
  keeping agents busy (use agent-orchestration), or for progress reports (use
  cumulative-flow).
license: CC0-1.0
metadata:
  author: Kerrick's AI Agent(s)
  version: "2.1"
---

# Trunk-based development

You already know trunk-based development: one trunk, small commits, a green build, short branches or none. This skill adds rules for every committer, people and agents alike, and several of them overturn advice you would normally follow, such as watching CI after a push or having an orchestrator integrate its sub-agents' work. Where a rule here conflicts with your habits or with general guidance, follow the rule here.

## Who reads what

**If you will commit, push, or integrate,** open every file under [References](#references) and read each one to the end before your first commit. Loading the skill brought in this page only, and the rules agents break most often, such as sitting idle until a build reports back, are spelled out in the references. If the skill is edited during your session, read every file again before your next commit.

**If you are briefing an agent that will commit,** name this skill in the brief, give the path of every reference file, and tell the agent to read each one completely. A brief that says only "use the skill", or that points only at the repository's rules file, isn't enough: the agent works from this page alone, then waits on CI or asks how to land work it has already verified.

**If you are only learning the practice or answering a question about it,** read this page and stop. The references would fill your context with rules you won't use.

Treat trunk-based development as how the whole project works, for every contributor and for every agent each contributor runs. When you sort rules into shared and private files, the trunk rules and the multi-agent rules go in the project's shared rules; a private file holds only the details of one person's machines and accounts. Filed as one maintainer's habit, the rules vanish from other contributors' agents, and the project ends up with one person committing to the trunk while everyone else waits on pull requests.

### References

- [references/verifying-before-you-push.md](references/verifying-before-you-push.md): what the gate runs, other machines you can use, shared build machines if your project has them, results you can't trust, and what to do when the build machines are down. Matters most before any push your workstation can't fully check.
- [references/when-the-trunk-is-red-or-stuck.md](references/when-the-trunk-is-red-or-stuck.md): reverting a breaking commit, a failure on one system only, flaky tests, and trunk runs that never finish. Matters the moment the trunk breaks, whoever broke it.
- [references/choosing-branches-and-worktrees.md](references/choosing-branches-and-worktrees.md): when a branch or pull request is allowed at all, the two-day ceiling, one writer per branch, merging versus rebasing a published branch, how many worktrees you may hold, and removing them. Matters before you make a branch, a pull request, or a worktree.
- [references/coordinating-with-others.md](references/coordinating-with-others.md): a change that departs from a recorded decision, warning others before you change what they depend on, how a team of agents lands its work, and sharing a machine. Matters to every agent that commits to the trunk, whether it works alone or beside others.
- [references/reviewing-agent-changes.md](references/reviewing-agent-changes.md): independent review after landing, an AI reviewer reading first, and people overseeing the system rather than each change. Matters before you review anything or set up review.
- [references/speeding-up-the-build-and-setting-up-ci.md](references/speeding-up-the-build-and-setting-up-ci.md): build-time targets, test stand-ins, impact analysis, caching, sharding, trunk CI, and the commit queue. Matters when the gate drifts past about a minute or someone configures CI.
- [references/releasing.md](references/releasing.md): who may ship, tagging without a release commit, release automation, the changelog after a tag, fixing a shipped release, cherry-picks, patch releases, and release branches. Matters before any work on releases, tags, or release branches.

## The loop every commit follows

Go round this loop many times a day:

1. `git fetch`, then `git rebase origin/<trunk>`, which puts your unpublished local commits on top of the trunk.
2. Make one small change that keeps every check green and could ship on its own.
3. Run the gate, described below.
4. Sync once more, push straight to the trunk, and start the next change. The change is done when it is pushed; CI then runs the complete build on the trunk.

**The gate is CI's own build script, cut down to about a minute.** It compiles, runs pure unit tests, and runs the tests that a test tier or Test Impact Analysis says your change could affect. If you can run on machines beyond your workstation, affected tests go to one running a system you lack only when the change, or a failure, is specific to that system; anything any system can show runs once, wherever is free. Your default will be lint, a typecheck, and the tests you judge to be near the change. Never invent a separate, lighter build, and never choose tests by reading the diff: the diff hides what the change reaches indirectly. If the project has no tier and no coverage map yet, let the tooling select by impact: the test runner's own dependency-graph selection, such as `jest --findRelatedTests <files>` or `vitest related <files> --run`, plus the compile or type check. That is impact analysis, not choosing by eye. Only when no such tool-based selection exists do you run the full suite before the push. Either way, report the slow gate as a fault to fix, and don't start building a tier or map in the middle of your task. After the push, or before landing where a merge queue exists, the same build runs in full on every platform and every slow tier, catching what a one-minute gate can't. The gate must be quick and pass reliably, here and in CI alike; when it doesn't, that is a defect to fix, never a reason to push less checked work.

**After the push, wait for nothing.** You'll want to watch the CI run, offer to watch it, or count yourself done only when it turns green. Barred from that, you'll want to send the project's full multi-platform build to build machines for every commit and wait for it instead. Both are push-and-poll, a loop that hands your work to someone else's build to learn whether you are finished and then idles, and both are banned. The verification you are reaching for belongs before the push: your gate, including, where you have other machines, affected tests on a system you lack when the change is specific to it, and waiting for those runs is part of the gate. Once pushed, move on to the next change. If the trunk turns red, that is handled as a red trunk, by whoever sees it. When the user asks whether CI is green, check once and report what you find; if it's red, handle it as a red trunk. Never start watching or polling.

**When a push is refused because the trunk moved,** rebase, run the gate again, and push again, every time. You'll be inclined to skip the rerun when the incoming commits look unrelated to yours, and that judgment is exactly what a semantic clash slips past: two changes can merge without a textual conflict and still break each other's behavior. Only tests that exercise both changes together catch that, so keep coverage strong wherever different agents' changes touch the same behavior. When the rebase stops on a conflict, understand the other change before you resolve it.

**Keep every push releasable.** The trunk is green and shippable at every moment. When a change needs several commits, hide it behind a feature flag or build it by branch by abstraction, so that each push is safe to release even when the goal takes days. Don't gather a story into one landing: land it as a run of small commits, interleaving refactors with slices of the feature. Integrate continuously, because work held off the trunk grows riskier the longer it waits: conflicts, duplicated effort, and silent incompatibilities pile up where nobody sees them, and more agents only raise the stakes. Shipping means tagging a commit CI has verified, or, for teams that ship rarely, releasing from a release branch; agents do neither unless the repository's rules allow it (see [releasing](references/releasing.md)).

## Every agent lands its own work, and nobody stops the line

**Each agent pushes what it wrote.** As an orchestrator you'll want sub-agents to hand you their verified commits so you can integrate them one at a time, and it will feel like the careful way to guard the trunk. The trunk stays green through each agent's gate and its rebase-and-rerun; a single integrator adds no check, and makes every agent wait on you. Ordering commits is work for an automated service, never for an orchestrator. Where no automated queue exists, every agent pushes its own commits as soon as its gate is green, rebasing and checking again when the push is refused. A brief counts the task done only after the agent has pushed and then reported. Never collect commits to land them yourself, even if a rule about commit queues seems to describe you. If the permission system refuses a sub-agent's push to the trunk, tell the user at once and quote the exact command, so they can add an allow rule; don't take over the pushing.

One developer running several agents, each in its own working copy, with no pull request required, is ordinary trunk-based development with more committers: the agents commit straight to the trunk, not to a branch and pull request apiece.

**Each agent's worktree is a short-lived branch,** and every branch rule applies to it. Keep each agent's change small and have the agent land it on the trunk within minutes; the other agents pick it up at their next rebase. Nobody integrates worktrees in sequence on anyone's behalf, and worktrees left by failed attempts are thrown away. The two-day branch limit is a ceiling to stay far below, not a pace to work at.

**Run agents in parallel, even in the same area.** Small steps that land fast make that safe: each agent says which files it is about to change before it changes them, widely used code changes by branch by abstraction, nobody reserves files or fixes a landing order, and whoever lands later rebases. Don't run agents one after another, make open work wait on one proof run, or ask the user which agent should land first. While anything runs or waits, start other independent work instead of ending your turn.

**A slow gate is the defect, not a reason to work around it.** When the gate is slow or the trunk is busy, you'll want to cut corners on landing. Never push untested work because the gate is slow. Never move slow checks to after the push. Never let commits pile up so that a check runs once for all of them. Never set landing windows or ask other agents to stop pushing. Make the tests faster and more reliable instead, with tiers, impact analysis, caching, and parallel runs (see [speeding up the build](references/speeding-up-the-build-and-setting-up-ci.md)). Stopping other people's pushes is a code freeze, whatever the reason, an imminent release and a branch cut included. Cutting a branch is one cheap commit and needs no pause.

## Never

- Never merge another person's or agent's branch or working copy into your work, and as an orchestrator never merge one sub-agent's work into another's or into your own integration. The trunk is the only place work meets: wait until the other work lands, then take it from the trunk. A sideways merge creates a combination no build has ever checked.
- Never disable or remove a test to make the build faster. Quarantining a flaky test with its reason recorded is a separate rule ([red or stuck](references/when-the-trunk-is-red-or-stuck.md)) and doesn't break this one.

## Gotchas

Read these again just before you act. Each names where its full rule lives.

- After pushing you'll want to watch CI, or to send a full multi-platform build to build machines and wait; both are push-and-poll. Push, start the next change, and treat any red as a red trunk. ([The loop](#the-loop-every-commit-follows))
- As an orchestrator you'll want sub-agents to hand you their commits to land; each agent pushes its own work once green, and when permissions refuse a push you quote the command to the user rather than taking over. ([Every agent lands its own work](#every-agent-lands-its-own-work-and-nobody-stops-the-line))
- You'll take the loaded skill as enough; before your first commit, open every reference and read it to the end, and name each reference path in any brief you write. ([Who reads what](#who-reads-what))
- You'll call a check "only CI can show this"; first try it on any machine you can use, or ask for the few minutes' work that would unblock it, and report whatever stays unverified, with the reason. ([verifying](references/verifying-before-you-push.md))
- You'll run the tests you judge near the change; the gate is CI's own build script cut to about a minute, its tests chosen by tier or impact map, or else by the test runner's related-tests selection, and the full suite only when no such tool exists. ([The loop](#the-loop-every-commit-follows))
- When the gate is slow or the trunk is busy, never push untested work, move checks to after the push, batch commits so a check runs once, set landing windows, or ask others to stop pushing; make the gate faster instead. ([Every agent lands its own work](#every-agent-lands-its-own-work-and-nobody-stops-the-line))
- You'll want to land several worktrees one by one on their agents' behalf; each agent lands its own small change within minutes, and the others rebase. ([Every agent lands its own work](#every-agent-lands-its-own-work-and-nobody-stops-the-line))
- You'll want to run agents in turn, park work behind one proof run, or ask the user who lands first; have agents announce their files, reserve nothing, fix no order, and take up other work while anything waits. ([Every agent lands its own work](#every-agent-lands-its-own-work-and-nobody-stops-the-line))
- On a red trunk you'll want to fix forward from the log and push to see; revert first, and prove any fix for a one-system failure on that system before pushing. ([red or stuck](references/when-the-trunk-is-red-or-stuck.md))
- Where build machines are shared, you'll want to send every commit's full build to every operating system; each request runs one check on any free machine, and you name a system only for what exists on it alone. ([verifying](references/verifying-before-you-push.md))
- You'll use only your workstation unless told otherwise; before pushing, any remote machine you control is yours to use, and if the repository or the user mentions build machines you haven't been told how to use, ask once. ([verifying](references/verifying-before-you-push.md))
- After a rebase you'll rerun the gate only when the incoming commits look related; rerun it every time. ([The loop](#the-loop-every-commit-follows))
- When your change departs from a recorded decision, you'll want to hold it for the user; push it and report the deviation, unless the decision is reserved to the project's owner. ([coordinating](references/coordinating-with-others.md))
- You'll hesitate to revert someone else's breaking commit; the build cop or revert job reverts it at once, and where neither exists, you revert it at once and tell its author and the user. Nobody waits on a forward fix. ([red or stuck](references/when-the-trunk-is-red-or-stuck.md))
- You'll rerun a flaky test until it passes; fix it or quarantine it now. ([red or stuck](references/when-the-trunk-is-red-or-stuck.md))
- When the build machines are down, you'll want to stop; run what your workstation can, push when it passes, and keep working. ([verifying](references/verifying-before-you-push.md))
- You'll trust a build that finished far faster than usual; rebuild from clean before you believe it. ([verifying](references/verifying-before-you-push.md))
- When a check fails on one system, you'll want to run it only where it passes; that failure is a defect to fix. ([verifying](references/verifying-before-you-push.md))
- You'll push a branch to see what CI says, or park verified fixes behind a flaky test; a branch is never a CI probe or a store for proven work. ([branches](references/choosing-branches-and-worktrees.md))
- Worktrees are cheap, so you'll tend several at once; hold one in progress per agent session, and if you already hold several, land each as soon as it's green, never in sequence. ([branches](references/choosing-branches-and-worktrees.md))
- As an orchestrator you'll count reading your sub-agents' diffs as their review; review comes after landing, within minutes, from someone independent of both the author and whoever briefed it. ([reviewing](references/reviewing-agent-changes.md))
- Asked for a release, you'll want to tag or publish; unless the repository's rules name you, tag nothing, publish nothing, and cut no release branch, and when the rules say nothing, ask the user. ([releasing](references/releasing.md))
- You'll make a "Release vX.Y.Z" commit before tagging; work out the version from the last tag and the changes since, and let the build stamp it. ([releasing](references/releasing.md))
- You'll make release automation wait until its commit is the tip, or have it commit to the trunk; it tags the latest green commit wherever the trunk has got to. ([releasing](references/releasing.md))
- You'll want to stamp the changelog with a date before tagging, or let it shrink to a single pending list; the dated heading is written afterwards, by automation, and holds only what the tagged commit contained. ([releasing](references/releasing.md))
- When releases stall because no trunk run finishes green, you'll plan around it; fix the builds, the reverts, or the flags instead. ([releasing](references/releasing.md))
- Under pressure from a production bug you'll want to fix the release branch directly; fix it on the trunk first, and go to the release branch first only when the trunk can't reproduce the bug, with the fix brought to the trunk immediately. ([releasing](references/releasing.md))
- Having fixed a production bug, you'll want to cherry-pick it onto the release branch yourself; land it on the trunk and tell the cherry-pick owner which commit is a candidate. ([releasing](references/releasing.md))
- Sorting private rules from shared ones, you'll file the trunk rules as one maintainer's habit; they are the whole project's shared rules. ([Who reads what](#who-reads-what))
- On a question about the practice you'll open every reference, and while working you'll take "this page is enough" as leave to skip them; learners stop at this page, and anyone who commits reads everything. ([Who reads what](#who-reads-what))

For the practice in depth, see [trunkbaseddevelopment.com](https://trunkbaseddevelopment.com/), by Paul Hammant and its contributors.
