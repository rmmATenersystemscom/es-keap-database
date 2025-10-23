# Keap Functionality — User Story Map (Ener Systems MSP, Construction/Engineering)

> Scope: Full Keap coverage, tailored to Ener Systems’ workflows, clients, and handoffs across **Sales → CX → Service → Finance**. Optimized for Construction/Engineering accounts, CFO-facing communication, and MSP operations (NinjaRMM, ThreatLocker, ConnectWise Manage hooks).

---

## Roles (Ener Systems)
- **Owner/CEO (Rene)**: vision, KPI dashboards, approvals.
- **Sales (AM/AE)**: pipeline, proposals, pricing, renewals.
- **CX/Onboarding**: intake, asset discovery, kickoff coordination.
- **Service (NOC/Helpdesk/Project)**: tasks, notes, follow-through.
- **Security**: policy acceptance, MFA, Zero Trust enrollment.
- **Finance/AR**: quotes, invoices, payments, subscriptions.
- **Marketing**: segments, nurture, testimonials, local awards.
- **Integrator/Dev**: API, ETL backup, data quality guardrails.

---

## Epic A — ICP & Intake (Construction/Engineering)
**Goal:** Capture high-fit leads and context needed for scoping.

1. **Lead Capture with Vertical Context**
   - As Marketing, I can capture leads via LP/forms that tag **Vertical: Construction/Engineering** and **Source** (CFO lunch, Chamber, Referral).
   - Acceptance: Contact created; company linked; tags applied; UTM/source stored.
   - Data: `contacts`, `companies`, `contact_tags (Vertical: C/E, Source:*)`.

2. **Qualification (BANT + Environment Snapshot)**
   - As Sales, I can record budget/timeline and a quick environment snapshot (seat count, Fortinet present?, Microsoft 365 SKU).
   - Acceptance: Required custom fields validated; next step task created.
   - Data: contact/company custom fields + `tasks` for next step.

3. **Discovery → Assessment**
   - As CX, I can trigger a checklist: asset inventory, MFA status, backups, firewall model, patching posture.
   - Acceptance: Task template applied; due dates set; Slack/Teams notifications.
   - Data: `tasks`, `notes`, tags like **Assessment: In‑Progress/Complete**.

---

## Epic B — Pipelines & Deals
**Goal:** Consistent stages for Construction/Engineering deals with CFO clarity.

**Pipeline:** *C/E Services*  
Stages & prob: Lead(10) → Qualify(20) → Scope & Discovery(40) → Proposal(60) → Verbal(80) → Won(100)/Lost
- Fields: ARR, Seats, Sites, Firewall model, Veeam tier, EnerCare tier, CyberGuard tier.

**Stories**
1. **Create Opportunity from Qualified Lead**
   - As Sales, I can create an opp linked to contact/company, set ARR & tiers.
   - Acceptance: Stage = Qualify; owner set; forecast visible.
   - Data: `opportunities (contact_id, stage_id, pipeline_id, value, owner_id)`.

2. **Move to Proposal with Pricing Snapshot**
   - As Sales, I can attach a quote and freeze the pricing snapshot (ARR/MRR).
   - Acceptance: Stage change logged; quote attached; task to review with CFO.
   - Data: notes/files; order/quote if using Keap e‑comm.

3. **Closed‑Won → Kickoff**
   - As Sales, I trigger **Onboarding** automation: welcome email, portal invite, payment method request, and create a **Project Kickoff** task set for CX.
   - Data: tags: **Customer**, **Onboarding: Open**; `tasks` assigned to CX.

---

## Epic C — Onboarding & Handoffs
**Goal:** Flawless kickoff and ownership clarity.

1. **Welcome + Payment Portal**
   - As CX/Finance, I send the payment-portal login + “add payment method” guide (Ener Systems docs). Tag **Billing: PM Method Received** on completion.
   - Data: email template + tag.

2. **Tech Intake & Safety**
   - As Security, I apply policy tags to trigger MFA, Zero Trust training, and password manager enrollment.
   - Data: tags like **Security: MFA‑Enrolled**, **ZT: Training Completed**.

3. **Create Service Records**
   - As Service, I create tasks for: FortiGate baseline, Veeam backup job, RMM agent roll‑out, ThreatLocker enroll, documentation in CW Manage.
   - Data: `tasks`, `notes`; optional webhook to CW Manage/NinjaRMM TL.

**Definition of Done (Onboarding)**
- Payment method on file; MSA signed; MFA enrolled; backups verified; firewall policies applied; first monthly invoice generated; kickoff note stored; `Onboarding: Closed` tag applied.

