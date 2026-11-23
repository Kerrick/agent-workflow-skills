# Choosing branches and worktrees

Matters most before you create a branch, a pull request, or a worktree, and before you open, sync, or remove a worktree.

## Branch, or straight to the trunk

The default is no branch. You'll be tempted to give work a branch for other reasons: a branch per sub-agent held until someone integrates it, a trial branch pushed so CI runs its matrix, or verified fixes parked on branches while a flaky test is unresolved. A branch is never a way to try CI and never a place to store proven work. Quarantine the flaky test with a stated reason and integrate the fixes now.

Where a branch exists at all, it is rare and short. It serves only review and CI, belongs to one developer, lives two days at most with review included, is never the base for other work, and is deleted once merged. Each worktree is such a branch: one in progress per agent session, and worktrees never merge into one another.

Your branch is nothing more than your local commits not yet on the trunk, whether or not it has a name. Expect it to exist for minutes; pushing it anywhere but the trunk is never part of the job.

Being short-lived doesn't make a forbidden merge safe. A short-lived branch exchanges work only with the trunk, every commit it delivers must be releasable by itself, and only its own developer or pair writes to it.

One developer or pair writes to a branch. When a branch is shared, that developer's agents count as one writer with the developer; put two people's agents on one branch and you have two writers. Others may read a branch to review it, but never commit production code to it.

A short-lived branch lives two days at most, counting time spent waiting for review, and a bug-fix branch gets no exemption. Past that it is a long-lived feature branch. Agents aim for minutes and treat two days as a far-off ceiling, never as a pace.

Rebase your unpublished local commits onto the trunk, as the loop in SKILL.md says. A branch already published for a pull request is different: keep it current by merging the trunk into it, since rewriting history others are reading disrupts them. Merge it into the trunk once, to finish it, and then delete it.

A pull-request branch counts as trunk-based only if its review is treated as urgent and finished promptly, before integration.

## Worktrees

Worktrees make opening another branch nearly free, so you'll tend to keep several going. Keep one in progress per agent session, and land it before you open another; an orchestrator's agents each hold their own one. If you already hold several, land each as soon as it is green, independently of the others; put unfinished work behind a flag and land it in slices; never wait to land them in sequence.

Every worktree is bound by the branch lifetime limit on its own. Sync each with the trunk separately, and integrate it only through the trunk, never into another worktree's branch, yours included. Clean up as branches merge: when a worktree's branch has merged and been deleted, delete the worktree, and run `git worktree list` now and then to catch any left behind.

For a side task that would otherwise make you stash or disturb work in progress, open an extra worktree from the same clone.
