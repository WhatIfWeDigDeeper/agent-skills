# GraphQL Queries

> **zsh compatibility note**: GraphQL queries with typed variable declarations (`String!`, `Int!`, etc.) cannot be passed as inline shell strings in zsh — `!` triggers history expansion. Use Python subprocess or write the query to a file:
> ```python
> import subprocess
> q = 'query($owner: String' + chr(33) + ', $name: String' + chr(33) + ', $number: Int' + chr(33) + ') { ... }'
> subprocess.run(['gh', 'api', 'graphql', '-f', 'owner=OWNER', '-f', 'name=REPO', '-F', 'number=N', '--field', 'query=' + q], ...)
> ```

## Fetch Thread Resolution State (Step 3)

The REST API doesn't expose whether a thread is resolved. Use this query to get thread node IDs, resolution state, and outdated status:

```bash
gh api graphql \
  -f owner=OWNER -f name=REPO -F number=PR_NUMBER \
  -f query='
query($owner: String!, $name: String!, $number: Int!, $after: String) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $number) {
      reviewThreads(first: 100, after: $after) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          isResolved
          isOutdated
          comments(first: 1) {
            nodes { databaseId }
          }
        }
      }
    }
  }
}'
```

This gives you a mapping from REST `comment.id` (= `databaseId`) → GraphQL `thread.id` + `isResolved` + `isOutdated`.

**Pagination**: If `pageInfo.hasNextPage` is true, repeat the query with `-f after=END_CURSOR` until all threads are fetched.

## Resolve a Thread (Step 12)

Use the node ID returned by the fetch query above:

```bash
gh api graphql -f query='
mutation {
  resolveReviewThread(input: {threadId: "THREAD_NODE_ID"}) {
    thread { isResolved }
  }
}'
```

Only resolve threads that were addressed (accepted or implemented). Leave declined threads open so reviewers can see your reply and follow up.
