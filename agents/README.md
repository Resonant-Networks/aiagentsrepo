# AI Agents Directory

This directory contains autonomous agent specifications, personas, runtime configurations, subagents, and workflows across multiple agent frameworks.

## Directory Structure

```
agents/
├── hermes/
│   ├── SOUL.md                 # Autonomous NOC & Incident Response Agent Persona & Guardrails
│   ├── AGENTS.md               # Hermes operating contract and diagnostic rules
│   └── config.example.yaml     # Runtime configuration template (LLMs, tools, channels)
├── antigravity/
│   ├── AGENTS.md               # Workspace rules and conventions for Antigravity AI assistant
│   ├── scripts-AGENTS.md       # Ad-hoc automation scripts conventions
│   ├── hooks/                  # Antigravity CLI lifecycle hooks
│   │   ├── hooks.json
│   │   └── herdr-agent-state.sh
│   └── subagents/              # Pre-configured subagent specifications (research, image-generator, self)
│       └── subagents.json
├── codex/
│   ├── AGENTS.md               # Codex Agent operating contract (TDD, Python, code structure limits)
│   └── zammad/
│       ├── CLAUDE.md           # Repository conventions for FastMCP server development
│       └── marketplace.json    # Codex marketplace catalog entry
└── workflows/
    └── agentflow/
        └── app.js              # AgentFlow interactive workflow UI engine
```

## Agent Profiles

1. **Hermes Agent (Autonomous NOC & Incident Response)**:
   - Disciplined network diagnostics, Zabbix/Zammad correlation, Slack ChatOps coordination, and OTDR fault triangulation.
   - Enforces strict read-only execution guardrails to protect production network infrastructure.

2. **Antigravity Agent (Full-Stack Pair Programmer & Customization Engine)**:
   - Deep reasoning agent supporting skills, subagents, MCP integration, and reactive background orchestration.
   - Designed for software engineering, architecture, and system administration.

3. **Codex Agent (TDD Engineering Contract)**:
   - Rigorous RED-GREEN-REFACTOR contract.
   - Enforces structural code constraints: nesting depth $\le 3$, construct size $\le 30$ LOC, file size $\le 200$ LOC.
