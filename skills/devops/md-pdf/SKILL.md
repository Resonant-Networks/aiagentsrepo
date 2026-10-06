---
name: md-pdf
description: >
  Convert Markdown documents to professional PDFs using Pandoc + WeasyPrint
  with a Notion-style CSS theme and optional company logo.
  Use when the user asks to convert markdown to PDF, generate PDF documentation,
  or render a styled PDF from a .md file.
---

## Requirements

```bash
sudo apt install pandoc weasyprint
```

## Files

Located at `~/.config/opencode/skills/md-pdf/`:

- `notion-style.css` — Notion-like styling (clean tables, code blocks, blockquotes)
- `RNetlogo.jpg` — Company logo (optional, referenced at top of markdown)

## Markdown Structure

Include the logo at the top of your `.md`:

```markdown
<img src="RNetlogo.jpg" alt="RNetlogo" class="logo" />

# Document Title

| | |
|---|---|
| **Document Version:** | 1.0 |
| **Prepared By:** | Author Name |
| **Date:** | Month Year |

---

## 1. First Section
```

## CSS Theme

`notion-style.css` provides:

| Element | Style |
|---------|-------|
| Body | Inter/Segoe UI, 11pt, max-width 700px |
| Logo | Centered block, 120px width |
| h1 Title | 20pt, dark blue (#0B3D91) |
| Section headings | 16pt bold, dark blue |
| Sub-headings | 13pt semibold |
| Tables | Bordered, alternating row colors, 9.5pt |
| Code blocks | Gray background, blue left border |
| Inline code | Gray pill background |
| Blockquotes | Gray box with blue left border |
| Horizontal rules | Thin gray line |

## Convert to PDF

```bash
SKILL_DIR=~/.config/opencode/skills/md-pdf
cp "$SKILL_DIR/notion-style.css" "$SKILL_DIR/RNetlogo.jpg" .
pandoc document.md -o document.pdf \
  --pdf-engine=weasyprint \
  --css=notion-style.css
rm -f notion-style.css RNetlogo.jpg   # optional cleanup
```

No `--metadata title` flag — let the markdown's `# Title` be the single source to avoid duplicate titles.

## Workflow

1. Write the document in markdown (use sections `## 1.`, `## 2.`, etc.)
2. Run the pandoc command above (copies assets from skill dir, builds PDF, cleans up)
3. Open the PDF to verify

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Duplicate title on page 1 | Remove `--metadata title` from pandoc command |
| Logo not found | Run the `cp` step from the command above to copy `RNetlogo.jpg` from the skill dir |
| Overfull code blocks | CSS already sets `white-space: pre-wrap; word-break: break-all` |
| `gap` / `overflow-x` warnings | Harmless — from pandoc's internal template |
| Images with spaces in name | URL-encode spaces: `image%20name.png` or rename without spaces |
