# Agent Lightning Flow Explained

## Using `wealth_onboarding_apo.py` as Example

---

## 🎯 The Big Picture

```
┌─────────────────────────────────────────────────────────────────┐
│                     YOUR CODE (3 things needed)                  │
├─────────────────────────────────────────────────────────────────┤
│  1. @rollout Agent Function    → Returns reward (0.0 - 1.0)     │
│  2. Dataset (train + val)      → Tasks with expected answers     │
│  3. Seed Prompt Template       → Starting prompt to optimize     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AGENT LIGHTNING (APO)                         │
│                                                                  │
│   Trainer.fit() runs a loop:                                    │
│   1. Call agent with prompt v0 → Get rewards                    │
│   2. Analyze failures → Generate "gradient" (critique)          │
│   3. Generate prompt v1, v2... → Test variations                │
│   4. Keep best performers → Beam search                         │
│   5. Repeat for N rounds                                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    Best Prompt Found! 🏆
```

---

## 📁 File Structure

```
wealth_onboarding_apo.py
├── WealthOnboardingTask (TypedDict)  ← Task schema
├── prompt_template_baseline()         ← Seed prompt
├── @rollout wealth_onboarding_agent() ← THE AGENT (returns reward)
└── main()                             ← Training loop
```

---

## 1️⃣ The Agent Function (Most Important!)

```python
@rollout  # ← Magic decorator that enables optimization
def wealth_onboarding_agent(task: WealthOnboardingTask, prompt_template: PromptTemplate) -> float:
    """
    SIGNATURE MUST BE: (task, prompt_template) -> float
    """
    
    # Step 1: Use the prompt template (APO optimizes this!)
    user_message = prompt_template.format(task_input=task["task_input"])
    
    # Step 2: Call your LLM (any provider works)
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": user_message}]
    )
    
    # Step 3: Calculate reward (0.0 to 1.0)
    reward = calculate_reward(response, task["expected_decision"])
    
    return reward  # ← APO uses this to judge prompt quality
```

### Why `@rollout`?
- **Traces** all LLM calls automatically
- **Connects** your agent to the APO algorithm
- **Enables** automatic prompt optimization

---

## 2️⃣ The Reward Function (How APO Learns)

```python
# From wealth_onboarding_apo.py - the reward calculation:

reward = 0.0

# FORMAT (40% of score)
valid_decisions = ["approve", "conditional_approve", "escalate", "decline"]
if decision in valid_decisions:
    reward += 0.2   # Correct format
if reason and len(reason) > 5:
    reward += 0.2   # Has explanation

# ACCURACY (40% of score)  
if decision == expected_decision:
    reward += 0.4   # Exact match!
elif close_match:
    reward += 0.2   # Partial credit

# RISK APPROPRIATENESS (20% of score)
if risk_handled_correctly:
    reward += 0.2

return reward  # Final: 0.0 to 1.0
```

### Reward Design Tips:
| Component | Weight | Why |
|-----------|--------|-----|
| Format compliance | 20-40% | Agent must follow instructions |
| Exact accuracy | 40-60% | Main goal |
| Partial credit | 10-20% | Helps gradient learning |
| Edge cases | 10-20% | Handles nuance |

---

## 3️⃣ The Training Loop

```python
def main():
    # 1. Load datasets
    dataset_train, dataset_val = load_train_val_dataset()
    
    # 2. Configure APO algorithm
    algo = APO[WealthOnboardingTask](
        openai_client,
        val_batch_size=10,      # Tasks per evaluation
        gradient_batch_size=4,  # Failures to analyze
        beam_width=2,           # Keep top 2 prompts
        branch_factor=2,        # Generate 2 variations per prompt
        beam_rounds=2,          # Run 2 optimization rounds
    )
    
    # 3. Create trainer with seed prompt
    trainer = Trainer(
        algorithm=algo,
        n_runners=8,  # Parallel workers
        initial_resources={
            "prompt_template": prompt_template_baseline()  # Starting prompt
        },
    )
    
    # 4. RUN OPTIMIZATION!
    trainer.fit(
        agent=wealth_onboarding_agent,
        train_dataset=dataset_train,
        val_dataset=dataset_val
    )
```

