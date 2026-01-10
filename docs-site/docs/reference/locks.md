# Locks & Leak Detection

Smolotchi uses file locks under `/run/smolotchi/locks` to coordinate long-running
operations. Each lock has a `.lock` file containing the owning PID plus a sidecar
`<name>.lock.json` metadata file with audit-friendly details.

**Lock metadata model**

- `.lock` contains the process ID (PID).
- `.lock.json` metadata includes:
  - `path`: lock path
  - `pid`: PID
  - `created_at`: ISO-8601 UTC timestamp
  - `hostname`: host that created the lock
  - `purpose`: optional string describing the lock

**Stale detection rules**

- `stale_pid`: PID is no longer alive.
- `stale_ttl`: lock age exceeds the TTL.
- `missing_meta`: no sidecar metadata (never deleted unless forced).

## CLI usage

List locks (default TTL 30 minutes):

```
smolotchi locks list --format table
```

Machine-readable output:

```
smolotchi locks list --format json
```

Dry-run prune (recommended first pass):

```
smolotchi locks prune --ttl-min 30 --dry-run --format table
```

Force prune missing metadata (explicit, risky):

```
smolotchi locks prune --ttl-min 30 --force --format table
```

### Recommended TTLs

For operator checks, start with `--ttl-min 30` and adjust based on the longest
expected workflow. Use dry-run to audit candidates before deleting.
