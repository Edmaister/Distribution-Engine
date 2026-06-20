# Amplifi Frontend

This is the first read-only Amplifi frontend slice. It is isolated from the
backend application and uses the existing API at `http://127.0.0.1:8000` by
default.

## Run Locally

```cmd
cd /d "C:\Projects\Referral Engine\frontend"
npm run dev
```

Open:

```text
http://127.0.0.1:5173/admin
```

## Build Check

```cmd
cd /d "C:\Projects\Referral Engine\frontend"
npm run build
```

## Current Screens

- Admin overview
- Health and readiness
- Admin audit
- Enterprise event inbox
- Sponsor billing spine
- Sponsor portal read-only billing view
- Distributor portal read-only offers and wallet view

## Session Settings

The top bar stores these values in browser local storage:

- API base URL, defaulting to `http://127.0.0.1:8000`
- Admin API key, defaulting to `test-admin-key`

The sponsor and distributor portal screens also store the tenant, sponsor, and
distributor codes in browser local storage after they are entered.

## Safety Notes

This slice is read-only. It does not issue invoices, replay events, route offers,
move wallet balances, or update distributor/sponsor records.
