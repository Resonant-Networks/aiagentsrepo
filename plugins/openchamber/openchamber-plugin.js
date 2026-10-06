
export const OpenChamberPlugin = async () => ({
  tool: {
    openchamber: {
      description: "Control OpenChamber projects, sessions, and scheduled tasks on the user's behalf. Sessions and scheduled tasks you create are for the user to follow and interact with; never use this tool to delegate parts of your own current task. Use one action per call. Scope with projectId or directory; omit both to use the current session directory. Session dispatches return immediately by default and you receive no notification when a dispatched session finishes, so never promise to report back on it; the user follows it in OpenChamber; a dispatched session needs no follow-up from you. If the user later asks how it went, use session.messages (add wait to block until it is idle, lastAssistant for just the final answer) — session.send always sends a NEW prompt and never just waits. Set wait only when the user asks or the next step requires the completed result. Session and worktree deletion are unavailable.",
      args: {
        action: { type: "string", enum: ["projects.list","models.list","session.list","session.create","session.send","session.fork","session.status","session.messages","schedule.list","schedule.create","schedule.run","schedule.delete","schedule.toggle"], oneOf: [{"const":"projects.list","description":"List configured projects; no parameters"},{"const":"models.list","description":"Show default, favorite, and recent model preferences; no parameters"},{"const":"session.list","description":"List sessions; optional directory, limit (default 10), all, or withStatus"},{"const":"session.create","description":"Create a session in the current directory by default; prompt is optional"},{"const":"session.send","description":"Send a new prompt to sessionId; scope with projectId or directory"},{"const":"session.fork","description":"Fork sessionId; messageId selects the boundary; prompt is optional"},{"const":"session.status","description":"Check sessionId status; directory defaults to the current session"},{"const":"session.messages","description":"Read text-only messages and current sessionStatus for sessionId; directory and limit 10 are defaults"},{"const":"schedule.list","description":"List tasks and scheduler status; scope with projectId or directory"},{"const":"schedule.create","description":"Create task; requires name, prompt, model, and one schedule selector"},{"const":"schedule.run","description":"Run taskId; scope with projectId or directory"},{"const":"schedule.delete","description":"Delete taskId; scope with projectId or directory"},{"const":"schedule.toggle","description":"Enable or disable taskId; requires the disabled boolean"}], description: "OpenChamber action to perform" },
        parameters: { type: "object", properties: {"projectId":{"type":"string","description":"Configured project ID; do not combine with directory"},"directory":{"type":"string","description":"Absolute checkout or session directory; defaults to the current session directory"},"sessionId":{"type":"string"},"messageId":{"type":"string","description":"Optional fork boundary message ID"},"taskId":{"type":"string"},"title":{"type":"string"},"prompt":{"type":"string"},"model":{"type":"string","description":"Model in provider/model format. When the user names no model: for session.create pick a suitable one from models.list favorites or recents (omit if there are none); for send and fork omit it — the session reuses its previous model"},"agent":{"type":"string","description":"OpenCode agent name; new sessions default to the build agent and existing sessions keep their previous one. Set only when the user explicitly requests a different agent"},"variant":{"type":"string","description":"Model variant; use only when the user explicitly requests it"},"worktree":{"type":"string","description":"New worktree name for session.create. Omit by default; use only when the user explicitly asks for an isolated worktree. Uncommitted changes do not carry over into a new worktree"},"branch":{"type":"string","description":"Branch name for the new worktree"},"startRef":{"type":"string","description":"Git ref used to create the new worktree"},"setUpstream":{"type":"boolean","description":"Make the new worktree branch track its upstream"},"goal":{"type":"boolean","description":"Run the dispatched prompt in Goal Mode; use only when the user explicitly requests it"},"goalTokenBudget":{"type":"integer","minimum":1000,"maximum":100000000,"description":"Goal token budget; requires goal"},"wait":{"type":"boolean","description":"Wait for current session activity to become idle. Omit by default; use only when the user asks or the next step requires the completed result"},"timeout":{"type":"integer","minimum":1,"maximum":86400,"description":"Wait timeout in seconds (default 600); requires wait"},"lastAssistant":{"type":"boolean","description":"Return the last assistant text; create/send/fork require wait"},"limit":{"type":"integer","minimum":1,"description":"Maximum sessions or messages to return (default 10)"},"all":{"type":"boolean","description":"Include archived sessions or all messages, depending on the action"},"last":{"type":"boolean","description":"Return only the last matching session message"},"withStatus":{"type":"boolean","description":"Include authoritative status in session.list"},"role":{"type":"string","enum":["all","user","assistant"],"description":"Message role filter"},"name":{"type":"string"},"daily":{"type":"string","description":"Daily run time in HH:mm format"},"weekly":{"type":"string","description":"Comma-separated weekdays; 0=Sunday and 6=Saturday"},"once":{"type":"string","description":"One-time run date in YYYY-MM-DD format"},"time":{"type":"string","description":"Weekly or one-time run time in HH:mm format"},"cron":{"type":"string","description":"Cron expression"},"timezone":{"type":"string","description":"IANA timezone"},"disabled":{"type":"boolean","description":"true disables and false enables; required for schedule.toggle"}}, additionalProperties: false, description: "Inputs for the action; use an empty object when none are needed" },
      },
      async execute(input, context) {
        const args = { ...(input.parameters ?? {}), action: input.action }
        const actionTitles = {"projects.list":"List configured projects","models.list":"Show model preferences","session.list":"List sessions","session.create":"Create a session","session.send":"Send a prompt","session.fork":"Fork a session","session.status":"Check session status","session.messages":"Read session messages","schedule.list":"List scheduled tasks","schedule.create":"Create a scheduled task","schedule.run":"Run a scheduled task","schedule.delete":"Delete a scheduled task","schedule.toggle":"Enable or disable a scheduled task"}
        const title = Object.hasOwn(actionTitles, args.action) ? actionTitles[args.action] : args.action
        context.metadata({
          title,
          metadata: {
            openchamber: {
              schemaVersion: 1,
              action: args.action,
              description: title,
            },
          },
        })
        const endpoint = process.env.OPENCHAMBER_AGENT_TOOL_URL
        const token = process.env.OPENCHAMBER_AGENT_TOOL_TOKEN
        const failure = (payload) => ({
          title,
          output: JSON.stringify(payload),
          metadata: { openchamber: { schemaVersion: 1, action: args.action, description: title, ok: false } },
        })
        if (!endpoint || !token) {
          return failure({ schemaVersion: 1, ok: false, action: args.action, error: { message: "OpenChamber managed tool connection is unavailable" } })
        }

        try {
          const response = await fetch(endpoint, {
            method: "POST",
            headers: {
              authorization: "Bearer " + token,
              "content-type": "application/json",
            },
            body: JSON.stringify({ input: args, contextDirectory: context.directory }),
            signal: context.abort,
          })
          const output = await response.text()
          let result = null
          try { result = JSON.parse(output) } catch {}
          const valid = result?.schemaVersion === 1 && typeof result?.ok === "boolean" && typeof result?.action === "string"
          context.metadata({
            title,
            metadata: {
              openchamber: {
                schemaVersion: 1,
                action: args.action,
                description: title,
                ok: valid && result.ok === true,
              },
            },
          })
          if (valid) return { title, output, metadata: { openchamber: { schemaVersion: 1, action: args.action, description: title, ok: result.ok === true } } }
          return failure({ schemaVersion: 1, ok: false, action: args.action, error: { message: "OpenChamber returned an invalid response", kind: "runtime", status: response.status } })
        } catch (error) {
          if (context.abort.aborted) throw error
          return failure({ schemaVersion: 1, ok: false, action: args.action, error: { message: error instanceof Error ? error.message : String(error), kind: "runtime" } })
        }
      },
    },
  },
})
