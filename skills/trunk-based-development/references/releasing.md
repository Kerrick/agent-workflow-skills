# Releasing

Matters most before any work on releases, tags, or release branches: when someone says "ship it", when releases have stalled, when you write or run a release job, when you record what shipped, when a released version has a production bug, and when you decide whether to cut, feed, or delete a release branch.

## Who ships, and what a release is

Asked for a release, you'll want to pick the version bump, commit it, tag, and then confirm with the user before publishing. Keep the instinct to confirm, and go further: an agent doesn't tag, publish a release, or create a release branch unless the repository's rules name it, because a release leaves the local copy and no revert can recall it. This holds for agents even where general guidance treats them like any other developer. The rules say who ships: a named person, a rotating role, or an automated job the owner has approved. An orchestrator never ships because its agents finished, never lets an agent decide to ship, and asks the user when the rules say nothing. "Ship it" and "wrap up" by themselves mean land the change on the trunk: land it, and say you made no release.

Releasing means choosing a commit CI has verified, tagging it, and publishing the artifacts CI built for it. The trunk never pauses for this, and agents keep committing at full pace meanwhile.

For plenty of projects a tag is all a release needs: name a trunk commit CI has passed after the version, and publish from it. The tagged commit needn't be the newest, only trusted; never tag the tip before CI has passed it.

When CI verifies several commits in one build, the newest of them counts as verified and is a release candidate like any other.

With a trunk that is always green, releasing is just picking a verified commit to ship. Each team sets its own cadence, and the more often it ships, the less process it needs. If a release starts to feel like an event, or releases stop because none of the recent trunk commits has a CI run that finished green, treat it as a defect in how builds, reverts, or flags are handled, and repair that. Don't plan around it or let shippable changes pile up behind it.

A team that ships many times a day can use a version generated from the commit count or the date instead of dotted numbers. Teams that ship less often, and anyone publishing a library others depend on, use SemVer, because there the version is a promise to users.

## Release automation never chases the tip

You'll want a release to start with a commit that moves the changelog's unreleased section under a dated version heading and bumps the version file, followed by a tag on that commit. Don't. A library with SemVer, a version file, and a changelog still ships with no release commit, because such a commit has to reach a busy tip and pass CI again, and the release stalls behind it. At the chosen commit, work out the version from the last release tag plus what has changed since, judged by breaking entries in the changelog or by comparing the public API. Have the build take the version from the tag and write it into the package, and use the changelog's unreleased section at that commit as the release notes. Nobody, person or agent, should have to chase the trunk's tip to ship.

For example, the last tag is v3.4.2, and the unreleased section at the chosen commit lists one added option and nothing breaking. An addition is a minor change, so the release is v3.5.0: tag that commit `v3.5.0`, let the build stamp 3.5.0 into the published package, and take the notes from that unreleased section. The trunk gets no commit.

A release job, being automated, tags the latest commit whose CI run finished green, even when the trunk has moved well past it. It doesn't need that commit to be the tip, doesn't wait for a lull in pushes, and makes no commit to the trunk while releasing; changelog bookkeeping is a separate job that runs later. Waiting for a quiet trunk is accumulating a release, not choosing one.

## Changelog and version after a tag

Once a tag exists, automation updates the trunk's changelog: it gives the release a dated heading, files under it only those pending entries the tagged commit already had, leaves anything newer pending, and raises the version file to match if the project keeps one. If it loses a race with another push, it rebases and tries again; after a failed run, it rebuilds its result from the tags. Keep dated history in the trunk's changelog. Never reduce the changelog to one growing unreleased list whose history exists only when regenerated from tags: after a few weeks of releases such a file shows no history and is full of changes shipped long ago.

## When a release branch is needed

Teams that ship many times a day have no release branches: a bad production build is fixed on the trunk, and the trunk ships again.

A team that releases daily or less often may use one. Cut it only when its rule of taking no ongoing development clashes with the trunk's, at the latest moment that works, and in place of a freeze; a team that must ship fixes between slower releases usually cuts it shortly before the release.

Don't cut one before it's needed. A branch created later from an old commit is identical, so a team that ships from tags creates a branch from a release's tag only when that release needs a fix, or ships the trunk again instead. Point releases follow the same rule.

Cut from a trusted commit, which need not be the trunk's head: an earlier known-good commit, or the one just before changes that shouldn't ship.

Before a cut, land unfinished work behind a feature flag that is off; the branch can then start at the newest commit.

## Fixing a bug in a shipped release

Fix a production bug on the trunk as fast as you can, like any other change, and release it the usual way. Nothing slows down around a release.

Urgency, or having first seen the bug on the release branch, will tempt you to patch the release branch now and bring the fix to the trunk afterwards. Don't: the port gets forgotten and the bug returns in the next release. Hold to this even when the shortcut looks faster.

One exception: a bug that genuinely cannot be reproduced on the trunk. Then the cherry-pick owner, or whoever the repository names, fixes it on the release branch, accepting the regression risk, and the same fix goes to the trunk immediately, in the same piece of work. Urgency and drifted code don't qualify.

Only the cherry-pick owner cherry-picks onto release branches. After fixing a production bug, you'll want to cherry-pick it onto the release branch yourself. Stop at the trunk: land the fix with its test through the usual loop, then tell the cherry-pick owner, or the user, which commit is a candidate. Leave the release branch alone, even to save time.

In order: (1) make the bug happen on the trunk; (2) commit the fix there along with a test; (3) let the trunk's CI go green; (4) cherry-pick the commit onto the release branch; (5) let that branch's CI go green too. Those waits belong to the cherry-pick owner; you push the trunk fix, report it, and move on.

When the faulty release came off a release branch, nothing changes: the trunk gets the fix, the branch gets a cherry-pick of it, and a point release follows if your cadence calls for one. When it came off a tag instead, this is the moment to start a release branch, rooted at that tag.

Name one owner for release branches: every cherry-pick onto them is theirs, made only after checking the agreed conditions. Record each request to add something after the cut, with its approval, in a tool.

Backports go through recorded requests: the fix lands on the trunk and closes its issue, a separate linked request asks for it in an older release, and the cherry-pick waits for approval from code owners or release managers. A project may limit which release branches take backports.

Each active release branch runs its own copy of the trunk's CI pipeline, and every cherry-pick is verified there, because the code around it differs from the trunk.

Cherry-pick, never merge: a cherry-pick copies only the chosen commits, and version control tracks them so later cherry-picks still apply. If commits were skipped on purpose, QA that passed on the trunk may need to recheck the release branch.

All development goes to the trunk; a release branch takes in only cherry-picks from it. Merges in either direction between a release branch and the trunk are off the table.

Commits an early cut missed reach the release branch, if needed, only as cherry-picks from the trunk, like fixes, and never the reverse.

## Retiring a release branch

Delete a release branch once nothing ships from it any more, usually after a newer release is live. Tag the last release on it first, because git eventually garbage-collects commits nothing refers to; the branch can be recreated from the tag.
