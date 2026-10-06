---
name: devops-log
description: >
  Create and maintain a structured devops session log under /home/ubuntu/devops-logs/.
  Use when the user asks to document changes, create session logs, or track infrastructure work.
  Naming: YYYY-MM-DD_HHmm_short-description.md
---

## What I do

- Create session logs in `/home/ubuntu/devops-logs/` after making infrastructure changes
- Use filename convention: `YYYY-MM-DD_HHmm_brief-description.md`
- Include sections: Changes, Verification, Rollback, Notes
- Use a compact table format for changes
- Verify each change and record results
- Provide exact rollback commands for every change

## When to use me

Use this skill when:
- The user asks to "log changes", "document work", "create a session log", or mentions "devops log"
- You modify nginx, Docker, systemd, networking, SSL, or any infrastructure component
- You want to make work auditable and reversible

## Format

Use this template:

```markdown
# DevOps Log

## <timestamp> — <short-description>

### Changes
| # | Action | Detail |
|---|--------|--------|

### Verification

### Rollback
\`\`\`bash
\`\`\`

### Notes
```
