# Help Options

Read the skill's SKILL.md file and display its content as formatted documentation (title, arguments, process steps, and notes). Then present two questions using `AskUserQuestion`. After the user selects options, store their choices and apply them during the workflow.

## Question 1: Workflow scope

Use `multiSelect: false`. These options are mutually exclusive.

| Option | Description |
|--------|-------------|
| Full PR (default) | Branch, commit, push, and open a pull request |
| Commit only | Stage and commit but don't push or create a PR |
| Push only | Commit and push but don't create a PR |

## Question 2: PR options

Use `multiSelect: true`. These can be combined. Skip this question if the user selected "Commit only" or "Push only" above.

| Option | Description |
|--------|-------------|
| Standard PR (Recommended) | No extra options, just create the PR |
| Draft PR | Create the pull request as a draft |
| Self-merge | Create the PR and immediately merge it |

## How to Apply

When options are selected, apply them by adjusting the workflow:
- **Commit only**: Stop after Step 3 (Stage & Commit). Skip push and PR creation.
- **Push only**: Stop after Step 4 (Push). Skip PR creation.
- **Draft PR**: Add `--draft` flag to `gh pr create`.
- **Self-merge**: After creating the PR, run `gh pr merge --merge` and delete the branch.
