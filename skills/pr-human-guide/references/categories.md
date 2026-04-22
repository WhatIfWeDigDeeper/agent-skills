# Review Categories

## 1. Security

**Why human review is needed**: Security requires threat modeling and
contextual judgment — understanding what an attacker could do with a change,
not just whether the code is syntactically correct.

**Detection signals** (file content and diff patterns):

- Authentication and authorization logic: login flows, session management,
  token creation/validation/revocation, role/permission checks, middleware
  that gates access
- Cryptography: hashing (especially password hashing), encryption/decryption,
  key generation, signing/verification, use of `crypto` libraries
- Input handling at trust boundaries: parsing user-supplied data, SQL/NoSQL
  query construction, HTML rendering of user content, file path construction
  from user input, deserialization
- Secret/credential handling: reading env vars that look like secrets, storing
  tokens, API key management, `.env` file changes
- Network security: CORS configuration, CSP headers, allowed origin lists,
  TLS settings, certificate pinning
- Dependency security: changes to security-relevant packages (auth libraries,
  crypto libraries, HTTP clients with redirect-following)

**File name signals**: files named `auth`, `login`, `session`, `token`,
`permission`, `role`, `acl`, `crypto`, `hash`, `secret`, `key`, `password`,
`middleware` (in security context), `cors`, `csp`, `sanitize`, `validate`
(at input boundaries)

**What does NOT qualify**: internal data validation that doesn't touch a trust
boundary, logging of non-sensitive data, UI validation that is also validated
server-side.

---

## 2. Config / Infrastructure

**Why human review is needed**: Config changes can affect all environments
simultaneously and often have a blast radius that isn't visible from the diff
alone. Humans understand deployment topology and can assess what breaks.

**Detection signals**:

- CI/CD pipeline files: `.github/workflows/`, `.circleci/`, `Jenkinsfile`,
  `.gitlab-ci.yml`, `bitbucket-pipelines.yml`, `azure-pipelines.yml`
