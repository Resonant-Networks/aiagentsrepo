# Herdr Agent State Integration

Reports active agent sessions, lifecycle transitions, and resumable session identifiers to Herdr multiplexer panes across multiple agent runtimes.

## Supported Implementations

1. **Hermes Agent** (`hermes/`):
   - `plugin.yaml`: Manifest registering `herdr-agent-state`.
   - `__init__.py`: Hooks into `on_session_start`, `on_session_reset`, and `pre_llm_call`. Dispatches session reporting via `herdr pane report-agent-session`.

2. **OpenCode** (`opencode/`):
   - `herdr-agent-state.js`: Node.js socket client communicating with the Herdr UNIX socket (`HERDR_SOCKET_PATH`) for streaming session status (`idle`, `working`, `blocked`).

3. **Antigravity CLI** (`antigravity/`):
   - `herdr-agent-state.sh`: POSIX shell + Python hook triggered before agent invocation (`PreInvocation`).
   - `hooks.json`: Registration configuration for Antigravity CLI.
