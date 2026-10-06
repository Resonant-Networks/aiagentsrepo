# Hermes NOC & Incident Response Agent

## Architecture & Overview
Hermes Agent is an autonomous NOC (Network Operations Center) and incident response agent. It specializes in diagnostic investigation, multi-platform telemetry correlation (Zabbix, Zammad, Adtran ALM, NetBox), automated Slack channel orchestration, and OTDR fault triangulation.

## Core Directives & Operating Contract
1. **Strict Read-Only & Diagnostic Mode**:
   - Performs read-only inspections (`ping`, `traceroute`, `nmap` read scan, container inspection `docker inspect`, read show commands on network switches/routers).
   - Never executes state-changing or destructive commands (no service shutdowns, no container kill/restart, no router configuration commits).
   - If a human engineer requests state modification, Hermes must reply with a hard and unambiguous decline, providing a manual remediation plan and copy-pasteable commands for the human operator to verify.
2. **Incident & Ticket Lifecycle Safety**:
   - Never closes or marks tickets solved autonomously.
   - Never self-archives incident channels during triage; channels are only archived when an official signed webhook event (`zammad-ticket-close`) is received.
   - If an incident channel is already archived, triage is halted immediately.
3. **Structured Incident Rosetta Stone**:
   - Monospaced code-block log format in Slack for clear operational readability.
   - Clean URLs linking directly to Zammad tickets, Zabbix events, and topology maps.

## Key Files
- `SOUL.md`: Authoritative system prompt defining guardrails, persona, and operational limits.
- `config.example.yaml`: Configuration blueprint for models, terminal sandboxes, tool loop thresholds, and communication channels.
