#!/bin/bash
# Hermes cron wrapper: refresh FNT session ID every 4 hours (system crontab).
# Patched: after a successful refresh that CHANGED the session, restart the
# cable-scanner Docker container + FNT MCP server so they load the new token.
# Quiet on success; logs to a file. Non-zero/error -> alert via cron mail.

LOG=/home/ubuntu/.hermes/skills/devops/fnt-session-fetch/refresh.log
EX=/home/ubuntu/.hermes/skills/devops/fnt-session-fetch/scripts/fnt_session_extractor.js
node_bin=/home/ubuntu/.nvm/versions/node/v22.23.2/bin/node
touch "$LOG"

cd /home/ubuntu/cable-scanner-fnt || { echo "$(date -Is) ERR cd failed" >> "$LOG"; exit 1; }

PREV=""
[ -f .env ] && PREV=$(grep -E '^FNT_SESSION_ID=' .env | cut -d= -f2-)

OUT=$($node_bin "$EX" 2>&1)
RC=$?

if [ $RC -ne 0 ]; then
  echo "$(date -Is) FAIL rc=$RC" >> "$LOG"
  echo "$OUT" | tail -5 >> "$LOG"
  echo "$OUT" | tail -5
  exit $RC
fi

NEW=$(grep -E '^FNT_SESSION_ID=' .env | cut -d= -f2-)
echo "$(date -Is) refreshed ${#NEW}-char session (was ${#PREV}-char)" >> "$LOG"

if [ -n "$NEW" ] && [ "$NEW" != "$PREV" ]; then
  echo "FNT session refreshed (now ${#NEW} chars). Restarting consumers..."
  # Restart cable-scanner Docker container so it loads the new session
  if sudo docker compose up -d --force-recreate >> "$LOG" 2>&1; then
    echo "$(date -Is) cable-scanner container recreated (loaded ${#NEW}-char session)" >> "$LOG"
  else
    echo "$(date -Is) WARN cable-scanner recreate failed" >> "$LOG"
  fi
  # Restart FNT MCP server (Hermes watchdog auto-respawns it, reloads .env)
  if pkill -f 'fnt-mcp/server.py'; then
    echo "$(date -Is) fnt-mcp server restarted (watchdog respawn)" >> "$LOG"
  fi
  echo "cable-scanner + fnt-mcp restarted."
fi
exit 0