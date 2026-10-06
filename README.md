# Resonant Networks — AI Agents, Plugins & Skills Repository

A unified, production-grade repository consolidating autonomous **AI Agents**, cross-runtime **Plugins**, and extensible **Skills** for network operations, infrastructure engineering, and automated software development.

---

## 🏛️ Repository Architecture

```
aiagentsrepo/
├── agents/                       # Autonomous Agent Personas, Contracts & Runtimes
│   ├── hermes/                   # Autonomous NOC & Incident Response Agent (SOUL.md, guardrails)
│   ├── antigravity/              # Antigravity agent configuration, conventions, subagents, and hooks
│   ├── codex/                    # Codex TDD contracts, structure limits, and Zammad integrations
│   └── workflows/                # Agent orchestration and landing pages (AgentFlow UI)
│
├── plugins/                      # Cross-Runtime Plugins & Hooks
│   ├── herdr-agent-state/        # Multiplexer pane lifecycle reporter (Hermes, OpenCode, Antigravity)
│   ├── openchamber/              # Multi-project, worktree, and session control plugin
│   ├── opencode/                 # Session auto-renaming and extension tools
│   └── zammad-mcp/               # FastMCP Codex package with references and manifests
│
└── skills/                       # Standardized Agent Skills (SKILL.md)
    ├── devops/                   # NOC, fiber fault analysis, Zabbix/Zammad probes, ChatOps, FNT Command
    ├── antigravity/              # Antigravity custom skill development, guides, and UI navigations
    ├── autonomous-ai-agents/     # Playbooks for Claude Code, Codex, OpenCode, Hermes, Computer Use
    ├── software-development/     # TDD cycle, systematic debugging, code review, refactoring
    ├── github/                   # PR workflows, codebase inspection, review automation
    ├── codex-plugins/            # Digest skills for Zammad MCP and code quality
    ├── research/                 # ArXiv search, web monitoring, grounded citations, wiki compilation
    ├── productivity/             # Google Workspace, Airtable, Notion, meeting items, PDF/DOCX/XLSX
    ├── mlops/                    # Model evaluation, Hugging Face Hub, inference optimization
    ├── creative/                 # Architecture diagrams, Excalidraw, Manim video, ASCII art
    └── communication/            # Email triage, Slack/Discord bots, Apple notes/reminders, social
```

---

## 🤖 AI Agents

| Agent | Focus Area | Key Features & Guardrails |
|---|---|---|
| **Hermes Agent** | NOC & Network Incident Response | Strict read-only diagnostic mode, Adtran ALM fiber triangulation, Zabbix/Zammad correlation, Slack war-room management |
| **Antigravity Agent** | Full-Stack Systems & Architecture | Built-in reactive subagents (`research`, `image-generator`, `self`), dynamic tool discovery, and MCP bindings |
| **Codex Agent** | Strict TDD & Clean Code | Enforces RED-GREEN-REFACTOR cycles, $\le 3$ nesting depth, $\le 30$ LOC per construct, and $\le 200$ LOC per file |

---

## 🔌 Plugins

- **`herdr-agent-state`**: Multi-runtime plugin ensuring agent session continuity in terminal multiplexers (implemented across Python, TypeScript, and POSIX shell).
- **`openchamber`**: Agent tool providing unified API access to projects, sessions, scheduled tasks, and isolated Git worktree branches.
- **`zammad-mcp`**: Codex plugin integration with FastMCP server definitions, triage prompts, and Codacy analysis.

---

## 🛠️ Key DevOps & NOC Skills

- **`slack-incident`**: Automated incident response pipeline. Spins up dedicated incident channels, invites on-call responders, displays the *Incident Rosetta Stone*, and runs background ALM OTDR triangulation.
- **`alm-fault-analysis`**: Real-time parsing and distance calculation for optical fiber breaks detected by Adtran ALM devices.
- **`zabbix-api-investigation`**: Zero-dependency Python script (`zabbix_probe.py`) querying Zabbix JSON-RPC for active alarms, items, and historical telemetry.
- **`fnt-command-automation` & `fnt-session-extractor`**: Headless Playwright automation and REST queries for FNT Command infrastructure, rack layouts, and physical cable routes.
- **`infra-watchdog`**: Continuous health monitoring for internal Docker stacks, Portainer instances, and core network endpoints.

---

## 🔒 Security & Operational Guardrails

1. **No Destructive Autonomous Actions**: Production agents run in diagnostic/read-only mode. Configuration edits or container restarts require human review.
2. **Credential Hygiene**: All scripts consume credentials via environment variables (`SLACK_BOT_TOKEN`, `ZABBIX_USER`, `FNT_PASSWORD`) or external secret managers. No secrets are committed.
3. **Parity & Auditability**: Every infrastructure change is logged with verification commands and reversible rollback instructions (enforced by the `devops-log` skill).

---

## 🚀 Usage & Deployment

### Cloning
```bash
git clone https://github.com/Resonant-Networks/aiagentsrepo.git
cd aiagentsrepo
```

### Loading Skills
Skills are compatible with any agent runtime supporting the `SKILL.md` specification (including Antigravity, Hermes Agent, and OpenCode):
```bash
# Example: Point Hermes to a skill directory
hermes --skill ./skills/devops/slack-incident

# Example: Import skills into Antigravity
agy --add-dir ./skills/devops
```
