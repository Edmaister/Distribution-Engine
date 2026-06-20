# Frontend UI Integration

This document describes how backend APIs map to **user** and **admin** frontends.

---

## User Portal

### Pages
1. **Dashboard**
   - Shows progress, missions, badges, and recommendations.
   - API: `GET /me/progress`, `GET /me/recommendations`

2. **Invite**
   - Generate referral codes (optionally tied to a campaign).
   - API: `POST /referrals/codes`

3. **Rewards & Activity**
   - Timeline of earned rewards and pending items.
   - API: (future `/me/rewards` read model)

4. **Leaderboard**
   - Rankings by points or referrals.
   - API: reads aggregated view (optional).

### Components
- **RecommendationCard** — renders NBA suggestions (invite, complete mission, apply reward).

---

## Admin Console

### Pages
1. **Campaigns**
   - List campaigns and their policies.
   - APIs:
     - `POST /campaigns`
     - `PUT /campaigns/{code}/policy`
     - `POST /campaigns/{code}/codes`

2. **Insights**
   - Campaign conversion KPIs (30-day).
   - API: `GET /admin/recommendations/campaigns/{code}?prefer_cache=true`

3. **Reward Ops**
   - Apply dangling rewards.
   - API: `POST /rewards/apply`

---

## UX Principles
- **Role-based routes** (`user`, `ops`, `admin`).
- **React Query** for caching and retries.
- **Tailwind UI** for consistent style.
- **Mermaid diagrams** (docs) align with flows.

---

## Value
- **Users**: clear view of progress and opportunities.
- **Admins**: control campaigns and see ROI instantly.
- **Developers**: clean API ↔ UI mapping.