---

## Epic D — Service & Security
**Goal:** Keep clients stable, compliant, and delighted.

1. **Ticket → Context Pull**
   - As Service, when a client calls, I can see device posture (RMM online?, last reboot?, ThreatLocker status) and contact context (role, site) from Keap tags/fields.
   - Data: prefetch via integration; store summary in `notes` when needed.

2. **Quarterly Business Review (QBR)**
   - As AM, I schedule QBR tasks, email the CFO agenda, and tag **QBR: Scheduled/Done**.
   - Data: `tasks`, `notes`, tags; opps created for upsell actions.

3. **Security Posture Changes**
   - As Security, if risk increases (policy exception, EDR alert), apply **Risk: Elevated** tag to trigger notifications and AM task.
   - Data: tag‑driven automations.

---

## Epic E — Finance & Renewals
**Goal:** Predictable ARR/MRR, clean collections.

1. **Subscriptions for Managed Services**
   - As Finance, I maintain subscriptions per client for EnerCare (LITE/Total) and CyberGuard (LITE/FULL) tiers; renewals 30/60 days reminder.
   - Data: `products`, `orders`, `payments`, subscriptions (if enabled).

2. **AR & Dunning**
   - As Finance, if invoice is overdue, tag **AR: Past Due** and trigger sequence (gentle reminder → escalation).
   - Data: tags; payment status reflected in `payments` total.

3. **Renewal/Upsell**
   - As Sales/AM, create opps for renewals, tier upgrades, license increases.
   - Data: opps linked to company; ARR delta captured in value field.

---

## Epic F — Marketing & Reputation
**Goal:** Keep a healthy funnel and leverage social proof.

1. **Local Awards & PR**
   - As Marketing, tag contacts who engaged with award campaigns (Best of St. Tammany, MSP Titans finalist) and send follow‑ups.
   - Data: tags: **Campaign: Award YYYY**, **Press: Sent**.

2. **Nurture Tracks**
   - As Marketing, vertical‑specific nurture (C/E risk, ransomware stats, case studies).
   - Data: tags mapped to journey membership; Easy Automations/Campaign Builder.

3. **Testimonial Requests**
   - As Marketing, trigger testimonial request post‑onboarding and after successful projects.
   - Data: tags: **Advocacy: Request Sent/Received**.

---

## Tag Taxonomy (starter)
**Categories**
- **Lifecycle:** Lead, MQL, SQL, Customer, Churn Risk
- **Vertical:** Construction/Engineering, CPA, Legal
- **Campaign:** Award YYYY, Webinar YYYY‑MM, eBook: <title>
- **Consent:** Email Opt‑In, SMS Opt‑In
- **Security:** MFA‑Enrolled, ZT‑Training Completed, Risk: Elevated
- **Billing:** PM Method Received, AR: Past Due
- **Onboarding:** Open, Closed
- **QBR:** Scheduled, Done

---

## Custom Fields (examples)
- Company: Site Count, Seat Count, Firewall Model, Backup Platform, M365 SKU
- Contact: Role (CFO/PM/Engineer), Consent SMS (Y/N), Mobile
- Opportunity: ARR, EnerCare Tier, CyberGuard Tier, Close Reason

---

## Validation Mapping (for ETL/backup)
- No orphans in `contact_tags`, `tasks`, `notes`, `opportunities`.
- Stage/pipeline consistency for opportunities.
- Subscription/orders/payments reconcile (±$0.01).
- Coverage sanity: distinct contacts with tags/opps/tasks meet expectations.
- Freshness: `updated_at` aligned with run timestamp; deltas behave.

---

## BDD Snippets
**Onboarding DoD**
```
Given a deal is marked Won
When onboarding is triggered
Then payment method is collected and MSA signed
And MFA enrollment is complete
And backup and firewall baselines are verified
And Onboarding: Closed tag is applied
```

**AR Dunning**
```
Given an invoice is 15 days overdue
When the AR: Past Due tag is applied
Then the client receives a courteous reminder
And a task is created for AM follow-up
```

**QBR Scheduling**
```
Given a customer with ARR > $X
When the quarter rolls over
Then create a QBR task and send the CFO agenda
```

---

## Definition of Done (Org)
- Data integrity validated post‑export; nightly deltas passing.
- Pipelines, tags, and custom fields align to this spec.
- Automations drive handoffs; tasks never orphaned; owners set.
- Dashboards show pipeline health, ARR/MRR, AR status, security posture.
