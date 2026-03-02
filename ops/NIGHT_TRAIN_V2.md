# Night Train v2 — Runbook

> **Version:** SRE-hardened v2 (2026-03-02)  
> **Repo:** AAndriant/betadvisor-app

---

## Architecture

```
Kick (workflow_dispatch)
  → Read ops/night-queue.json
  → Find first OPEN issue
  → Invoke Jules API
  → Jules creates branch jules/<id>-slug + PR with "Closes #N"

CI (push on jules/* branch)
  → Backend CI + Mobile CI

Autoqueue (workflow_run: CI success)
  → Guard: branch must be jules/* (not jules/train)
  → Extract issue_id from branch (BEFORE merge)
  → Validate issue is in ops/night-queue.json
  → Merge PR → jules/train
  → Close issue + label ready
  → Write ops/night-train-state.json
  → Scan queue for NEXT open issue (skip CLOSED + skip existing PR)
  → Invoke Jules API for NEXT
  → If no NEXT: comment "Queue Complete" on last issue
```

---

## Files

| File | Purpose |
|------|---------|
| `.github/workflows/start-night-train.yml` | Kick workflow (manual dispatch) |
| `.github/workflows/jules-autoqueue-train.yml` | Autoqueue (CI → merge → chain) |
| `ops/night-queue.json` | Queue definition (strict JSON array of issue numbers) |
| `ops/night-train-state.json` | State file (last completed issue, auto-updated) |

---

## Queue Format

`ops/night-queue.json` must be a **strict JSON array** of GitHub issue numbers:

```json
[32, 34, 35, 36, 37, 38, 39, 40, 41, 42, 33]
```

- No trailing commas
- No objects — must be a flat array
- Numbers must correspond to existing issues

---

## Operation Order (Autoqueue)

This is the **correct, SRE-hardened** order:

1. **Extract** issue_id from branch `jules/<id>-slug` (BEFORE merge)
2. **Validate** issue is in `ops/night-queue.json` (HARD STOP if not found)
3. **Merge** PR → `jules/train`
4. **Close** issue (only if merge succeeded) + label `ready` + remove `agent:jules`
5. **Write** state file `ops/night-train-state.json`
6. **Scan** queue forward for NEXT open issue
7. **Guard**: skip CLOSED issues + skip issues with existing `jules/*` PR
8. **Invoke** Jules API for NEXT issue
9. **Complete**: if no NEXT, log `queue_complete` and comment on last issue

> ⚠️ **NEVER** extract issue_id AFTER merge. Always extract first, validate, then merge.

---

## STOP Rules

The train will STOP and apply `needs:human` label in these cases:

| Condition | Action |
|-----------|--------|
| Cannot extract issue_id from branch or PR body | STOP + `needs:human` on PR |
| Issue not found in queue | STOP + `needs:human` on issue + comment |
| Merge conflict | STOP + `needs:human` on PR + comment |
| JULES_API_KEY missing | STOP + `needs:human` on next issue |
| Jules API error (non-2xx) | STOP + `needs:human` on next issue |

**Critical**: The train NEVER falls back to `queue[0]`. It only scans forward from the current index.

---

## Idempotence

If the autoqueue reruns (e.g., CI rerun), it will:

1. Find the same PR for the branch
2. Attempt merge (may already be merged → skip gracefully)
3. Check for existing `jules/*` PR for the next issue → skip if found
4. This prevents double-kicking Jules on the same issue

---

## Telemetry

Look for these canonical log lines:

```
[NTv2] TELEMETRY: current_issue=32 current_index=0 next_issue=34 next_index=1 queue_length=11
[NTv2] TELEMETRY: kick_issue=32 kick_index=0 queue_length=11
[NTv2] 🏁 queue_complete last_completed_issue=33
```

Structured fields:
- `current_issue` / `current_index` — issue just completed
- `next_issue` / `next_index` — issue being dispatched next
- `queue_length` — total items in queue
- `queue_complete` — true when no more open issues

---

## State File

`ops/night-train-state.json` is auto-updated after each successful merge:

```json
{
  "last_completed_issue": 32,
  "last_completed_at": "2026-03-02T09:45:00.000Z",
  "last_completed_pr": 123,
  "last_run_id": 22567662979,
  "queue_position": "1/11"
}
```

If the state file commit fails, it logs a warning but does NOT block the train.

---

## Manual Operations

### Start the train
```bash
gh workflow run "Start Night Train" --ref main
```

### Dispatch a specific issue
```bash
gh workflow run "Dispatch Issue to Jules" --field issue_number=34
```

### Check train state
```bash
cat ops/night-train-state.json
```

### Reset jules/train branch
```bash
gh workflow run "Reset jules/train"
```

### Stop the train
Close all remaining issues in the queue, or remove the `agent:jules` label from the current issue.

---

## Troubleshooting

| Symptom | Check | Fix |
|---------|-------|-----|
| Train stalled | Check last autoqueue run logs | Look for `HARD_STOP` or `needs:human` |
| Issue skipped | Check if issue was CLOSED | Reopen if needed |
| Duplicate Jules session | Check for existing `jules/*` PR | Close duplicate PR |
| State file stale | Check `ops/night-train-state.json` | Autoqueue will update on next merge |
| Queue exhausted | Look for `queue_complete` in logs | Update `ops/night-queue.json` for next sprint |
