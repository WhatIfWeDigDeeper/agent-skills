# Package Manager Reference

## Detection

Check in this order (first match wins):

**1. `packageManager` field in `package.json`** — this is the authoritative declaration:
```json
{
  "packageManager": "pnpm@8.6.0"
}
```

**2. Lock files** — if no `packageManager` field:

| Lock file | Package manager |
|-----------|-----------------|
| `bun.lockb` | bun |
| `pnpm-lock.yaml` | pnpm |
| `yarn.lock` | yarn |
| `package-lock.json` | npm |

**3. Default** — if neither, use npm.

## Command Reference

Use `$PM` as the detected package manager throughout the workflow.

### Verify CLI and Connectivity

| Manager | Command | Verifies |
|---------|---------|----------|
| npm | `npm ping` | Registry connectivity |
| yarn | `yarn info yarn version` | CLI + registry connectivity |
| pnpm | `pnpm view pnpm version` | CLI + registry connectivity |
| bun | `bun --version` | CLI only (no registry ping) |

### Audit

| Manager | Command | JSON output |
|---------|---------|-------------|
| npm | `npm audit` | `npm audit --json` |
| npm | `npm audit fix` | _(auto-fixes; no JSON mode)_ |
| yarn | `yarn audit` | `yarn audit --json` |
| pnpm | `pnpm audit` | `pnpm audit --json` |
| bun | Not supported | - |

### Check Outdated Packages

| Manager | Command |
|---------|---------|
| npm | `npm outdated` |
| yarn | `yarn outdated` |
| pnpm | `pnpm outdated` |
| bun | `bun outdated` |

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
