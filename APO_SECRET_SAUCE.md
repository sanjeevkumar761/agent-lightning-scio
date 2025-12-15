# 🧪 The Secret Sauce Behind APO

## The Core Idea: "Textual Gradients"

APO treats **prompt optimization like gradient descent**, but instead of numeric gradients, it uses **LLM-generated critiques** to improve prompts.

```
Traditional ML:  loss → numeric gradient → update weights
APO:             failures → textual critique → update prompt
```

---

## The 2-Step Magic

### Step 1: Compute "Textual Gradient" (Critique)

An LLM analyzes **failed rollouts** and generates a critique:

```
Input to LLM:
├── Current prompt template
├── Sample runs that failed (with full traces)
└── Rewards for each run

Output:
"Critique:
• Agent misses high-value threshold (>$5M should escalate)
• No priority ordering for constraints
• Format is too loose, allows ambiguous responses"
```

### Step 2: Apply Edit

Another LLM takes the critique and **rewrites the prompt**:

```
Input to LLM:
├── Current prompt
└── Critique from Step 1

Output:
"[Improved prompt with the critique addressed]"
```

---

## The Algorithm: Beam Search

```
Round 0:
    v0 (seed) → score: 65%
    
Round 1:
    Critique v0's failures → "needs explicit thresholds"
    Generate v1, v2 from v0
    
    v0: 65%
    v1: 72% ✓ (keep)
    v2: 58%  (drop)
    
Round 2:
    Critique v1's failures → "add step-by-step reasoning"
    Generate v3, v4 from v1
    
    v1: 72%
    v3: 88% ✓ BEST!
    v4: 70%
```

**Beam search** keeps the top `beam_width` prompts and generates `branch_factor` variations from each.

---

## Why It Works

| Technique | What It Does |
|-----------|--------------|
| **Textual Gradients** | LLM identifies *what went wrong* by analyzing actual failures |
| **Trace Analysis** | Sees full conversation, tool calls, and rewards — not just final output |
| **Conservative Edits** | Changes ONE thing at a time, avoids breaking what works |
| **Beam Search** | Explores multiple paths, keeps winners, prunes losers |
| **Diversity Temperature** | Generates varied alternatives to explore solution space |

---

## The Prompts That Power It

**Gradient Prompt** (finds problems):
```
Analyze where the current prompt failed to elicit the right mechanism.
Write 3-5 short bullets titled 'Critique:' focusing on missing 
constraints, ordering, or formatting.
```

**Edit Prompt** (fixes problems):
```
Revise the prompt to address ONE critique point clearly and effectively.
Keep the new prompt close in tone, length, and structure to the original.
Return only the revised full prompt.
```

---

## The Parameters

```python
APO(
    gradient_model="gpt-5-mini",     # LLM for critiques
    apply_edit_model="gpt-4.1-mini", # LLM for edits
    beam_width=2,                     # Keep top 2 prompts
    branch_factor=2,                  # Generate 2 variants each
    beam_rounds=2,                    # Run 2 optimization rounds
    gradient_batch_size=4,            # Analyze 4 failures per critique
)
```

---

## TL;DR Secret Sauce

1. **Run agent** → Collect failures with full traces
2. **LLM critiques** → "Here's what went wrong"
3. **LLM edits** → "Here's a fix for ONE issue"
4. **Beam search** → Keep winners, generate more variations
5. **Repeat** → Converge on best prompt

**It's essentially using LLMs to debug and improve prompts automatically!** 🔧

---

## References

- [ProTeGi Paper](https://aclanthology.org/2023.emnlp-main.494.pdf) - Original textual gradients concept
- [TextGrad](https://github.com/zou-group/textgrad) - Related work on text-based optimization
- [Agent Lightning APO Docs](https://microsoft.github.io/agent-lightning/stable/algorithm-zoo/apo/)
