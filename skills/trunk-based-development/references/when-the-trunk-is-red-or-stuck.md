# When the trunk is red or stuck

Matters most the moment CI or a build shows the trunk broken, by you or anyone else; when a flaky test blocks you; and when trunk CI runs keep getting cancelled.

## The trunk is red

A red trunk comes before every other task. Your default will be to read the log, reason out a fix, push it, and watch whether CI goes green. Revert the breaking commit at once instead; pushing guesses to see how CI reacts is push-and-poll with the trunk red throughout. Only a very small team may fix forward instead, and only quickly. A team is very small when it has a few concurrent writers at most, people and agents counted together, whatever its headcount (see the team-size rule in [coordinating with others](coordinating-with-others.md#choosing-how-a-team-of-agents-lands-work)).

When the failure shows up on one system only, reproduce it on a machine running that system (a failure specific to one system is exactly when naming a system is right), and demonstrate the fix there before you push. Don't conclude without trying that a machine can't run the check. If you can't demonstrate the fix there within minutes, revert, and work on the fix away from the trunk.

When someone else's commit broke the trunk, you'll hesitate to revert it. Where the project has a build cop or a revert job, it reverts the commit at once. Where it has neither, any agent that sees the breaking commit reverts it at once and tells its author and the user; an orchestrator that sees it briefs an agent to revert it, and does not revert it itself. Nobody waits on a forward fix; the author lands the fix again once it's ready.

With many agents committing, build every commit and find culprits by automated bisection; an agent can hold build-cop duty.

## A test fails intermittently

You'll want to rerun a flaky test until it passes and move on. Never accept a test that can pass while the code is broken. Fix the flaky test, or quarantine it with its reason recorded, right away, and integrate your other work immediately rather than holding it behind the flake.

## Trunk runs never complete

When new pushes keep cancelling trunk CI runs so that none ever finishes, the fix is in CI's configuration: set it up so pushes can't cancel runs in a way that leaves none completing. A batched run that verifies the newest of several commits is fine. Never ask people to push less often, and never hold pushes to let a run finish.
