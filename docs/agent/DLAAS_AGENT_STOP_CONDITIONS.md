# DLaaS Agent Stop Conditions

Codex must stop safely when any condition below is met.

## Normal Stop

Stop when the selected task is complete, documented, tested or validated, reviewed against Definition of Done, and task status is updated.

## Readiness Stop

Stop before implementation when:

- The task lacks a `TASK-XXX` ID.
- The task does not reference an enhancement.
- The enhancement does not reference a DLaaS capability.
- The capability is not in `docs/sa/CAPABILITY_GAP_MATRIX.md`.
- Dependencies are missing.
- Backend source of truth is unknown.
- Schema, states, APIs, auth, permissions, risks, or tests are unknown and relevant.
- DB/state validation is required but unavailable.

## Scope Stop

Stop when:

- The work expands beyond one reviewable unit.
- The task requires product work outside the selected task.
- The task would require unrelated refactors.
- A frontend/control-plane task depends on backend states, APIs, auth, or schema that are not known.

## Safety Stop

Stop when:

- The change touches money, rewards, funding, fulfilment, settlement, audit, auth, security, or production data without required tests.
- A high-risk change needs human approval.
- Production or live DB access is required and not approved.
- Live DB assumptions are needed but cannot be validated.
- Source-of-truth code and schema disagree and the task does not explicitly resolve that uncertainty.
- Tests fail and cannot be fixed safely inside the selected task.

## Data Stop

Stop when:

- Customer data, secrets, tokens, provider payloads, or production identifiers may be exposed.
- The available DB role is not read-only for verification tasks.
- A route believed to be read-only writes state.
- A retry, replay, repair, settlement, fulfilment, approval, reversal, or payout action could affect non-test data.

## Merge Stop

Stop when:

- A change has not had Definition of Done review.
- Required tests or validation were not run and no reason is documented.
- Task status and docs were not updated.
- Follow-up tasks for known gaps were not created.
- Human approval is required.

Never auto-merge DLaaS task work.
