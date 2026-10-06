# OpenChamber Plugin

`openchamber-plugin.js` is an agent-facing tool that allows LLMs to control OpenChamber projects, sessions, git worktree branches, and scheduled tasks directly.

## Capabilities
- **Project & Model Querying**: `projects.list`, `models.list`
- **Session Management**: `session.list`, `session.create`, `session.send`, `session.fork`, `session.status`, `session.messages`
- **Scheduler Control**: `schedule.list`, `schedule.create`, `schedule.run`, `schedule.delete`, `schedule.toggle`
- **Git Worktree Isolation**: Dispatches isolated worktrees for sub-tasks without mutating the primary working tree.
