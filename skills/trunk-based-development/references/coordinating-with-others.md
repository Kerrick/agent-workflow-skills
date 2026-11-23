# Coordinating with others

Matters to every agent that commits to the trunk, alone or beside others: when a change contradicts a recorded decision, before you change something others depend on, when deciding how a team of agents lands work, and when several agents or worktrees share one machine.

## Your change departs from a recorded decision

When your technical change contradicts a decision record, you'll want to stop, leave the change unpushed, and ask the user whether to conform or supersede the record. That feels like respecting the decision, but holding the change protects nothing a revert can't: push it, and report the deviation, without waiting for anyone's permission. The keeper of the decision records reviews it afterwards. A wrong deviation is reverted or sent back for fixing, and a right one gets a new record. Whoever writes the record commits it, and whoever writes the code commits that, each when it's done; never bundle the two into one landing, and never make the code wait for the record. The one exception is a decision the project reserves to its owner: that change waits for the owner before any push.

## Changing something others depend on

When your next edit will ripple into other people's work, say a function signature many callers use or a schema that code is generated from, announce it first to everyone working in the repository, naming what will change and whether they should leave it alone for now. A warning takes seconds; sorting out two agents' clashing rewrites takes far longer. This is a heads-up about one thing, so others avoid conflicting edits to it for a few minutes; it never halts anyone's pushes, and holding off on that thing is their choice.

## Choosing how a team of agents lands work

Don't give agents long-lived branches, not even a branch per worktree landed in turn; every agent lands small changes through the trunk. When agents write faster than review keeps up, speed up review instead of adding branches and pull requests.

Headcount misleads: what sizes a team is how many writers, human or agent, are active at once and how many commits land in its busiest hour. Two people with a dozen agents running are a large team. Such a team is best served by commits straight to the trunk through a commit queue, with AI leading review; without AI-led review, pull requests move the bottleneck onto human reviewers.

Where an automated commit queue exists, handing your change to it is your push. Where none exists, each agent pushes directly. An orchestrator is never the queue.

## Sharing a machine

Where you can, give each agent a machine of its own, so agents share no runtime resources.

Worktrees on one machine share it, so make every runtime resource the app uses configurable and give each running copy its own settings; otherwise two worktrees' runs collide and the failures look like real bugs.
