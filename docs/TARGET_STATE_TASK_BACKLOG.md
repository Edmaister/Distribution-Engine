# Target-State Task Backlog

This backlog captures the next platform hardening slices needed to move from
feature-rich prototype to reviewable target-state platform.

## P0 - Migration System

- Done: Renumber duplicate migration prefixes.
- Done: Fail checks when duplicate numbered migrations are introduced.
- Done: Fail checks for pasted psql prompt text and unguarded table/index creation.
- Done: Keep readiness hints aligned to actual migration names.
- Done: Apply only ordered, numbered migrations during database startup.
- Done: Prove the numbered migration chain can be replayed by the startup runner.
- Done: Archive legacy unnumbered SQL and extensionless migration artifacts out
  of the active replay folder.
- Done: Fail checks when unnumbered SQL or extensionless numbered artifacts are
  introduced into the active migration folder.

## P1 - Cold CI

- Done: Run backend tests, frontend build, migration checks, and clean database
  replay from a clean checkout.
- Done: Wire producer-to-distributor-to-referral attribution checks into CI through
  service-level journey contract tests.
- Make the headline artifact a green cold-start run.

## P1 - Outcome-To-Money Reconciliation

- Done: Add an admin outcome-to-money map that traces completed customer
  outcomes through reward, commission, distributor wallet movement, producer
  invoice evidence, settlement, and open settlement exceptions.
- Done: Surface the map in the Admin Command Centre as a backend-backed
  operating view for the Producer - Supply, Distributor - Demand, and Amplifi
  Admin financial rail.
- Done: Add an integration test that seeds a completed customer outcome and
  proves the money map reads reward, commission, wallet, invoice, and settled
  settlement evidence across real database tables.
- Done: Add broken-trail coverage for missing distributor wallet movement,
  missing producer invoice evidence, failed settlement, and open settlement
  exception states.
- Done: Add an admin repair-focus breakdown so the Command Centre shows which
  owner rail should act next: Producer - Supply, Distributor - Demand, or
  Amplifi Admin.
- Done: Add an outcome-scoped repair action that resolves open settlement
  exceptions linked to a completed customer outcome, with an Admin Command
  Centre action for eligible attention outcomes.
- Done: Add an outcome-scoped repair action that creates draft producer invoice
  evidence for completed outcomes with rewards that have not yet been invoiced.
- Done: Add an outcome-scoped repair action that creates settled settlement
  evidence after reward and producer invoice evidence exist, with traceable
  fulfilment audit repair metadata.
- Done: Add outcome-scoped repair actions that regenerate missing reward,
  commission, and distributor wallet evidence from configured policies, route
  attribution, commission rules, and wallet ledgers.
- Done: Promote outcome-money visibility from Admin-only operations into
  role-scoped Producer - Supply and Distributor - Demand review experiences.
  Producer users see reward and invoice readiness; Distributor users see
  commission and wallet readiness; Admin retains repair execution and
  settlement exception ownership.

## P1 - Partner Seam

- Done: Add OAuth2 client-credentials onboarding for external partners.
- Done: Add outbound webhooks for key lifecycle events.
- Done: Provide a thin partner SDK or documented client examples.
- [done] Added partner client credentials, bearer token issue, webhook subscription,
  durable delivery queue, and a thin Python client example.
- Done: Add the outbound delivery worker and admin action that signs and sends
  pending webhook rows, tracks sent/pending/failed state, and schedules retries.
- Done: Surface partner seam delivery health in the Admin Command Centre with
  client, pending, sent, and failed delivery visibility.
- Done: Protect newly stored webhook signing secrets with an application secret
  key and expose a 24-hour delivery health summary API for Admin UX.
- Done: Add a partner-scoped integration overview API and Partner Integration
  workspace so external partners can review tenant/client identity, webhook
  subscriptions, delivery evidence, and guardrails without seeing secret
  material.
- Done: Add partner-scoped webhook self-service for bearer-token clients:
  create endpoint subscriptions and rotate webhook signing secrets from both the
  API and Partner Integration workspace.
- Done: Add partner-visible delivery exception handling so failed/cancelled
  webhook rows appear in the Partner Integration workspace and bearer-token
  clients can requeue their own failed/cancelled deliveries after fixing their
  endpoint.
- Done: Add partner dead-letter CSV export for failed/cancelled webhook delivery
  evidence, available through the API and Partner Integration workspace.
