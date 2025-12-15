# APO Walkthrough: Wealth Client Onboarding  
*How APO optimized a compliance analyst prompt for financial onboarding*

---

## ✅ Overview

This walkthrough shows how Agent Lightning’s **Automatic Prompt Optimization (APO)** improved a prompt for a wealth management compliance analyst tasked with evaluating client onboarding documentation.  

The final optimized prompt (v4) includes:

- Structured decision rules  
- Strict formatting  
- Risk and documentation logic  
- Clear escalation and fallback pathways

We’ll follow the APO process:

- Seed prompt (v0)  
- Rollouts on training tasks  
- Textual gradients (LLM critiques)  
- Beam search  
- Validation scoring  
- Final winner: **v4**

---

## ✅ 1. Seed Prompt (v0)

Initial prompt:

> “You are a financial assistant helping onboard new wealth clients. Ask for their name, investment goals, risk tolerance, preferred communication method, and any existing accounts. Be polite and professional.”

This prompt was vague, lacked decision logic, and didn’t enforce formatting or risk evaluation.

---

## ✅ 2. Round 0 — Training Rollouts

APO runs the agent on onboarding tasks involving inheritance and business profit claims.

### Example Task
Client case:  
> “Inheritance claim. Documents: death certificate, probate, ID. Missing bank statements.”

Model output (v0):  
> “Thanks for submitting your documents. We’ll review and get back to you.”

Reward: **0.4** — polite but failed to apply decision logic or flag missing docs.

---

## ✅ 3. Round 0 — Textual Gradients

Gradient model critiques v0:

> “Prompt lacks decision rules and formatting constraints.  
> It does not guide the assistant to evaluate documentation or apply risk logic.  
>  
> Suggested improvements:  
> - Add structured decision options  
> - Enforce two-line output format  
> - Include documentation rules per claim type  
> - Add escalation and decline conditions”

---

## ✅ 4. Round 0 — Generate Candidate Prompts (v1–v3)

Using the critique, APO generates:

- **v1** — Adds decision options and basic formatting  
- **v2** — Introduces documentation rules for inheritance and business profit  
- **v3** — Adds escalation logic and red flag detection

---

## ✅ 5. Round 0 — Validation Scoring

| Version | Accuracy |
|---------|----------|
| v0 | 92.5% |
| v1 | 94.1% |
| v2 | 95.7% |
| v3 | 96.3% |

Beam keeps **v2** and **v3**.

---

## ✅ 6. Round 1 — New Rollouts for v2 and v3

New training tasks include:

- Business profit claims with unaudited financials  
- Inheritance claims missing probate  
- High-value cases with profit margin >50%

Gradient critiques suggest:

> “v2 needs escalation logic for high-risk cases.”  
> “v3 should clarify fallback phrasing and enforce exact output format.”

---

## ✅ 7. Round 1 — Generate New Candidates (v4–v6)

APO generates:

- **v4** — Combines decision rules, formatting, escalation logic, and documentation checks  
- **v5** — Adds tone reinforcement  
- **v6** — Compresses formatting instructions

---

## ✅ 8. Round 1 — Final Validation

| Version | Accuracy |
|---------|----------|
| v4 | 97.3% |
| v5 | 96.8% |
| v6 | 95.9% |

✅ **Winner: v4**

---

## ✅ 9. Final Optimized Prompt (v4)

```text
You are a wealth management compliance analyst evaluating client onboarding. Review the documentation for inheritance or business profit claims.

DECISION OPTIONS:
- approve: All required documentation present, low risk
- conditional_approve: Documentation mostly complete, minor items needed
- escalate: High-value or high-risk case requiring senior review
- decline: Insufficient documentation or unacceptable risk

Return exactly two lines only (no extra spaces or lines):
decision: [approve|conditional_approve|escalate|decline]
reason: [Brief explanation using these exact phrases; max 100 chars]

Apply rules in order:
1) Parse and normalize input; if missing or malformed → escalate: "Unclear case data; senior review required."
2) If claim type missing or ambiguous → conditional_approve: "Insufficient claim type info; request clarification."
3) Check required docs per claim type:
   - Business Profit: audited financials OR (unaudited + 3 yrs tax returns), business registration, bank statements (12 mo)
   - Inheritance: death certificate, probate, beneficiary ID, bank statements
4) If missing critical docs → decline: "Missing required docs for claim type."
5) If any immediate decline red flags (fraud indicators, forged docs) → decline: "Fraud indicators; decline case."
6) If any escalate flags (claim amount > USD 1,000,000 equivalent, years in operation <3, profit margin >50%) → escalate with appropriate reason.
7) If minor docs missing (e.g., bank statements) → conditional_approve: "Missing bank statements; minor docs needed."
8) Else approve: "All docs present; low-risk claim."

Case details: {task_input}