- Container/runtime config: `Dockerfile`, `docker-compose.yml`,
  `docker-compose.*.yml`, `.dockerignore` (if it affects what's in the image)
- Infrastructure as code: `*.tf`, `*.tfvars`, `*.bicep`, CloudFormation
  templates (`*.yaml` / `*.json` in `infra/`, `cloud/`, `terraform/`,
  `cloudformation/` directories), CDK stacks
- Environment configuration: `.env.example`, `.env.production`, config files
  that define per-environment values (`config/production.*`, `config/staging.*`)
- Package scripts with side effects: `package.json` `scripts.build`,
  `scripts.start`, `scripts.deploy`, `scripts.postinstall`
- Kubernetes/Helm: `*.yaml` in `k8s/`, `helm/`, `charts/` directories,
  resource limits, replica counts, service type changes
- IAM/permissions: role definitions, policy documents, service account config

**What does NOT qualify**: `package.json` version bumps with no script changes,
`README` updates in config directories, test configuration files
(`jest.config.js`, `pytest.ini`) unless they change test execution scope.

---

## 3. New Dependencies

**Why human review is needed**: Dependencies introduce supply chain risk,
license obligations, and maintenance burden. Humans can evaluate whether a
dependency is trustworthy and whether it's the right choice.

**Detection signals**:

- New entries in `package.json` dependencies or devDependencies
- New entries in `requirements.txt`, `Pipfile`, `pyproject.toml` (dependencies
  section), `setup.py` install_requires
- New entries in `go.mod`, `Cargo.toml`, `Gemfile`, `build.gradle`,
  `pom.xml`, `composer.json`
- Lockfile changes that add new transitive packages (e.g., `package-lock.json`,
  `yarn.lock`, `pnpm-lock.yaml`, `poetry.lock`) — flag if the lockfile adds a
  package not already present in the manifest (transitive dependency)

**Elevated concern signals** (always flag, regardless of size):
- Packages with native bindings or C extensions
- Packages that make network requests as part of their operation
- Packages with filesystem access (reading outside project directory)
- Packages for auth, crypto, or security

**What does NOT qualify**: version bumps of existing dependencies (unless
upgrading across major versions), moving a dep from devDependencies to
dependencies without adding a new package.

---

## 4. Data Model Changes

**Why human review is needed**: Schema changes affect data integrity,
backwards compatibility, and rollback safety. Humans can assess whether
migrations are safe under concurrent traffic and whether clients are prepared.

**Detection signals**:

- Database migrations: files in `migrations/`, `db/migrate/`, `alembic/`,
  `flyway/` directories; files named `*.migration.*`, `*_migration.*`,
  `*_migrate.*`
- Schema definition files: `schema.prisma`, `schema.rb`, `models.py`
  (Django), entity definitions with column annotations
- API contracts: changes to `.proto` files, GraphQL schema files (`*.graphql`,
  `*.gql`, `schema.graphql`), OpenAPI/Swagger specs (`openapi.yaml`,
  `swagger.yaml`, `*.spec.yaml` in API directories)
- Serialization formats: changes to JSON schema files, Avro/Thrift schemas
- ORM model changes: adding/removing/renaming columns, changing column types,
  adding/removing relationships, changing nullability constraints

**Elevated concern signals**:
- `DROP`, `DELETE`, `TRUNCATE` in migration files
- Removing nullable constraint from existing column
- Renaming a column without an alias/migration
- Removing a field from an API response schema
- Changing a field type in a way that isn't backwards-compatible

**What does NOT qualify**: adding a new table/model with no foreign keys to
existing tables (low blast radius), purely additive API changes (new optional
fields), index additions with no schema change.

---

## 5. Novel Patterns

**Why human review is needed**: Introducing a new pattern requires architectural
judgment — is this the right abstraction, does it fit the codebase's direction,
will it be maintainable by the rest of the team?

**Detection approach**: Compare the diff against sibling files and existing
modules. Read 2-3 files from the same directory or related modules to
understand existing conventions, then assess whether the changed file introduces
something the codebase hasn't seen before.

**Examples of novel patterns that qualify**:

- First use of a caching layer (Redis, Memcached, in-memory LRU) when the
  codebase previously had none
- Introducing a new ORM or query pattern that differs from the rest of the
  codebase
- A different error handling strategy (e.g., introducing Result types in a
  codebase that uses exceptions, or vice versa)
- First use of a concurrency primitive (goroutines, async/await, threads,
  workers) in a context where the rest of the code is synchronous
- A new directory structure or module organization pattern
- Introducing a new framework or major library for a concern already handled
  elsewhere (e.g., adding a second HTTP client when one already exists)
- First use of metaprogramming, reflection, or code generation
- Introducing a new testing pattern (e.g., property-based testing, snapshot
  testing) when the codebase uses a different approach

**What does NOT qualify**: consistent use of existing patterns, adding a new
file that follows the same structure as its siblings, using a library already
imported elsewhere in the codebase.

**Sampling guidance**: For large codebases, prioritize reading files in the
same package/module as the changed file, then the most-imported utility
modules. Do not read the entire codebase — 2-3 representative files is enough
to establish the existing pattern.

---

## 6. Concurrency / State

**Why human review is needed**: Race conditions and deadlocks are difficult to
detect with static analysis and require reasoning about execution order under
concurrent load.

**Detection signals**:

- New use of locking primitives: mutexes, semaphores, `synchronized` blocks,
  `Lock`, `RWLock`, `threading.Lock`, `asyncio.Lock`
- New shared mutable state: module-level variables that are written from
  multiple call sites, class-level state accessed across request boundaries,
  global caches without lock protection
- New async/concurrent patterns: new goroutines, new `async def` functions
  that access shared state, new `Promise.all` / `Promise.race` with shared
  side effects, new worker threads
- Channel/queue usage: new message queues, new pub/sub patterns, new event
  emitters with state side effects
- Database transaction scope changes: changing isolation levels, adding or
  removing transactions, adding `SELECT FOR UPDATE`

**What does NOT qualify**: async I/O with no shared state (e.g., purely
fetching data and returning it), read-only access to shared state, using
existing well-established concurrency patterns consistently.

---

## Consolidation Rules

When multiple items in the same file qualify for the same category:

1. If the flagged regions are adjacent or within 20 lines of each other,
   merge into a single line range: `(L10-45)`
2. If the flagged regions are scattered across the file, omit the line range
   and describe the concern at the file level
3. If a file qualifies for two different categories, create separate entries
   for each — do not merge across categories

## Selectivity Threshold

Flag an area only if a reasonable senior engineer would specifically want to
review it beyond what automated tools would catch. When in doubt, flag only
when there is a concrete reviewer-relevant risk or uncertainty.

Exceptions — never flag these regardless of content:
- Changes that only affect comments or documentation
- Test files (unless they contain security test fixtures with real credentials,
  or test infrastructure that affects production code paths)
- Auto-generated files (lockfiles with only version changes, compiled output,
  generated protobuf stubs)
- Whitespace-only or formatting-only changes
