# Night Train v3 — Architecture & Runbook

> **Version:** v3 (2026-03-02)  
> **Repo:** AAndriant/betadvisor-app  
> **Agents:** Antigravity (Claude Sonnet 4.6) + Jules (Gemini 3 Pro)

---

## Overview

Night Train v3 is a fully automated CI/CD pipeline that enables two AI agents to collaborate asynchronously on the BetAdvisor codebase:

- **Antigravity** (Claude Sonnet 4.6): Sprint planning, issue creation, code review, architecture decisions
- **Jules** (Gemini 3 Pro): Autonomous coding on queued issues during 6-7h shifts

The system is designed for a **non-technical product owner** to monitor with minimal intervention.

---

## Agent Alternation Model

```
┌─────────────────────────────────────────────────────────────────┐
│                    DAILY DEVELOPMENT CYCLE                       │
│                                                                  │
│  EVENING (18:00-20:00 CET) — Antigravity                        │
│  ├── Review previous sprint results on main                     │
│  ├── Code review (read commits, check issues)                   │
│  ├── Plan next sprint (5-6 issues, well-scoped)                 │
│  ├── Create issues with labels: agent:jules, ready              │
│  ├── Update ops/night-queue.json                                │
│  └── gh workflow run "Start Night Train" --ref main             │
│                                                                  │
│  NIGHT (20:00-03:00 CET) — Jules (autonomous)                   │
│  ├── Picks first open issue from queue                          │
│  ├── Branches from main: jules/<id>-<slug>                      │
│  ├── Codes solution + opens PR targeting main                   │
│  ├── CI runs automatically                                      │
│  ├── On CI success: autoqueue squash-merges + chains next       │
│  └── Repeats until queue exhausted                              │
│                                                                  │
│  MORNING (08:00-10:00 CET) — Antigravity                        │
│  ├── git log --since="12 hours ago" origin/main                 │
│  ├── Review closed issues + merged code                         │
│  ├── Identify failures (needs:human labels)                     │
│  └── Decide: fix issues or plan next sprint                     │
│                                                                  │
│  DAY — Product owner monitors, Antigravity available on-demand  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Architecture (v3 — simplified)

```
Kick (workflow_dispatch)
  → Read ops/night-queue.json
  → Find first OPEN issue
  → Invoke Jules API (startingBranch: main)
  → Jules creates branch jules/<id>-slug from main
  → Jules opens PR targeting main with "Closes #N"

