# DLaaS Task Runner Prompt

Use this prompt to ask Codex to run one DLaaS task cycle.

```text
Run the DLaaS task runner.

Read:
- AGENTS.md
- docs/product/DLAAS_TARGET_STATE.md
- docs/sa/
- docs/sa/CAPABILITY_GAP_MATRIX.md
- docs/roadmap/ENHANCEMENT_BACKLOG.md
- docs/roadmap/ORDERED_TASK_LIST.md
- docs/agent/DLAAS_AGENT_RUNBOOK.md
- docs/agent/DLAAS_AGENT_STOP_CONDITIONS.md

Select the highest-priority unblocked task by dependency order.

Before implementing, output:
- Selected TASK ID
- Task title
- Linked enhancement
- Linked platform capability
- Why this task is next
- Dependencies
- Readiness result: Ready / Not Ready
- Missing information
- Recommended next action

Use this readiness checklist:
1. Does the task reference a TASK ID?
2. Does the TASK ID reference an enhancement?
3. Does the enhancement reference a DLaaS platform capability?
4. Does the capability exist in the gap matrix?
5. Are dependencies satisfied?
6. Is the backend source of truth known?
7. Is the schema known or explicitly not relevant?
8. Are required states known?
9. Are required APIs known or explicitly not relevant?
10. Are auth/permissions known or explicitly not relevant?
11. Are UX loading, empty, error, success, and permission states known where relevant?
12. Are tests defined?
13. Is DB/state validation required?
14. Are risks documented?

If the task is Not Ready, stop and recommend the next action.

If the task is Ready:
- Implement only that one task.
- Do not implement product features outside the task.
- Do not invent backend fields, statuses, APIs, routes, or schema.
- Do not build frontend work unless backend truth is known and the selected task requires it.
- Do not change reward, funding, fulfilment, settlement, audit, auth, security, or production-data behavior without tests and approval where needed.
- Run relevant tests or docs validation.
- Run a Definition of Done review.
- Update task status and docs.
- Create follow-up tasks for gaps.
- Stop safely.

Return:
- Selected TASK ID
- What changed
- Files changed
- Tests/validation performed
- Definition of Done result
- Follow-up tasks
- Remaining gaps
- Recommended next action
```
