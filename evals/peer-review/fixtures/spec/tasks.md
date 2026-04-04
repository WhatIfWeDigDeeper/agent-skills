# Tasks: data-sync skill

## Phase 1: Skill Scaffolding

- [ ] Create `skills/data-sync/SKILL.md` with frontmatter
- [ ] Implement argument parsing: `--target ENV` (default `staging`), `--dry-run`
- [ ] Document workflow steps: Diff, Preview, Sync, Report

## Phase 2: Implementation

- [ ] **Diff step**: run `rsync --dry-run` to collect changed files list
- [ ] **Preview step**: if `--dry-run` flag present, print file list and exit
- [ ] **Sync step**: run `rsync` to push changed files
- [ ] **Report step**: print summary line "Synced N files to ENV."

## Phase 3: Verification

- [ ] Test `--dry-run` shows file list without syncing
- [ ] Test `--target production` routes to production environment
- [ ] `npx cspell skills/data-sync/SKILL.md`
