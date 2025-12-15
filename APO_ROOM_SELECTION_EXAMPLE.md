# APO Walkthrough for the Room‑Selection Prompt  
*A clear, realistic example of how APO optimizes your scheduling prompt.*

---

## ✅ Overview

This walkthrough shows how Automatic Prompt Optimization (APO) would optimize **your room‑selection scheduling prompt** using:

- Rollouts on training tasks  
- Textual gradients  
- Beam search  
- Validation scoring  
- Versioned prompt candidates (v0 → v1 → v2 → … → vN)

This version matches how APO behaves in the real UI:  
**you only ever see v0, v1, v2, v3…**  
Internal branches are hidden.

---

## ✅ 1. Seed Prompt (v0)

APO begins with your original long scheduling prompt as **v0**.

It will try to improve accuracy, clarity, and consistency while reducing errors.

---

## ✅ 2. Round 0 — Training Rollouts

APO samples several training tasks, such as:

- Date: 2025‑03‑12  
- Time: 14:00  
- Duration: 60 min  
- Attendees: 12  
- Needs: projector, whiteboard  
- Accessible required: yes  

Example rooms:

- **Orion**: capacity 10, projector, whiteboard, accessible  
- **Nova**: capacity 14, projector, whiteboard, accessible  
- **Atlas**: capacity 20, projector only  

### Example model mistake using v0
The model incorrectly selects **Atlas** because it has “more space,” even though it lacks required equipment.

Reward: **0**

APO collects several such rollout traces.

---

## ✅ 3. Round 0 — Textual Gradients

APO sends the rollout results to a gradient model, which produces a critique like:

> “The prompt is long and mixes rules with examples.  
> It does not emphasize rejecting rooms missing required equipment.  
> Tie‑breaking rules are buried in the text.  
>  
> Improvements:  
> - Move rules to the top  
> - Emphasize equipment matching  
> - Clarify tie‑breaking order  
> - Shorten or remove examples”

This critique is the **textual gradient**.

---

## ✅ 4. Round 0 — Generate Candidate Prompts (v1–v4)

APO applies the critique to produce several improved prompts:

- **v1** — More structured rules  
- **v2** — More concise, fewer examples  
- **v3** — Clearer tie‑breaking  
- **v4** — More verbose reasoning instructions  

These are the children of v0.

---

## ✅ 5. Round 0 — Validation Scoring

APO evaluates v0–v4 on a validation set.

Example results:

| Version | Accuracy |
|---------|----------|
| v0 (seed) | 64% |
| v1 | 71% |
| v2 | 69% |
| v3 | 73% |
| v4 | 66% |

Beam width = 2 → keep **v3** and **v1**.

---

## ✅ 6. Round 1 — New Rollouts for v3 and v1

APO runs new training tasks.

### Example new mistake
Needs: “video conferencing”  
Room has: “video‑conference”

Model incorrectly rejects it due to hyphen mismatch.

Gradient critique:

> “Clarify that equipment matching is case‑insensitive and hyphen/underscore variations should be treated as equivalent.”

Another critique for v1:

> “Prompt does not clearly define overlapping booking logic.”

---

## ✅ 7. Round 1 — Generate New Candidates (v5–v8)

APO generates new versions from v3 and v1:

- **v5** — Adds equipment normalization  
- **v6** — Clarifies booking overlap rule  
- **v7** — Compresses formatting rules  
- **v8** — Reorders rules for clarity and conciseness  

These become the next set of candidates.

---

## ✅ 8. Round 1 — Validation Scoring

Example results:

| Version | Accuracy |
|---------|----------|
| v5 | 76% |
| v6 | 74% |
| v7 | 70% |
| v8 | 78% |

Beam keeps: **v8** and **v5**.

---

## ✅ 9. Final Selection

APO compares all versions across all rounds and selects the best overall performer.

### ✅ Winner: **v8**

- Highest validation accuracy  
- Clear rule ordering  
- Strong equipment matching logic  
- Correct booking overlap handling  
- Concise formatting  
- Token cost around ~195 tokens  

---

## ✅ 10. What This Shows

This walkthrough mirrors how APO actually works:

- You only see **v0 → v1 → v2 → … → v8**  
- Internal branches are hidden  
- Each version is the *best surviving candidate* from each round  
- APO uses real rollout mistakes to generate textual gradients  
- Beam search ensures only the strongest prompts survive  
- The final prompt is the best across all rounds  

This is exactly the process behind the dashboard you saw.

---

