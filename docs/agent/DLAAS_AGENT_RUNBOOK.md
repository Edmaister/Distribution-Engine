# DLaaS Agent Runbook

This runbook explains how Codex should execute DLaaS roadmap work without manual prompting for every step.

It is an operating guide only. It must not be used to implement product features outside the ordered task list.

## Source Of Truth

Codex must read these sources before major work:

1. `AGENTS.md`
2. `docs/product/DLAAS_TARGET_STATE.md`
3. `docs/sa/`
4. `docs/sa/CAPABILITY_GAP_MATRIX.md`
5. `docs/roadmap/ENHANCEMENT_BACKLOG.md`
6. `docs/roadmap/ORDERED_TASK_LIST.md`
7. `docs/agent/DLAAS_AGENT_STOP_CONDITIONS.md`

The workflow is:

```text
Target State -> SA Docs -> Gap Matrix -> Enhancement Backlog -> Ordered Task List -> Implementation -> Tests -> Docs Update
```

## Runner Cycle

1. Read the source documents.
2. Confirm completed and blocked tasks in `docs/roadmap/ORDERED_TASK_LIST.md`.
3. Select the highest-priority unblocked task by dependency order.
4. Run the readiness checklist from `.agents/skills/dlaas-task-runner/SKILL.md`.
5. If readiness fails, stop and report the missing information.
6. If readiness passes, restate the task scope before editing.
7. Implement only that one task.
8. Run relevant tests or docs validation.
9. Review against `docs/agent/DLAAS_AGENT_STOP_CONDITIONS.md`.
10. Run the Definition of Done review prompt.
11. Update task status and related docs.
12. Create follow-up tasks for any gaps.
13. Stop and summarize.

## Branch And Review Guidance

- Use one branch or PR per task where possible.
- Keep each task small enough to review independently.
- Do not auto-merge.
- Do not bundle unrelated fixes.
- If a task expands beyond one reviewable unit, stop and split it into follow-up tasks.

## Readiness Requirements

A task is ready only when:

- It has a `TASK-XXX` ID.
- It links to an enhancement in `docs/roadmap/ENHANCEMENT_BACKLOG.md`.
- The enhancement links to a capability in `docs/sa/CAPABILITY_GAP_MATRIX.md`.
- Dependencies are satisfied.
- Backend source of truth is known.
- Schema, states, APIs, auth, permissions, tests, risks, and DB/state validation needs are known or explicitly not relevant.

## Implementation Boundaries

- Do not invent backend fields, statuses, schemas, APIs, routes, or response bodies.
- Treat database schema and service-layer code as current source of truth.
- Do not start frontend/control-plane work unless backend truth is known.
- Do not change reward, funding, fulfilment, settlement, audit, auth, security, or production-data behavior without tests and required approval.
- Do not assume live DB state without validation.

## Completion Report

Every runner cycle should end with:

- Selected task ID and title.
- Readiness result.
- Files changed.
- Tests or validation performed.
- Definition of Done result.
- Task status update.
- Follow-up tasks.
- Remaining gaps.
- Recommended next action.
