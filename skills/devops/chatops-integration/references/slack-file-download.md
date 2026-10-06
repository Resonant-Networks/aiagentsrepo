# Slack File Download via REST API

The Slack MCP tools (8 tools) do NOT include a "download file" function. When you need to retrieve a file shared in a Slack channel (PDF, image, document), use the Slack REST API directly with the bot token.

## Workflow

### 1. Find the File

Use the Slack MCP tool to get channel history and identify the file ID:

```
mcp__slack__slack_get_channel_history(channel_id="C0XXXXXXX")
```

The response's `files[]` array contains: `id`, `name`, `mimetype`, `url_private_download`, `size`, `filetype`.

### 2. Download with Auth

The `url_private_download` from Slack requires authentication. The bot token is in the env:

```bash
SLACK_TOKEN=$(grep SLACK_BOT_TOKEN ~/.hermes/.env | cut -d= -f2)

# Get file metadata + download URL
FILE_INFO=$(curl -s -H "Authorization: Bearer $SLACK_TOKEN" \
  "https://slack.com/api/files.info?file=$FILE_ID")

URL_PRIVATE=$(echo "$FILE_INFO" | python3 -c \
  "import sys,json; print(json.load(sys.stdin).get('file',{}).get('url_private_download',''))")

# Download
curl -sL -H "Authorization: Bearer $SLACK_TOKEN" -o /tmp/output.pdf "$URL_PRIVATE"
```

### 3. Extract Content

```bash
# For PDFs
pdftotext /tmp/output.pdf /tmp/output.txt

# Find relevant sections
grep -n "Section Name\|Chapter N\|Keyword" /tmp/output.txt

# Read targeted portions
read_file(path="/tmp/output.txt", offset=N, limit=500)
```

## Pitfalls

- **Plain curl (no auth)** returns a ~77KB placeholder instead of the real file — always use the `Authorization` header
- **Public permalink** (`slack-files.com/...`) also redirects to an auth wall — use `files.info` API endpoint
- **Token redaction** — the token value is masked in `config.yaml` output; extract from `~/.hermes/.env` instead
- **Large PDFs** — use `pdftotext` (from `poppler-utils`) for full extraction; `read_file` auto-converts but caps at ~100K chars
