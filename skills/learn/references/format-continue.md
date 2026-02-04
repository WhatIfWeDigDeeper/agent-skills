# Continue Configuration Format

Continue uses JSON format for project-level configuration.

## File Location

Project-level config: `.continuerc.json` in the project root.

## JSON Structure

```json
{
  "customInstructions": "Your project-specific instructions here.\n\nMultiple paragraphs separated by newlines.",
  "models": [],
  "tabAutocompleteModel": {}
}
```

## Adding Learnings

The `customInstructions` field is a single string. To add learnings:

1. Read existing `.continuerc.json`
2. Parse JSON
3. Append new content to `customInstructions` (preserve existing)
4. Write back with proper formatting

### Example Update

**Before:**
```json
{
  "customInstructions": "Use TypeScript strict mode."
}
```

**After adding learning:**
```json
{
  "customInstructions": "Use TypeScript strict mode.\n\nAlways run tests before committing: npm test"
}
```

## Creating New Config

If `.continuerc.json` doesn't exist:

```json
{
  "customInstructions": ""
}
```

## Important Notes

- Use `\n` for newlines in JSON strings
- Escape quotes with `\"`
- The file must be valid JSON
- Project-level `.continuerc.json` takes precedence over user-level config at `~/.continue/config.yaml`

## Parsing Tips

When reading/writing:

```javascript
// Read
const config = JSON.parse(fs.readFileSync('.continuerc.json', 'utf8'));
const existing = config.customInstructions || '';

// Append
config.customInstructions = existing + '\n\n' + newLearning;

// Write
fs.writeFileSync('.continuerc.json', JSON.stringify(config, null, 2));
```