CI (push on jules/* branch)
  → Backend CI (Django check + migrations)
  → Mobile CI (npm ci + tsc)

Autoqueue (workflow_run: CI success on jules/* branch)
  → Extract issue_id from branch name
  → Validate issue is in ops/night-queue.json
  → PROOF-OF-WORK: verify PR has meaningful code changes
  → Squash merge PR → main
  → Close issue + label "done"
  → Find NEXT open issue in queue
  → Invoke Jules API for NEXT
  → If no NEXT: log "Sprint Complete"
```

### Key Differences from v2

| Aspect | v2 | v3 |
|--------|----|----|
| Starting branch | `jules/train` | `main` |
| PR target | `jules/train` | `main` |
| Merge method | `repos.merge` (merge commit) | `pulls.merge` (squash) |
| Post-sprint merge | Manual: jules/train → main PR | Not needed (already on main) |
| Train branch reset | Required after each sprint | Not needed |
| Workflows | 9 files | 4 files |
| State file | Git commit to main after each issue | Eliminated |

---

## Files

| File | Purpose |
|------|---------|
| `.github/workflows/start-night-train.yml` | Kick workflow (manual dispatch) |
| `.github/workflows/jules-autoqueue.yml` | Autoqueue (CI → validate → merge → chain) |
| `.github/workflows/guard-jules-pr-in-queue.yml` | Block ghost PRs from old/invalid sessions |
| `.github/workflows/ci.yml` | CI pipeline (backend + mobile) |
| `ops/night-queue.json` | Sprint queue (strict JSON array of issue numbers) |
| `AGENTS.md` | Coding rules for Jules |

---

## Queue Format

`ops/night-queue.json` must be a **strict JSON array** of GitHub issue numbers:

```json
[86, 87, 88, 89, 90]
```

Rules:
- No trailing commas
- No objects — flat array only
- Numbers must correspond to existing open issues
- **Order = execution order** (first = processed first)

---

## Autoqueue Operation Order

1. **Find PR** for the jules/* branch that triggered CI
2. **Extract** issue_id from branch name `jules/<id>-slug`
3. **Validate** issue is in `ops/night-queue.json` (HALT if not)
4. **Proof-of-work** — verify PR has meaningful code files (HALT if no-op)
5. **Squash merge** PR → `main`
6. **Close** issue + label `done` + remove `agent:jules`
7. **Scan** queue forward for next OPEN issue (skip closed, skip existing PRs)
8. **Dispatch** next issue to Jules API
9. **Complete** — if no more issues, log `Sprint Complete`

---

## HALT/STOP Rules

| Condition | Action |
|-----------|--------|
| Cannot extract issue_id | STOP + `needs:human` on PR |
| Issue not in queue | STOP + `needs:human` on issue |
| PR has no meaningful changes | HALT + `needs:human` on issue |
| Merge conflict/failure | STOP + `needs:human` on PR |
| JULES_API_KEY missing | STOP + `needs:human` on next issue |
| Jules API error | STOP + `needs:human` on next issue |

**Key rule**: The autoqueue NEVER falls back to `queue[0]`. It only scans forward from the current position.

---

## Issue Sizing Guide

For a 6-7 hour Jules shift:

| Size | Jules time | Files | Per sprint |
|------|-----------|-------|------------|
| **S** (Small) | 20-35 min | 1-2 | 8-12 |
| **M** (Medium) | 35-60 min | 3-5 | 5-8 |
| **L** (Large) | 60-90 min | 5-8 | 3-5 |

**Recommended**: 5-6 Medium issues per sprint (sweet spot for quality + throughput).

### Issue Writing Rules

Each issue MUST have:
- [ ] Clear, single goal (1 feature or fix)
- [ ] Scope section with checkboxes
- [ ] Acceptance Criteria with provable assertions
- [ ] Files/Hints listing expected file changes
- [ ] Labels: `agent:jules`, `ready`
- [ ] No more than 5-8 files to touch
- [ ] No ambiguous scope ("improve", "refactor" without specifics)

---

## Manual Operations

### Start the Night Train
```bash
gh workflow run "Start Night Train" --ref main
```

### Check current queue
```bash
cat ops/night-queue.json
```

### Monitor a running sprint
```bash
# Recent workflow runs
gh run list --limit 5

# Check for halted issues
gh issue list --label "needs:human" --state open

# See recent commits on main
git log --since="6 hours ago" --oneline origin/main
```

### Re-kick after a stall
```bash
# Just re-run the kick — it finds the next OPEN issue automatically
gh workflow run "Start Night Train" --ref main
```

### Archive a sprint queue
```bash
cp ops/night-queue.json ops/queues/$(date +%Y-%m-%d)-sprint-N.json
echo '[]' > ops/night-queue.json
git add ops/ && git commit -m "ops: archive sprint N queue"
git push
```

---

## Troubleshooting

| Symptom | Check | Fix |
|---------|-------|-----|
| Train stalled (no activity) | `gh run list --limit 5` | Re-kick: `gh workflow run "Start Night Train" --ref main` |
| `needs:human` on issue | Read the issue comment | Fix manually or re-scope the issue |
| Merge conflict | PR comments | Resolve conflict manually, re-push |
| Queue exhausted | `cat ops/night-queue.json` | Create new issues + update queue |
| No-op PR (proof-of-work fail) | Issue comment with NOOP details | Re-scope issue to be more specific |
| Jules didn't code anything | Check session ID on [jules.google.com](https://jules.google.com) | Re-kick the train |

---

## Telemetry

Key log patterns to search for in workflow runs:

```
[kick] TELEMETRY: kick_issue=86 kick_index=0 queue_length=5
[autoqueue] TELEMETRY: completed=86 idx=0 next=87 next_idx=1 queue_len=5
[autoqueue] TELEMETRY: completed=87 idx=1 next=NONE queue_complete=true queue_len=5
[autoqueue] ❌ NOOP: PR #123 has no meaningful code changes.
```

---

## Security

- `JULES_API_KEY` is stored as a GitHub Actions secret
- No secrets are ever logged (masked by Actions)
- The `guard-jules-pr-in-queue.yml` prevents unauthorized PRs
- AGENTS.md prohibits Jules from modifying workflows or committing secrets
