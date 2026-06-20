# DLaaS Definition Of Done Review Prompt

Use this prompt after one DLaaS task implementation cycle.

```text
Review the completed task against the DLaaS Definition of Done.

Read:
- AGENTS.md
- docs/product/DLAAS_TARGET_STATE.md
- docs/sa/CAPABILITY_GAP_MATRIX.md
- docs/roadmap/ENHANCEMENT_BACKLOG.md
- docs/roadmap/ORDERED_TASK_LIST.md
- docs/agent/DLAAS_AGENT_STOP_CONDITIONS.md
- all files changed by the task

Check:
1. Does the change advance the linked DLaaS platform capability?
2. Does it satisfy the selected task acceptance criteria?
3. Does it stay within one reviewable task?
4. Does it avoid invented fields, statuses, schemas, routes, APIs, and response shapes?
5. Does it preserve database schema unless the task explicitly required schema work?
6. Does it preserve business logic unless the task explicitly required logic work?
7. Are backend source-of-truth files correctly reflected?
8. Are schema assumptions verified or marked as unknown?
9. Are required states documented or implemented from source truth?
10. Are auth and permission impacts documented or tested?
11. Are idempotency and retry impacts documented or tested where relevant?
12. Are reward, funding, fulfilment, settlement, and audit impacts documented or tested where relevant?
13. Are tests or validation appropriate for the task type?
14. Were docs and task status updated?
15. Were follow-up tasks created for unresolved gaps?
16. Did the work avoid frontend/control-plane assumptions not backed by backend truth?
17. Did the work avoid live DB assumptions without validation?
18. Is any human approval still required?

Return:
- Pass / Fail
- Evidence
- Files changed
- Tests/validation reviewed
- Remaining gaps
- Follow-up tasks
- Whether the task can remain marked complete
- Required next action
```
