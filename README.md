# Agent workflow skills

[Agent Skills](https://agentskills.io/) for developers who run coding agents, often several at once, and want their work to land small, proven, and visible:

- **cumulative-flow** keeps a plain-text ledger of work items, with the times each was found, started, and landed, and draws a cumulative flow diagram from it with a bundled script, so the agent can say whether a body of work is converging instead of guessing a percent done.
- **agent-orchestration** guides an agent that delegates to sub-agents or works beside other agent sessions: writing briefs, choosing a model, keeping agents busy instead of blocked on CI, checking what agents actually did, relaying between the user and agents, and handling refusals.
- **trunk-based-development** guides committing and integrating trunk-based: small green commits straight into one trunk, a fast build before every push, no long-lived or sideways branches, never push-and-poll CI, and a red trunk fixed or reverted at once. For the practice in depth, see [trunkbaseddevelopment.com](https://trunkbaseddevelopment.com/), by Paul Hammant and its contributors.

An Agent Skill is a folder with a `SKILL.md` file of instructions. Your agent loads one when a request matches its description, and follows it. The three skills refer to each other: agent-orchestration has every agent that commits read trunk-based-development, and keeps its count of open and landed work with cumulative-flow. It also points to the `adr` skill in [technical-writing-agent-skills](https://github.com/Kerrick/technical-writing-agent-skills) for decision records.

## Example: drawing a cumulative flow diagram

cumulative-flow includes `scripts/cfd.py`, which reads the ledger, a tab-separated file with this header row:

```
id	title	kind	found	started	landed	commits	note
```

Run from the skill's folder, it writes `cfd.svg` beside the ledger and prints the counts now and six hours ago:

```
uv run scripts/cfd.py path/to/ledger.tsv --title "Road to 1.0" --utc-offset -6
```

Run `uv run scripts/cfd.py --help` for the other options, such as `--markers` for vertical marks at a release or a broken build, and `--json` for the summary as JSON.

## Compatibility

| Requirement | Details |
| - | - |
| Format | The [Agent Skills specification](https://agentskills.io/specification). |
| Agent | Any agent that loads Agent Skills. agent-orchestration names Claude models (Sonnet, Opus) and Claude Code features in places. |
| Installing | [Node.js](https://nodejs.org/), for `npx skills`. Or copy the folders by hand. |
| `cfd.py` (cumulative-flow only) | [uv](https://docs.astral.sh/uv/), or Python 3.11 or later with `python3 scripts/cfd.py`. It uses only the standard library. |

## Installation

Install every skill for your user account with the [`skills`](https://github.com/vercel-labs/skills) command-line tool:

```
npx skills add Kerrick/agent-workflow-skills -g -a claude-code --skill '*' -y
```

This copies each skill into `~/.claude/skills/`. To install into the current project instead, leave out `-g`, and the skills go in `.claude/skills/` in that folder. To install only one, name it, as in `--skill cumulative-flow`. For another agent, change `claude-code` after `-a`, or leave out `-a` to choose from the agents the tool detects. Run `npx skills add --help` for the other options. To see which skills the repository holds before you install, run:

```
npx skills add Kerrick/agent-workflow-skills --list
```

To install by hand on macOS or Linux, clone this repository and link each folder in `skills/` to where your agent looks for skills, so a `git pull` updates them. For Claude Code:

```
git clone https://github.com/Kerrick/agent-workflow-skills.git ~/src/agent-workflow-skills
ln -s ~/src/agent-workflow-skills/skills/* ~/.claude/skills/
```

On Windows, use `npx skills`, which copies the folders for you.

## Usage

Work with your agent the way you usually would, such as "how far along is the bug list?", "split this across a few sub-agents", or "commit and push this". Your agent picks a skill by comparing your request with each skill's description. To be sure it uses one, name it: "use trunk-based-development to land this change".

To get newer versions of skills you installed with `-g`, run:

```
npx skills update -g
```

## Reporting problems

Open an issue at [github.com/Kerrick/agent-workflow-skills/issues](https://github.com/Kerrick/agent-workflow-skills/issues). Include the agent and model you used, the prompt you gave it, and what the agent did that broke a rule or missed one.

## License

What you make with the skills is yours, without conditions. The skills, and the rest of the repository, are dedicated to the public domain under [CC0 1.0](LICENSES/CC0-1.0.txt). [`REUSE.toml`](REUSE.toml) gives every file's license, following the [REUSE specification](https://reuse.software/), and [`LICENSES/`](LICENSES/) holds the text.