---

## 4️⃣ What Happens During `trainer.fit()`

```
Round 0: Evaluate seed prompt (v0)
         ├── Run agent on 10 tasks → Average reward: 0.65
         ├── Analyze 4 failures → "Agent misses high-value thresholds"
         └── Generate v1, v2 variations

Round 1: Evaluate all candidates
         ├── v0: 0.65
         ├── v1: 0.72 ✓ Better!
         ├── v2: 0.58 ✗ Worse
         └── Keep v0, v1 (beam_width=2)
         
         Generate v3, v4 from v1
         
Round 2: Final evaluation
         ├── v0: 0.65
         ├── v1: 0.72
         ├── v3: 0.88 ✓ BEST!
         └── v4: 0.71
         
         Winner: v3 with 88% accuracy!
```

---

## 🔧 How to Apply to ANY Agent

### Template

```python
from agentlightning import Trainer
from agentlightning.algorithm.apo import APO
from agentlightning.litagent import rollout
from agentlightning.types import PromptTemplate, Dataset

# 1. Define your task type
class MyTask(TypedDict):
    id: str
    input: str
    expected_output: str

# 2. Define seed prompt
def my_seed_prompt() -> PromptTemplate:
    return PromptTemplate(
        template="Do something with {input}",
        engine="f-string",
    )

# 3. Create your agent with @rollout
@rollout
def my_agent(task: MyTask, prompt_template: PromptTemplate) -> float:
    # Use the template
    prompt = prompt_template.format(input=task["input"])
    
    # Call your LLM/agent logic
    result = call_llm(prompt)
    
    # Calculate reward
    if result == task["expected_output"]:
        return 1.0
    else:
        return 0.0

# 4. Train!
def main():
    algo = APO[MyTask](openai_client)
    trainer = Trainer(
        algorithm=algo,
        initial_resources={"prompt_template": my_seed_prompt()}
    )
    trainer.fit(agent=my_agent, train_dataset=train, val_dataset=val)
```

---

## 🎯 Key Integration Points

| Your Code | Agent Lightning |
|-----------|-----------------|
| `@rollout def agent(task, prompt_template) -> float` | Required signature |
| `prompt_template.format(**vars)` | Use the optimizable template |
| `return reward` | 0.0-1.0, higher = better |
| `Dataset[MyTask]` | List of tasks with expected answers |

---

## ⚡ Works With Any Framework

### LangChain
```python
@rollout
def langchain_agent(task, prompt_template) -> float:
    prompt = prompt_template.format(**task)
    chain = LLMChain(llm=ChatOpenAI(), prompt=prompt)
    result = chain.run(task["input"])
    return calculate_reward(result, task["expected"])
```

### AutoGen
```python
@rollout
def autogen_agent(task, prompt_template) -> float:
    assistant = AssistantAgent(system_message=prompt_template.format(**task))
    # ... run conversation
    return reward
```

### Plain OpenAI
```python
@rollout
def openai_agent(task, prompt_template) -> float:
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt_template.format(**task)}]
    )
    return reward
```

---

## 📊 Reward Function Examples

### Binary (Simple)
```python
return 1.0 if correct else 0.0
```

### Graded (Better for APO)
```python
reward = 0.0
if format_valid: reward += 0.3
if partially_correct: reward += 0.3
if exactly_correct: reward += 0.4
return reward
```

### LLM-as-Judge
```python
judge_response = client.chat.completions.create(
    messages=[{"role": "user", "content": f"Score this: {result}. Expected: {expected}"}]
)
return float(judge_response) / 10.0  # Normalize to 0-1
```

---

## Summary

1. **Wrap your agent** with `@rollout`
2. **Accept `prompt_template`** and use it via `.format()`
3. **Return a reward** between 0.0 and 1.0
4. **Provide datasets** with expected answers
5. **Call `trainer.fit()`** and let APO find the best prompt!

That's it! Agent Lightning handles the rest. ⚡
