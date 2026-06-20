# DLaaS Task Runner Skill

Use this skill when asked to run, continue, select, review, or automate DLaaS roadmap tasks.

The purpose of this skill is to let Codex execute one reviewable DLaaS task cycle at a time without manual prompting. It is an operating framework only. It must not be used to skip readiness checks, invent backend truth, or batch unrelated implementation work.

## Required Source Documents

Read these before selecting or implementing any task:

1. `AGENTS.md`
2. `docs/product/DLAAS_TARGET_STATE.md`
3. `docs/sa/`
4. `docs/sa/CAPABILITY_GAP_MATRIX.md`
5. `docs/roadmap/ENHANCEMENT_BACKLOG.md`
6. `docs/roadmap/ORDERED_TASK_LIST.md`
7. `docs/agent/DLAAS_AGENT_STOP_CONDITIONS.md`

If any required document is missing, stop and report the missing source.

## Execution Loop

Follow this chain:

```text
Target State -> SA Docs -> Gap Matrix -> Enhancement Backlog -> Ordered Task List -> Readiness -> One Task -> Tests -> Definition of Done Review -> Docs Update -> Stop
```

## Task Selection Rules

- Select the highest-priority unblocked task from `docs/roadmap/ORDERED_TASK_LIST.md`.
- Prefer dependency order over ease.
- Do not skip follow-up tasks that block schema, state, money, audit, or API confidence.
- Do not select a frontend/control-plane task unless backend source of truth, states, APIs, and permissions are known.
- Do not select reward, funding, fulfilment, settlement, audit, auth, security, or production-data tasks unless required tests and validation are defined.
- Implement only one task per cycle.
- Use one branch or PR per task where possible.

## Readiness Checklist

Before implementation, answer:

1. Does the task reference a `TASK-XXX` ID?
2. Does the task reference an enhancement?
3. Does the enhancement reference a DLaaS platform capability?
4. Does the capability exist in `docs/sa/CAPABILITY_GAP_MATRIX.md`?
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

If readiness fails, stop and recommend the next action. Do not implement.

## Implementation Rules

- Do not invent backend fields, statuses, schemas, API responses, or routes.
- Treat database schema and service-layer code as source of truth.
- Separate confirmed facts from assumptions.
- Do not modify product behavior beyond the selected task.
- Do not make high-risk changes without human approval.
- Do not auto-merge.
- Update task status and relevant docs before stopping.
- Create follow-up tasks for gaps discovered during the cycle.

## Test And Review Rules

- Run the tests named in the task when feasible.
- For docs-only tasks, perform readback validation instead of product tests.
- Money, reward, funding, fulfilment, settlement, auth, security, and audit tasks require tests plus DB/state validation where relevant.
- Run a Definition of Done review before marking a task complete.

## Stop Conditions

Stop when:

- The selected task is complete, documented, tested or validated, and reviewed.
- Readiness fails.
- Dependencies are missing.
- Tests fail and cannot be fixed safely within the selected task.
- Source of truth, schema, state, auth, or API behavior is uncertain.
- Live DB validation is required but unavailable.
- The change touches money, settlement, funding, security, auth, or production data and approval is missing.
- Scope expands beyond one reviewable unit.

When stopping, report the selected task, result, files changed, validation performed, remaining gaps, follow-up tasks, and recommended next action.
