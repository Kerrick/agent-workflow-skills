# Speeding up the build and setting up CI

Matters most when the pre-push gate drifts past about a minute, when you configure CI, and when agents keep losing races to push.

## The gate has drifted past about a minute

The usual budget you know for a commit build is about ten minutes. Here the target is about a minute, and a much longer build is a defect to fix, since it sets the floor on how often anyone can commit.

Use a graph-based build tool with a shared remote cache, so builds skip work the change doesn't touch and reuse compiled outputs across machines.

Split whatever still has to run across parallel workers and shards.

Use Test Impact Analysis where each test exercises a small part of the code. Where most tests run through most of the code, a coverage map adds little; don't build one there.

Replace internal tiers and external services with mocks or virtualized stand-ins, so builds are fast, deterministic, and able to run offline.

Write many tests and keep each one fast, so that a large suite never pushes the gate past its budget.

## Setting up trunk CI and a commit queue

When agents keep losing the race between syncing and pushing, put a commit queue, also called a merge queue, in front of the trunk. Agents hand changes to it; it tests each on the latest trunk, possibly batching several or building ahead, lands the passing ones in order, and returns failures to their authors. Only the queue writes to the trunk, and no person signs off inside it, so it is not a review gate. Handing your change to the queue is your push. An orchestrator is never the queue.

Where the tooling allows, run CI on each commit as a speculative merge, and use a merge queue that tests every change against the trunk as it will be once that change lands.
