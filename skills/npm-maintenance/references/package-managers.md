# Package Manager Reference

## Detection

Check for lock files in order of precedence:

| Lock file | Package manager |
|-----------|-----------------|
| `bun.lockb` | bun |
| `pnpm-lock.yaml` | pnpm |
| `yarn.lock` | yarn |
| `package-lock.json` | npm |

Also check `package.json` for `packageManager` field:
```json
{
  "packageManager": "pnpm@8.6.0"
}
```

If no lock file exists, default to npm.

## Command Reference

Use `$PM` as the detected package manager throughout the workflow.

### Verify Connectivity

| Manager | Command |
|---------|---------|
| npm | `npm ping` |
| yarn | `yarn --version` |
| pnpm | `pnpm --version` |
| bun | `bun --version` |

Note: Only npm has a dedicated ping command. For others, verify the CLI works.

### Audit

| Manager | Command | JSON output |
|---------|---------|-------------|
| npm | `npm audit` | `npm audit --json` |
| yarn | `yarn audit` | `yarn audit --json` |
| pnpm | `pnpm audit` | `pnpm audit --json` |
| bun | Not supported | - |

### View Package Info

| Manager | Latest version | Dist tags |
|---------|----------------|-----------|
| npm | `npm view <pkg> version` | `npm view <pkg> dist-tags` |
| yarn | `yarn info <pkg> version` | `yarn info <pkg> dist-tags` |
| pnpm | `pnpm view <pkg> version` | `pnpm view <pkg> dist-tags` |
| bun | `bunx npm-view <pkg> version` | - |

### Install/Update Package

| Manager | Install latest | Install specific |
|---------|----------------|------------------|
| npm | `npm install <pkg>@latest` | `npm install <pkg>@<version>` |
| yarn | `yarn add <pkg>@latest` | `yarn add <pkg>@<version>` |
| pnpm | `pnpm add <pkg>@latest` | `pnpm add <pkg>@<version>` |
| bun | `bun add <pkg>@latest` | `bun add <pkg>@<version>` |

### Run Scripts

All package managers support `$PM run <script>` syntax:
- `npm run build`
- `yarn run build` (or just `yarn build`)
- `pnpm run build`
- `bun run build`
