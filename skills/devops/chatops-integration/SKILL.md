---
name: chatops-integration
description: Set up Slack/Teams/Discord MCP for Hermes NOC integration.
version: 1.0.0
author: hermes-curator
license: MIT
metadata:
  hermes:
    tags: [chatops, slack, mcp, integration, setup, incident-response]
    related_skills: [slack-incident, hermes-agent]
---

# ChatOps Integration

Configure external chat platform integrations (Slack, Teams, Discord) for Hermes NOC operations via MCP servers. This skill covers obtaining credentials, configuring `mcp_servers` in config.yaml, and verifying the integration is live.

## When to Use

- "Set up Slack MCP / Slack API integration for Hermes"
- "What credentials do I need for a Slack bot?"
- "Configure chat platform for incident response"
- Any task involving wiring up a new chat platform API/MCP for NOC operations

---

## Slack MCP Setup

### 1. Create a Slack App

1. Go to [https://api.slack.com/apps](https://api.slack.com/apps)
2. Click **Create New App** → **From scratch**
3. Name it (e.g. "Hermes NOC Bot") and select your workspace

### 2. Bot Token Scopes

Under **OAuth & Permissions** → **Bot Token Scopes**, add:

| Scope | Purpose |
|-------|---------|
| `channels:history` | View messages in public channels |
| `channels:read` | View basic channel information |
| `chat:write` | Send messages as the bot |
| `reactions:write` | Add emoji reactions to messages |
| `users:read` | View users and basic info |
| `users.profile:read` | View detailed user profiles |

### 3. Install to Workspace

Click **Install to Workspace** → authorize → copy the **Bot User OAuth Token** (starts with `xoxb-`).

### 4. Get Team ID

- From your app → **Settings** → **Basic Information**
- Or from any Slack URL: `https://app.slack.com/client/T<ID>/...` — the `T<ID>` segment is your Team ID.

### 5. Hermes Config

Add to `mcp_servers` in `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  slack:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-slack"]
    env:
      SLACK_BOT_TOKEN: "xoxb-YOUR_BOT_TOKEN"
      SLACK_TEAM_ID: "T_YOUR_TEAM_ID"
```

### 6. Verify

Restart Hermes (see Gateway Restart Blockade below if blocked), then:

- Run `hermes mcp test slack` — expect `✓ Connected` with 8 discovered tools
- Check startup logs for `"Connected to MCP server 'slack'"`
- Confirm 8 tools are registered (prefixed `mcp_slack_*`)
- Quick test: call `mcp_slack_list_channels(limit=5)`

### Exposed Tools (8 total)

| Tool | What it does |
|------|-------------|
| `mcp_slack_list_channels` | List public or pre-defined channels |
| `mcp_slack_post_message` | Post a new message to a channel |
| `mcp_slack_reply_to_thread` | Reply in a specific message thread |
| `mcp_slack_add_reaction` | Add emoji reaction to a message |
| `mcp_slack_get_channel_history` | Get recent messages from a channel |
| `mcp_slack_get_thread_replies` | Get all replies in a thread |
| `mcp_slack_get_users` | List workspace users |
| `mcp_slack_get_user_profile` | Get detailed user profile |

---

## Troubleshooting

| Symptom | Likely Cause |
|---------|-------------|
| `"Failed to connect to MCP server 'slack'"` | Token or TeamID malformed; fix config and restart |
| `"OAuth exception" / "not_in_channel"` | Bot not installed to workspace or missing channel scope |
| Tools not appearing | YAML indentation wrong under `mcp_servers`; restart required; check startup logs |
| `"SLACK_BOT_TOKEN is not set"` | Env var not passed to subprocess or dropped by credential redaction; add `env:` block explicitly or patch config.yaml directly |
| Scripts/skills reference Slack API but get 401 | Credentials expired or app re-installed; regenerate token and update config |
| Bot connected but silently ignores YOUR DMs/mentions | Inbound authorization default-deny (see "Inbound Authorization" below). Check gateway journal for `[Slack] Early reject of unauthorized user <U...>` — the message is dropped at intake before the agent ever sees it |

### Inbound Authorization (why a connected bot won't answer)

A **connected** Slack bot (gateway active, `hermes mcp test slack` ✓, can list users / post to home channel) can still ignore every inbound message. This is not a connection failure — it's the authorization gate in `gateway/authz_mixin.py:_is_user_authorized`, which **defaults to DENY** (per SECURITY.md, a network-exposed adapter must have an allowlist). The adapter drops the message at the front gate (`[Slack] Early reject of unauthorized user` in the journal) before the agent loop ever starts.

Authorization for Slack resolves in this order; the first hit wins, else deny:

1. `SLACK_ALLOWED_USERS` env (comma-separated user IDs) — or global `GATEWAY_ALLOWED_USERS`
2. Chat-scoped allowsets for group/forum (`group_allow_from` in `platforms.slack.extra`, or `SLACK_GROUP_ALLOWED_*`)
3. **DM pairing store** — `~/.hermes/platforms/pairing/<platform>-approved.json` (e.g. `slack-approved.json`). `is_approved(platform, user_id)` grants authorization independently of the env allowlist
4. `SLACK_ALLOW_ALL_USERS=true` / `GATEWAY_ALLOW_ALL_USERS=true` (fail-open, avoid)
5. Fallback: **default-deny**

Corollary: `platforms.slack.home_channel.chat_id` drives **outbound delivery targeting only** — it does NOT authorize inbound users. A user can be in the home channel and still be rejected. That's why Telegram works (its pairing store approves `user_id`, e.g. `61463612`) while Slack silently rejects the same human who was never paired.

**Diagnose:** the rejected ID is in the journal, e.g. `hafizmohdrizal` = `U04A3PR9294`. Confirm which gate is empty:
```bash
# connection OK? (gateway up, tools discoverable)
hermes gateway status; hermes mcp test slack
# is the user approved? (compare across platforms)
ls -la ~/.hermes/platforms/pairing/            # telegram-approved.json present, slack-approved.json missing = never paired
# is an env allowlist set? (empty = default-deny)
grep -iE "ALLOWED_USERS" ~/.hermes/.env
```

**Fix (operator action — not scriptable from the gateway):** add the user to `SLACK_ALLOWED_USERS=U0A...,U0B...` (comma-separated, no spaces) in `~/.hermes/.env`, OR approve the pairing. Then restart the gateway from a **separate shell** (the in-tree restart block applies — see Gateway Restart Blockade).

### CLI Setup Pitfalls

When using `hermes mcp add slack` (instead of manual YAML editing):

- **`--args` must be the LAST flag.** The `--env` flags must come BEFORE `--args`:
  ```bash
  hermes mcp add slack \
    --command npx \
    --connect-timeout 60 \
    --env "SLACK_BOT_TOKEN=$SLACK_BOT_TOKEN" \
    --env "SLACK_TEAM_ID=T04B035410Q" \
    --args "-y,@modelcontextprotocol/server-slack"
  ```
  If `--env` comes after `--args`, the env vars get appended to the args array instead of the `env:` section.

- **Token redaction can silently drop `SLACK_BOT_TOKEN`.** Hermes' credential redaction system masks `xoxb-*` tokens in output. This can cause the token value to be lost when `hermes mcp add` writes the config, leaving `SLACK_TEAM_ID` present but `SLACK_BOT_TOKEN` missing. If the saved config shows `env:` with only `SLACK_TEAM_ID`, you'll need to patch `~/.hermes/config.yaml` directly:

  ```python
  # Python script — reads token from .env, patches config.yaml, never prints the value
  with open('/home/ubuntu/.hermes/.env') as f:
      for line in f:
          if line.startswith('SLACK_BOT_TOKEN='):
              token = line.strip().split('=', 1)[1]
              break

  with open('/home/ubuntu/.hermes/config.yaml') as f:
      config = f.read()

  old_block = """  slack:
      command: npx
      ...
      SLACK_TEAM_ID: T04B035410Q
      ...
      enabled: false"""

  new_block = old_block.replace('SLACK_TEAM_ID: T04B035410Q',
                                f'SLACK_BOT_TOKEN: {token}\n      SLACK_TEAM_ID: T04B035410Q') \
                       .replace('enabled: false', 'enabled: true')

  config = config.replace(old_block, new_block)
  with open('/home/ubuntu/.hermes/config.yaml', 'w') as f:
      f.write(config)
  ```

  Then verify with `hermes mcp test slack`.

- **Args format in saved config.** After `hermes mcp add`, the saved config may have args as a single comma-separated string rather than separate YAML list entries:
  ```yaml
  # WRONG — single argument, won't work
  args:
    - -y,@modelcontextprotocol/server-slack

  # CORRECT — two separate arguments
  args:
    - -y
    - "@modelcontextprotocol/server-slack"
  ```
  If `hermes mcp test` fails with a connection error, check the args format and patch accordingly.

### Gateway Restart Blockade

After adding/changing MCP server config, the gateway must restart for the new tools to load. However, **the gateway blocks ALL restart attempts from within its own process tree**:

```
Error: Blocked: command/script cannot restart or stop the gateway from inside the gateway process.
SIGTERM propagates to child processes. Run `hermes gateway restart` from a separate shell.
```

This block applies to:
- `systemctl --user restart hermes-gateway.service`
- `hermes gateway restart`
- `at now + 1 minute` scheduled commands
- Cron jobs with gateway lifecycle commands (deep guard #30719 rejects them at creation time)
- Any shell that inherits the gateway PID tree

**The ONLY reliable fix** is to run the restart from a **separate shell** — a fresh SSH session or a TTY not descended from the gateway process:

```bash
hermes gateway restart
```

**Cron no_agent scripts — technical note:** `--script` with `no_agent=true` expects a **file path** relative to `~/.hermes/scripts/`, not an inline shell command. Even with the correct path, cron creation rejects gateway restart patterns. This is intentional to prevent SIGTERM-respawn loops.

The gateway comes back up in ~10s and discovers MCP servers. The current session terminates; start a fresh conversation to verify the new tools are loaded.

### Verification

After restart, confirm the MCP server is active:

```bash
hermes mcp test slack
```

Expected output:
```
Testing 'slack'...
  Transport: stdio → npx
  Auth: none
  ✓ Connected (Nms)
  ✓ Tools discovered: 8
    slack_list_channels     ...
    slack_post_message      ...
    ...
```

### Package Deprecation

The official `@modelcontextprotocol/server-slack@2025.4.25` npm package shows as deprecated. Alternatives:

- `@zencoderai/slack-mcp-server` — another npm package, similar tool set
- `korotovsky/slack-mcp-server` — Go-based, more feature-rich (DMs, group DMs, smart history fetch)
- Update the `args` in config.yaml to point at the replacement package when the official one stops working.

---

## Related

- `references/gateway-restart-blockade.md` — full error chain reproduction data for all blocked restart paths
- `slack-incident` — Slack incident channel orchestration (uses same Slack credentials, but is a user-owned skill — run `hermes curator adopt slack-incident` before curator can update it)
- `hermes-agent` / `references/native-mcp.md` — general MCP configuration reference
- `node-incident-recovery`, `zabbix-api-investigation` — NOC skills that rely on chatops for incident messaging
- `references/slack-file-download.md` — download files (PDFs, images) shared in Slack channels via the REST API, for extraction and analysis