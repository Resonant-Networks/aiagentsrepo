# Skills Library

A comprehensive, categorized repository of agent skills adhering to the open Agent Skills standard (`SKILL.md` format with frontmatter metadata, trigger conditions, executable workflows, scripts, and references).

---

## Skill Categories

### 1. [DevOps & Network Operations (`devops/`)](./devops/)
Specialized network operations, incident response, observability, and infrastructure automation:
- **`alm-fault-analysis`**: Triangulates and investigates Adtran ALM optical fiber cuts and degradation events.
- **`chatops-integration`**: Gateway to Slack and Teams ChatOps, inbound auth handling, and file downloads.
- **`devops-log`**: Creates structured session logs tracking changes, verifications, and rollback scripts.
- **`docker-config-propagation`**: Docker configuration propagation across staging and production hosts.
- **`fnt-command-automation`**: Automated queries to FNT Command physical cabling, ODFs, and patch panels.
- **`fnt-elid-fetcher`**: Retrieves live random ELIDs across Cable, Rack, and Equipment modules for verification (`get_random_elid.py`).
- **`fnt-session-extractor`**: Headless Playwright script extracting active `sessionid` cookies from FNT Command (`fnt_session_extractor.js`).
- **`fnt-session-fetch`**: Automated session refresh daemon and credential wrapper (`fnt_refresh_wrapper.sh`).
- **`infra-watchdog`**: Proactive infrastructure host monitor and container health checker (`host_monitor.py`, `service_probe.py`).
- **`md-pdf`**: Converts Markdown documentation to high-styled PDFs using Pandoc + WeasyPrint with Notion CSS and company branding.
- **`node-incident-recovery`**: Disaster recovery runbooks for Containerlab nodes and network switches.
- **`sdlc-review`**: Automated review against security, CI/CD parity, and architecture quality gates.
- **`server-service-inventory`**: Full system, network, and package inventory generation.
- **`slack-incident`**: Automated war room generation (`#incident-<id>`), responder onboarding, and ALM OTDR triangulation (`slack_incident.py`, `triangulate_alm.py`).
- **`tailscale-subnet-routing`**: Tailscale subnet router diagnostics, route acceptance, and connectivity audits.
- **`zabbix-api-investigation`**: Zabbix JSON-RPC API diagnostic queries, event correlation, and trigger analysis (`zabbix_probe.py`).

### 2. [Antigravity Customizations (`antigravity/`)](./antigravity/)
Guides and extensions for the Antigravity agent runtime:
- **`agy-customizations`**: Deep-dive guide to skills, rules, hooks, and MCP servers in Antigravity.
- **`antigravity_guide`**: Master reference manual, slash commands, and configuration sitemap.
- **`automation`**: Automation foundation and testing contracts.
- **`generative_ui`**: Interactive generative UI components and artifact design.
- **`migrate-workflows`**: Guidance for migrating legacy scripts into Antigravity workflows.
- **`permissioned-github`**: Principle of least privilege for GitHub agent actions.
- **`plugin`**: Plugin architecture and lifecycle integration.
- **`ui-plugin-navigation`**: Navigation heuristics for web and desktop frontends.

### 3. [Autonomous AI Agents (`autonomous-ai-agents/`)](./autonomous-ai-agents/)
Operational playbooks for running and orchestrating autonomous agent frameworks:
- **`claude-code`**: Claude Code CLI agent guidelines.
- **`codex`**: OpenAI Codex CLI patterns and prompt architecture.
- **`computer-use`**: OS and GUI computer use workflows.
- **`hermes-agent`**: Hermes Agent core architecture, skins, widgets, and templates.
- **`merge-reconciler`**: Multi-agent git merge conflict reconciliation.
- **`opencode`**: OpenCode CLI agent execution and sub-task coordination.

