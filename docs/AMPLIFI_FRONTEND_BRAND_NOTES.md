# Amplifi Frontend Brand Notes

These notes translate the supplied brand kit and CX/UX brief into frontend
implementation rules.

Source files:

- `C:\Users\Carla\Downloads\amplifi-brand-kit_2.html`
- `C:\Users\Carla\Downloads\amplifi-cx-ux-brief_6.html`

## Brand Position

Amplifi is a distribution infrastructure platform. Product UI copy should feel
precise, trustworthy, and operationally useful.

Use:

- distribution infrastructure
- distribution operating system
- control centre
- marketplace
- opportunity
- eligibility
- reputation
- earnings
- auditability

Avoid:

- referral platform
- loyalty platform
- amazing
- revolutionary
- hype language
- exclamation points

## Core Tokens

| Token | Hex | Use |
| --- | --- | --- |
| Ink | `#0A0E1A` | Primary text, dark sidebar, authority surfaces |
| Ink Mid | `#1C2238` | Dark panels |
| Ink Soft | `#3A4260` | Secondary text |
| Rule | `#E4E7F0` | Borders and dividers |
| White | `#FFFFFF` | Panels and cards |
| Off White | `#F5F6FA` | App background |
| Signal Blue | `#1A56F0` | Primary actions, links, active state |
| Signal Mid | `#3D70F5` | Dark-surface active accents |
| Signal Light | `#EBF0FF` | Active nav backgrounds and subtle highlights |
| Gold | `#C8A96E` | Premium/executive-only accent |
| Success | `#0D9E72` | Positive status only |
| Warning | `#D97706` | Warning status only |
| Danger | `#DC2626` | Error/destructive status only |

Signal Blue is the brand accent. Status colours are allowed but should not
become decorative theme colours.

## Typography

- Primary typeface: `Sora`
- Technical/data typeface: `DM Mono`
- Body default: `15px`, line-height around `1.6-1.7`
- Product labels: `11px`, uppercase, modest letter spacing
- IDs, codes, timestamps, and metric labels: `DM Mono`

## Product UI Shape

Admin/Enterprise Control Centre:

- Dark Ink sidebar.
- Signal Blue active nav state.
- Compact topbar.
- Dense KPI cards.
- Tables for campaigns, distributors, events, audit, invoices, and settlement.
- Clear action buttons, but no decorative hero treatment.

Distributor Portal:

- Lighter product surface.
- Opportunity cards with reward, eligibility, sponsor/product, and match tags.
- Earnings and pending balances visible.
- Marketplace filters by industry, reward type, and eligibility.

Sponsor Portal:

- Calm finance-style surface.
- Dashboard, invoices, statements, receipts, wallet, contracts, forecast.
- Emphasise outstanding balance, status, due dates, and traceable IDs.

## UX Constraints

- Every screen should have one clear job.
- Every operational record should show status and next action.
- Every financial action should show amount, currency, entity ID, and confirmation.
- Compliance should be framed as eligibility/confidence, not friction.
- Matched opportunities should prioritise relevance over volume.
- Avoid hiding raw identifiers from admin and finance users.