- Done: Add repeated delivery-failure alerts grouped by webhook endpoint and
  event type, with backend-owned severity and recommended actions surfaced in
  the Partner Integration workspace.
- Done: Add webhook signing-secret readiness reporting so partners can see
  protection mode, protected subscription count, legacy plaintext count, and
  rotation guidance without exposing secret values.
- Done: Add controlled legacy webhook signing-secret rotation so partner
  sessions can resolve readiness warnings and receive the new one-time secrets
  without exposing stored secret material.
- Done: Add partner-facing client credential onboarding so tenant-scoped partner
  sessions can create OAuth-style clients for their own tenant while
  bearer-token client sessions remain scoped to their own credentials and
  webhooks.
- Done: Add admin-triggered in-app notification evidence for repeated partner
  webhook delivery alerts, surfaced in both Admin Command Centre and Partner
  Integration views.
- Done: Add managed secret-provider readiness for partner webhook signing
  secrets, including application-key vs managed-KMS configuration reporting in
  backend readiness and Partner Integration UX.
- Done: Add an opt-in AWS KMS backend for partner webhook signing-secret
  protection and surface the active KMS backend in Partner Integration readiness
  so operators can distinguish local-envelope managed mode from physical KMS.
- Done: Add an optional physical webhook notification provider for repeated
  partner delivery-failure alerts, with signed JSON delivery and persisted
  provider status evidence.
- Done: Add a backend-owned Partner Seam production readiness contract, exposed
  to Partner Integration and Admin, that separates code-complete partner
  capability from live deployment configuration.

## P1 - Second Vertical

- Done: Configure an Insurance vertical journey and progress model without
  relying on banking event names for completion.
- Done: Add backend readiness reporting so Admin can see whether the platform is
  single-vertical or has a second configured vertical.
- Done: Surface vertical readiness in the Admin Command Centre as an operating
  signal, not a technical payload.
- Done: Enable the public Progress API to accept configured journey identifiers
  and non-banking event types, including Insurance events such as
  FIRST_PREMIUM_PAID.
- Done: Route enterprise events through configured journey definitions so
  Insurance events can enter the event fabric and queue with journey context.
- Done: Carry journey and milestone context into reward fulfilment requests so
  Insurance rewards do not lose vertical context downstream.
- Done: Apply configured leaderboard scoring rules to referral milestones and
  seed Insurance leaderboard recognition rules.
- Done: Surface reward policy and leaderboard scoring readiness in the Admin
  vertical readiness view.
- Done: Add vertical identifier validation for Banking and Insurance so progress
  and enterprise-event intake reject/ignore events without the required customer
  or policy evidence.
- Done: Surface identifier-validation readiness in the Admin vertical readiness
  view.
- Done: Add journey-aware fulfilment policy resolution and seed an Insurance
  provider route so Insurance rewards can use a vertical-specific fulfilment
  path before falling back to generic reward-type routing.
- Done: Surface fulfilment provider readiness in the Admin vertical readiness
  view.
- Done: Add an Insurance regulatory overlay with disclosure, template, and
  recommendation-compliance coverage for quote, policy issue, first-premium,
  and completed-policy prompts.
- Done: Surface regulatory overlay readiness in the Admin vertical readiness
  view.
- Done: Add a canonical seeded Insurance customer outcome that traces through
  opportunity, route attribution, referral completion, reward, commission,
  distributor wallet movement, producer invoice evidence, fulfilment provider,
  and settled outcome-money evidence.
- Done: Expose an Admin Insurance journey proof that shows whether Producer,
  Distributor, Consumer, and Admin surfaces have enough evidence to trust the
  second-vertical journey.
- Done: Add a focused Admin proof API at
  `GET /admin/verticals/proof/insurance` so clients can read the canonical
  Insurance journey proof without unpacking the full readiness payload.
- Done: Extend the same proof from Admin visibility into dedicated Producer,
  Distributor, and Consumer page sections, with role-specific summaries for
  supply evidence, demand earnings, and customer reward visibility.
- Done: Replace the shared Admin proof read on role pages with dedicated
  producer-, distributor-, and consumer-scoped proof APIs. The pages now read
  proof through the same role surface that owns the user journey.
- Done: Add local role-scoped API key identities for Producer, Distributor, and
  Consumer proof access, including producer/distributor claim checks that reject
  mismatched request contexts.