### 4. [Software Development (`software-development/`)](./software-development/)
Disciplined engineering and debugging practices:
- **`dogfood`**: Internal dogfooding and QA verification.
- **`hermes-agent-skill-authoring`**: Standardized authoring rules for new skills.
- **`inspecting-hermes-desktop-dom`**: Desktop DOM inspection and accessibility audits.
- **`node-inspect-debugger`**: Node.js V8 inspector debugging.
- **`plan`**: High-leverage execution planning.
- **`python-debugpy`**: Remote python debugging with debugpy.
- **`requesting-code-review`**: Structured review requests and feedback formatting.
- **`simplify-code`**: Eliminates cognitive complexity and dead paths.
- **`spike`**: Time-boxed architectural spikes and prototypes.
- **`systematic-debugging`**: Scientific root-cause isolation.
- **`test-driven-development`**: Strict RED-GREEN-REFACTOR cycle enforcement.

### 5. [GitHub & Collaboration (`github/`)](./github/)
- **`codebase-inspection`**: Deep repository structural analysis.
- **`github-auth`**: Authentication and credential helpers for GitHub CLI and git.
- **`github-code-review`**: High-signal pull request review workflows.
- **`github-issue-to-pr`**: End-to-end issue decomposition to pull request.
- **`github-issues`**: Issue triaging, labeling, and prioritization.
- **`github-pr-workflow`**: Pull request authoring, changelogs, and branch hygiene.
- **`github-repo-management`**: Repository settings, branch protection, and secrets management.

### 6. [Codex Plugins (`codex-plugins/`)](./codex-plugins/)
- **`zammad-mcp-issue-digest`**: Aggregates and synthesizes open Zammad tickets.
- **`zammad-mcp-pr-digest`**: Summarizes pull requests and changelog impact.
- **`zammad-mcp-quality`**: Audits codebase against strict quality gates and coverage thresholds.

### 7. [Research & Analysis (`research/`)](./research/)
- **`arxiv`**: Search and summarize academic papers from arXiv.
- **`blogwatcher`**: Monitor engineering blogs and technical announcements.
- **`competitor-news-monitor`**: Industry competitive intelligence gathering.
- **`grounded-citations`**: Fact-checking and evidence-backed citation attribution.
- **`llm-wiki`**: Knowledge graph and personal wiki compilation.
- **`research-paper-writing`**: Academic drafting, LaTeX formatting, and literature review.

### 8. [Productivity & Operations (`productivity/`)](./productivity/)
- **`airtable`**, **`document-to-action-items`**, **`docx`**, **`google-workspace`**, **`maps`**, **`meeting-action-items`**, **`nano-pdf`**, **`notion`**, **`ocr-and-documents`**, **`pdf`**, **`powerpoint`**, **`product-price-monitor`**, **`teams-meeting-pipeline`**, **`weekly-review-planning`**, **`xlsx`**.

### 9. [MLOps & Model Operations (`mlops/`)](./mlops/)
- **`evaluation`**: LLM evaluation benchmark harness.
- **`huggingface-hub`**: Hugging Face model and dataset integration.
- **`inference`**: Fast inference runtime optimizations.
- **`models`**: Model weight management and quantizations.

### 10. [Creative & Design (`creative/`)](./creative/)
- **`architecture-diagram`**, **`ascii-art`**, **`ascii-video`**, **`baoyu-infographic`**, **`claude-design`**, **`comfyui`**, **`design-md`**, **`excalidraw`**, **`humanizer`**, **`manim-video`**, **`p5js`**, **`popular-web-designs`**, **`pretext`**, **`sketch`**, **`songwriting-and-ai-music`**, **`touchdesigner-mcp`**.

### 11. [Communication & Social (`communication/`)](./communication/)
- **`apple-notes`**, **`apple-reminders`**, **`email-inbox-triage`**, **`findmy`**, **`gif-search`**, **`himalaya`**, **`imessage`**, **`obsidian`**, **`openhue`**, **`songsee`**, **`xurl`**, **`youtube-content`**.
