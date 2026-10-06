---
name: docker-config-propagation
description: "Reaching a running container: mount vs baked-in env."
version: 1.0.0
author: hermes-curator
license: MIT
metadata:
  hermes:
    tags: [docker, env, dotenv, config, container, deployment]
    related_skills: [node-incident-recovery, fnt-command-automation]
---

# Docker Config Propagation

Verifying that an application config / env variable edit has actually taken effect in a running containerized app — before telling anyone the fix is "done".

## When to Use

- You edited a host `.env` (or a config file) and need to know whether the running Docker app picked it up.
- A user asks "was that change for the docker version or the host/vite version?"
- You must restart/rebuild a container so it reads a new secret, session token, or config value.
- A container-app appears to be a plain host process but is actually container-resident.

## The Core Question

**Is the config bind-mounted, or baked into the image?** This single fork decides everything.

```bash
# 1. Is the file/path bind-mounted from the host?
docker inspect <NAME> -f '{{json .Mounts}}'

# 2. Is the env var baked into the container's env (image ENV or COPY+ENV)?
docker inspect <NAME> -f '{{json .Config.Env}}' | tr ',' '\n' | grep -i <VAR>
```

- **Bind-mounted** (`<host-path> -> /app/...`) → a host-file edit **is already live** in the container. No rebuild.
- **Baked into `Config.Env` / image** → a plain `docker restart` **will NOT** pick up a new value; the old env is baked in. You must **rebuild** with the new value:
  ```bash
  docker compose up -d --build <service> \
    # or, non-compose:
  docker run --env-file /abs/host/.env ... <image>
  ```

### Third case: compose `env_file:` + `environment:` (resolved at container START)

A common `docker-compose.yml` pattern answers the question differently — neither bind-mount nor image-baked:

```yaml
  myservice:
    environment:
      - FOO=${FOO:-default}
    env_file: [".env"]
```

The env is read from the compose file's `.env` **when the container is STARTED** (compose substitution + `env_file`), and is NOT part of the image and NOT a live bind-mount. Consequences:

- Container `inspect .Mounts` will be `[]` and there will be no `/app/.env` in the image — do NOT conclude "the host `.env` doesn't reach it" or "it's baked in".
- **Patching the host `.env` + `docker restart <svc>` IS sufficient** — the next start re-reads `.env`. No image rebuild needed for an env-value change (rebuild is only for code/binary changes).
- Verify the compose file: `grep -nE 'env_file|environment' docker-compose.yml`. If `env_file`/interpolation drives the var, restart (not rebuild) is the fix.

## Is the app even container-resident?

A service that looks like a native process may actually run inside a container (path like `/app/node_modules`, or the container runs it via `docker exec`). Confirm before editing host files:

```bash
docker ps -a | grep -i <NAME>                 # does a container exist for it?
ss -tlnp | grep <PORT>                         # who owns the listening port?
sudo ls -l /proc/<PID>/cwd                     # working dir → /app? in-container.
```

## Pitfalls

- **Process path inside the container (`/app/...`) is the giveaway**: the vite/node binary shows a container mount path, meaning the app is container-resident, not a bare host process.
- **`.env` may have TWO consumers**: a host vite/dev instance AND the container. Editing one path does not fix the other unless it's the same bind-mounted file.
- **Plain `docker restart` does not fix a baked-in env** — the stale value is in the image. Rebuild, or override at `docker run` time.
- **Verification beats assumption**: read `.Mounts` and `.Config.Env` from `docker inspect` before declaring a fix live.
- **In read-only/incident mode, do not run the rebuild/restart yourself** — hand the exact command to the human engineer.

## Verification

After a rebuild (run by the engineer), confirm the new value is live:
```bash
docker inspect <NAME> -f '{{json .Config.Env}}' | tr ',' '\n' | grep -i <VAR>
docker exec <NAME> sh -c 'grep -n "^<VAR>=" /app/.env 2>/dev/null'
```
Then hit the app's real health/query path and confirm it no longer serves stale/demo data.

## Example in this environment

The cable-scanner app (`cable-scanner-app`, image `cable-scanner-cable-scanner`, vite in `/app/node_modules`) is the **third case** above. Its `/home/ubuntu/cable-scanner-fnt/docker-compose.yml` uses `env_file: .env` + `environment:` interpolation, so the FNT env is resolved at **container start**: `docker inspect cable-scanner-app` shows `MOUNTS=[]` and there is no `/app/.env` baked into the image. Therefore:

- Patching `/home/ubuntu/cable-scanner-fnt/.env` (the source of truth — also read by a host vite instance in the same worktree) + `docker restart cable-scanner-app` is all that's needed to push a new `FNT_SESSION_ID` into the running app. **No rebuild required** for a session change.
- In read-only/incident mode, hand the engineer the exact command: `docker restart cable-scanner-app`.