- Done: Add a frontend session role selector for Admin, Producer, Distributor,
  Consumer, and Partner local keys so role-scoped journeys can be tested without
  memorising raw API keys.
- Done: Centralise tenant, producer, and distributor permission checks and add a
  frontend session-role banner that warns when the selected local role does not
  fit the current workspace.
- Done: Add a backend session introspection API and wire the frontend banner to
  backend-confirmed roles, with local key inference kept only as a fallback.
- Done: Use backend-confirmed producer and distributor session claims to load and
  lock the matching workspace identity, while Partner/Admin sessions remain
  flexible for cross-record operations.
- Done: Extend backend session introspection with workspace access metadata and
  use it in the frontend banner so allowed/blocked workspace guidance comes
  from the API contract.
- Done: Surface backend workspace access in the sidebar so navigation shows
  session-aligned and check-needed workspaces without hiding the target-state
  operating model.
- Done: Move Admin vertical readiness onto a vertical catalog service so
  Banking and Insurance readiness are evaluated from configured vertical
  metadata, with missing components surfaced to the frontend.
- Done: Add a third clean-room Retail Loyalty vertical with catalog metadata,
  journey, progress milestones, identifier validation, fulfilment route,
  leaderboard/reward metadata, and regulatory overlay so agnosticism is proven
  beyond a Banking + Insurance two-case implementation.
- Done: Centralise frontend session contract loading in the app shell so the
  sidebar, banner, and role workspaces share one backend-confirmed session
  source.
- Done: Expand backend workspace access metadata to every visible sidebar route,
  including Admin operating views, and make the session banner render from that
  API contract instead of a frontend route map.
- Done: Add backend-owned workspace summaries and guidance text so frontend
  access banners explain what the session can do or which session to switch to
  without hardcoded UX copy.
- Done: Add scoped Admin identities to backend session introspection and
  workspace access guidance, with frontend presets for Finance Admin,
  Distribution Admin, and System Admin testing.
- Done: Add a backend-recommended starting workspace per session role and
  surface it in the sidebar and session banner as a gentle start-here cue.
- Done: Add a direct session banner route to the backend-recommended starting
  workspace so mismatched users get a clear next action instead of only a
  warning.
- Done: Add JWT-capable backend identity claims that feed the same central
  permission checks as local role-scoped API keys, and add frontend bearer-token
  session entry so Admin, Producer, Distributor, Consumer, and Partner journeys
  can be exercised through backend-confirmed JWT roles.
- Done: Add configurable JWT claim mapping so a production IdP can use its own
  role, tenant, subject, producer, distributor, client, and scope claim names
  without changing permission code.
- Done: Runtime vertical proof is catalog-driven and clean-room validated across
  Banking, Insurance, and Retail Loyalty. Historical banking wording that
  remains in legacy docs/tests is fixture-specific, not architectural defaulting.

## P1 - Identity And Deployment Readiness

- External dependency: Bind JWT validation to the selected production IdP/OAuth
  issuer and token lifecycle. Local keys remain a development fallback only.
- External dependency: Roll out live AWS KMS credentials/key lifecycle and
  configure the selected production partner alert notification endpoint.

## P2 - Channels And Intelligence

- Done: Add a backend channel catalog/readiness API for WhatsApp, SMS, and
  USSD adapters on the existing distributor/opportunity channel concept.
- Done: Surface backend-backed channel readiness in Producer - Supply so the
  workspace no longer shows a placeholder for partner/channel catalogue state.
- Done: Add a provider-backed outbound dispatch adapter and admin dispatch API
  for WhatsApp, SMS, and USSD, including signed provider calls and unconfigured
  provider guardrails.
- Done: Add signed inbound receive/session webhooks for WhatsApp replies, SMS
  replies, and USSD session menus, normalised into a single channel payload
  contract.
- Done: Add explainable recommendation intelligence for Producer - Supply,
  Distributor - Demand, and Admin channel choices, using event fit, audience
  preference, opportunity/distributor channel constraints, and live provider
  readiness without sending messages or bypassing consent checks.
- Done: Add shared frontend money and rate formatting helpers and apply them to
  Producer - Supply funding/billing, Distributor - Demand earnings/wallets, and
  Admin settlement operating views so users see locale-aware currency and
  percentage values instead of raw decimal payloads.
