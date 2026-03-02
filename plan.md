1. **Understand the Goal**: The issue mentions that when PRs are merged via the `autoqueue-train.yml` GitHub Workflow, the linked issues aren't automatically closed because GitHub only triggers issue auto-close on standard merge via the UI or `gh pr merge`, but the script uses `github.rest.repos.merge`. We need to explicitly close the issue.
2. **Current Implementation Analysis**:
    - The workflow `.github/workflows/jules-autoqueue-train.yml` extracts the `issueNumber` from the PR body (step 3).
    - It merges the PR to `jules/train` (step 2) using `github.rest.repos.merge`.
    - It marks the current issue as `ready` and removes `agent:jules` label (step 4).
    - It does not actually close the issue.
3. **Proposed Fix**: After step 4 (marking the issue as `ready`), add a step to explicitly close the issue using `github.rest.issues.update` with `state: 'closed'`.
