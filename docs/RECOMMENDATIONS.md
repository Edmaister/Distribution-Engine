# Recommendations Engine

This document explains how the **Next-Best-Action (NBA)** and **Next-Best-Offer (NBO)** system works.

---

## Purpose
The recommendation engine ensures users are **guided** toward the most impactful actions that benefit both them and the bank.  
It makes the referral program **engaging**, **data-driven**, and **personalized**.

---

## Inputs
- **Referrals**: codes issued, validated, UCNs captured.
- **Rewards**: applied or pending.
- **Missions**: progress and milestones.
- **Badges**: awarded achievements.
- **Enterprise Events**: Hogan IDS events (salary deposits, debit orders, insurance activations).
- **Policies**: reward amounts and eligibility rules (sticker defaults or campaign overrides).

---

## Outputs
The service generates structured recommendation cards such as:

- **SEND_INVITE**  
  *"Invite more friends to unlock your next mission badge."*  
  Triggered when missions/goals suggest more referrals are needed.

- **COMPLETE_MISSION**  
  *"You're 1 step away from finishing Invite 5 Friends mission."*  
  Triggered when mission progress is close to goal.

- **APPLY_REWARD**  
  *"Your referee switched a debit order – apply your R35 reward."*  
  Triggered when IDS evidence is present but no reward yet applied.

Each card contains:
- `action` (enum)
- `reason` (why recommended)
- `confidence` (0–1, simple heuristic or ML in future)
- `campaignCode` / `missionCode` / `referralTrackId` (context)

---

## API
- `GET /me/recommendations?referrer_hash=&sticker=&tenant=`  
  Returns 3–5 cards for display in the user dashboard.

---

## Business Value
- **Increases engagement** by nudging users.
- **Prevents leakage** by surfacing rewards pending application.
- **Encourages cross-product take-up** (banking + insurance).
