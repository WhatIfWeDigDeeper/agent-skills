# API Error Handling

This policy applies to `gh api` commands and `git push` in the pr-comments skill, including step snippets.

## Retry policy

For every `gh api` call (REST and GraphQL), wrap the command in a 3-attempt retry with exponential backoff:

- **Auto mode**: perform retries silently. If all 3 attempts fail, pause auto mode and surface the error for manual resolution before continuing.
- **Manual mode**: after exhausting retries, show the error and ask whether to continue.

## git push failures

Do not retry `git push` automatically — show the error and suggest the user push manually. Push failures are typically persistent (branch protection, auth issues, etc.) and retrying without user intervention will not resolve them.
