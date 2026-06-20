# DLaaS PR Review Prompt

Use this prompt to review a branch, PR, or local diff for DLaaS alignment.

```text
Review this change as a DLaaS PR reviewer.

Prioritize bugs, regressions, security risks, money/reward/settlement risks, audit gaps, tenant isolation gaps, and missing tests.

Read:
- AGENTS.md
- docs/product/DLAAS_TARGET_STATE.md
- docs/sa/CAPABILITY_GAP_MATRIX.md
- docs/roadmap/ENHANCEMENT_BACKLOG.md
- docs/roadmap/ORDERED_TASK_LIST.md
- changed files
- relevant services, routers, migrations, and tests

Check:
1. Does every implementation change reference a TASK ID?
2. Does the TASK ID reference an enhancement and capability?
3. Is the change scoped to one reviewable task?
4. Does it preserve tenant/account isolation?
5. Does it avoid invented fields, statuses, schemas, APIs, routes, or responses?
6. Are schema changes backed by migrations and tests?
7. Are backend state transitions canonical and auditable?
8. Are money, reward, funding, fulfilment, settlement, and audit flows tested?
9. Are idempotency, retry, and duplicate-event protections preserved?
10. Are auth and permission boundaries enforced?
11. Are public/internal APIs validated with clear errors?
12. Are frontend/control-plane assumptions backed by backend source truth?
13. Are live DB assumptions verified or explicitly marked unavailable?
14. Are docs and task status updated?
15. Are follow-up tasks added for discovered gaps?
16. Is there any high-risk change requiring human approval?

Return findings first, ordered by severity:
- P0: blocks merge; correctness/security/money/data-isolation issue
- P1: should fix before merge
- P2: follow-up acceptable if documented
- P3: minor

Then return:
- Open questions
- Test gaps
- DLaaS alignment summary
- Merge recommendation: Do not merge / Needs changes / Reviewable after approval

Do not auto-merge.
```
