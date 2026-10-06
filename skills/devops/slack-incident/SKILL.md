---
name: slack-incident
description: "Manage Slack incident channels: create #incident-<ticket-id>, invite responders, post read-only diagnostic briefings with Incident Rosetta Stone, and archive ONLY upon authorized ticket closure webhook."
version: 1.2.0
platforms: [linux]
metadata:
  hermes:
    tags: [NOC, Incident, Slack, ChatOps, Guardrails, RosettaStone]
---

# Slack Incident Management & NOC Guardrails

Use this skill to orchestrate incident channels on Slack for incoming NOC tickets while adhering to strict read-only guardrails and proper Slack mrkdwn.

## Mandatory Guardrails

1. **Slack Formatting (mrkdwn):**
   - Use `*bold*` (NOT `**bold**`).
   - Use `<http://url|Link Text>` (NOT `[Link Text](http://url)`).
   - Use `_italic_` for italics.
   - Use `•` for bullet points.

2. **NOC Incident Dispatch Card (Clean Native Slack Mrkdwn, No Code Blocks, No Lines):**
   Every incident channel must feature a clean, mobile-friendly "NOC Incident Dispatch" card using native Slack mrkdwn without code blocks or horizontal ASCII divider lines:
   ```text
   🚨 *NOC INCIDENT DISPATCH* | *SEVERITY: 🔴 DISASTER*

   • *Zammad Ticket:* <http://100.80.103.95:8084/#ticket/zoom/<ID>|#<NUMBER> (DB #<ID>)>
   • *Zabbix Event:* <http://100.80.103.95:8083/tr_events.php?eventid=<EVENT_ID>|Event #<EVENT_ID>>
   • *Target Group:* <GROUP>
   • *Affected Device:* <HOST>
   • *Incident Trigger:* <TRIGGER>
   • *Assigned Responder:* <@USER_ID>

   🔗 *QUICK LINKS*
   • <http://100.80.103.95:8084/#ticket/zoom/<ID>|Zammad Ticket #<NUMBER>> • <http://100.80.103.95:8083/tr_events.php?eventid=<EVENT_ID>|Zabbix Event #<EVENT_ID>> • <http://<DEVICE_IP>|Device WebGUI>
   ```

3. **Plan & Probe Only — No Configuration Execution:**
   - Run only read-only network inspection commands (`ping`, `traceroute`, `clab inspect`, `docker inspect`, `show` reports on routers).
   - Never run configuration changes, commits, restarts, or deletions.
   - If an engineer asks you to execute a fix in the channel, reply with a firm **NO** and present the recommended commands for them to execute manually.

4. **Never Self-Solve or Self-Archive:**
   - Never close or resolve tickets on your own.
   - Never archive the incident channel during investigation or in response to engineer chat.
   - Channel archiving is ONLY permitted when executing the official `zammad-ticket-close` webhook handler.

5. **Never Unarchive Closed Channels (Abort on `is_archived`):**
   - Never call `conversations.unarchive` or attempt to unarchive a channel.
   - If an incident channel is archived or you encounter `is_archived`, the incident has ALREADY been closed/resolved.
   - Immediately abort the workflow and complete your turn. Do NOT retry or force-post.

6. **Pattern 2: Two-Stage Notification for Optical Incidents:**
   - **Stage 1 (T=0s)**: `rosetta` immediately provisions the channel `#incident-<ID>`, invites responders, and posts the clean `NOC INCIDENT DISPATCH` card in sub-second time.
   - **Stage 2 (T+30~60s Background)**: If the incident is optical/ALM, `rosetta` automatically spawns `triangulate_alm.py` in the background with `--wait`. Once the OTDR shot finishes, it replies directly into the dispatch thread with the exact GPS coordinates, nearest landmark, and Google Maps pin.

## Commands

1. **Initialize Incident & Post Dispatch Card (Stage 1 + Auto Stage 2):**
   ```bash
   python3 ~/.hermes/skills/slack-incident/scripts/slack_incident.py rosetta --ticket-id "<ID>" --number "<NUMBER>" --title "<TITLE>" --device "<HOST>" --group "<GROUP>" --users "U04A3PR9294"
   ```
   This automatically creates `#incident-<ID>`, invites responders, posts the NOC Incident Dispatch card, and for optical alarms automatically initiates background OTDR triangulation.

2. **Standalone ALM Optical Fault Triangulation:**
   ```bash
   python3 ~/.hermes/skills/slack-incident/scripts/triangulate_alm.py --port <PORT> [--wait] [--timeout 60] [--channel <CHANNEL>] [--thread-ts <TS>]
   ```
   Queries ALM REST API, retrieves route KML polyline, computes cumulative Haversine distance, and returns GPS coordinates and Google Maps links.

3. **Close & Archive Channel (ONLY on `zammad-ticket-close` Webhook):**
   ```bash
   python3 ~/.hermes/skills/slack-incident/scripts/slack_incident.py close --ticket-id "<ID>" --number "<NUMBER>"
   ```
   This posts the clean resolution card and archives the channel in one step.

4. **Post Additional Updates to Channel:**
   ```bash
   python3 ~/.hermes/skills/slack-incident/scripts/slack_incident.py post --channel "incident-<ID>" --message "<UPDATE_MESSAGE>"
   ```

