# Help Options

Display the skill's `description` from frontmatter as a one-line summary, then present two questions using `AskUserQuestion`. After the user selects options, store their choices and apply them during the workflow.

## Question 1: Destination

Use `multiSelect: false`. These options are mutually exclusive.

| Option | Description |
|--------|-------------|
| Auto-route (default) | Use the routing decision tree to choose skills or config files |
| Skills only | Only create or update skills, don't modify config files |
| Config only | Only update config files, don't create new skills |

## Question 2: Additional options

Use `multiSelect: true`. These can be combined.

| Option | Description |
|--------|-------------|
| Dry run | Show what would be learned without writing any files |
| All assistants | Write to every detected config file without prompting |

## How to Apply

When options are selected, apply them by adjusting the workflow:
- **Skills only**: In the routing step (Step 3), always route to skill creation/update (Routes B and C). Skip Route A (config file updates).
- **Config only**: In the routing step (Step 3), always route to config file updates (Route A). Skip Routes B and C (skill creation/update).
- **Dry run**: Run the full analysis and categorization, display the proposed changes, then stop without writing any files.
- **All assistants**: Skip the "prompt user to select which to update" step when multiple configs are found. Write to all detected config files.
