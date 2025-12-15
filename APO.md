# APO, Textual Gradients, Beam Search, Rollouts, and Validation Sets  
*(Based on the Microsoft Agent Lightning APO documentation)*

---

## ✅ APO (Automatic Prompt Optimization)

APO is an algorithm that **automatically improves a prompt** through multiple rounds of optimization.  
It uses two core mechanisms:

- **Textual gradients** — LLM‑generated critiques that describe how to improve a prompt  
- **Beam search** — a structured search process that keeps only the best prompts each round

APO repeatedly:

1. Evaluates the current prompt on tasks (rollouts)  
2. Generates critiques (textual gradients)  
3. Applies edits to create new candidate prompts  
4. Scores all candidates on a validation set  
5. Keeps the top‑k prompts for the next round  

This continues until APO finds the best-performing prompt.

---

## ✅ Textual Gradients

A **textual gradient** is an LLM‑generated critique that explains how to improve the current prompt.

APO:

- Samples rollout results (model outputs + rewards)  
- Sends them to a gradient model  
- Asks the model to critique the prompt and suggest improvements  

These critiques act like gradients in machine learning — but instead of numeric vectors, they are **text instructions** describing how to edit the prompt.

Example critique:

> “The prompt is too vague. Add instructions to reason step-by-step.”

APO then uses another model to apply the critique and generate an improved prompt.

---

## ✅ Beam Search Process

Beam search is a **guided search strategy** that keeps only the best candidates at each step.

In APO:

- **Beam width** = number of top prompts to keep each round  
- **Branch factor** = number of new prompts generated from each parent  
- **Beam rounds** = number of optimization iterations  

Process:

1. Take the current top‑k prompts  
2. Generate several improved versions using textual gradients  
3. Evaluate all candidates on the validation set  
4. Keep only the top‑k prompts for the next round  

This balances exploration and exploitation.

---

## ✅ Rollouts

A **rollout** is a single execution of the agent on a task using a specific prompt.

A rollout includes:

- The messages exchanged  
- The spans (trace)  
- The final reward  
- Status information  

APO uses rollouts for:

### 1. Training rollouts  
Used to compute textual gradients (critiques).

### 2. Validation rollouts  
Used to score candidate prompts and decide which ones survive in the beam.

---

## ✅ Validation Set

The **validation set** is a set of tasks used to evaluate how good a prompt is.

APO uses it to:

- Score each candidate prompt  
- Select the top‑k prompts for the next beam round  
- Track the best prompt across all rounds  

It is separate from the training dataset used for textual gradients, preventing overfitting.

---

## ✅ Summary Table

| Concept | Meaning | Role in APO |
|--------|---------|-------------|
| **APO** | Automatic Prompt Optimization | Iteratively improves prompts using LLM feedback |
| **Textual Gradient** | LLM-generated critique | Guides how to edit the prompt |
| **Beam Search** | Keep top‑k candidates each round | Efficiently explores many prompt variations |
| **Rollout** | One execution of the agent on a task | Provides data for critiques and scoring |
| **Validation Set** | Tasks used for evaluation | Determines which prompts survive each round |

---

