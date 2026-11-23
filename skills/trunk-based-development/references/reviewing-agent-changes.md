# Reviewing agent changes

Matters most before you review anything, and before you set up review of agent output.

## Who reviews, when, and how

As an orchestrator, you'll treat reading each sub-agent's diff while you integrate it as the review step. Review needs a reviewer who is independent: a person, or an agent with no part in the change or its brief, so an orchestrator can't review its own sub-agents' work. That reviewer reads each change within minutes of it reaching the trunk. Its answer is never an approval: it pushes a follow-up fix commit or reverts the change. Some projects also have an agent look over each patch before it enters the queue; that is optional and never stands in for review after landing.

Pair programming counts as review. An agent that helped produce a change is one of its authors, never its reviewer.

Aim for zero waiting reviews: each one starts within minutes and judges the change quickly, against objective criteria. An agent that finishes a task picks up any changes waiting for review before it starts anything new.

Agents produce changes faster than any person can read them, so a model reads each change before a person does. If review starts to hold work up, make review faster; don't add work in progress to get around slow review.

People sample and audit what the AI reviewer passed. When a defect slips through, fix the reviewer's guidance or the automated checks, and still fix or revert the defect itself.

Reject a change only for objective reasons that are documented and public, never because someone claims sole right to that code.

Next to the AI reviewer, CI runs the test suite, type checks, and lint on every change, so judgment is never the only gate.
