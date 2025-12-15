# APO Simple Definitions

## 1. **Rollout** = One Run of Your Agent

```python
@rollout
def my_agent(task, prompt_template) -> float:
    # A "rollout" is one execution of this function
    # Input: a task + a prompt
    # Output: a reward score
```

**Think of it as:** One test question → Agent answers → Get a score

---

## 2. **Reward** = How Good Was the Answer? (0.0 to 1.0)

```python
# Simple reward:
if answer == expected_answer:
    return 1.0  # Perfect!
else:
    return 0.0  # Wrong

# Better reward (graded):
reward = 0.0
if format_correct: reward += 0.3
if partially_right: reward += 0.3
if exactly_right: reward += 0.4
return reward
```

**Think of it as:** A grade from 0% to 100%

---

## 3. **Training & Validation Datasets** = Test Questions with Answer Keys

```python
# Training data: APO learns from failures here
train_dataset = [
    {"id": "1", "input": "Book room for 5 people", "expected": "Room A"},
    {"id": "2", "input": "Book room with projector", "expected": "Room B"},
    # ... more tasks
]

# Validation data: APO measures final accuracy here (never trained on)
val_dataset = [
    {"id": "3", "input": "Book accessible room", "expected": "Room C"},
    {"id": "4", "input": "Book cheapest room", "expected": "Room D"},
    # ... more tasks
]
```

**Think of it as:**
- **Training** = Practice problems (APO analyzes mistakes)
- **Validation** = Final exam (measures if prompt actually improved)

---

## The Whole Flow in One Picture

```
Training Data          Your Agent              Reward
     │                     │                     │
     ▼                     ▼                     ▼
┌─────────┐         ┌─────────────┐        ┌─────────┐
│ Task 1  │────────▶│  @rollout   │───────▶│  0.8    │
│ Task 2  │────────▶│  my_agent() │───────▶│  0.6    │
│ Task 3  │────────▶│             │───────▶│  1.0    │
└─────────┘         └─────────────┘        └─────────┘
                           │
                    APO looks at low
                    rewards & improves
                    the prompt
                           │
                           ▼
                    New prompt version!
                           │
                           ▼
Validation Data     Test new prompt         Final Score
     │                     │                     │
     ▼                     ▼                     ▼
┌─────────┐         ┌─────────────┐        ┌─────────┐
│ Task A  │────────▶│  @rollout   │───────▶│  0.9    │
│ Task B  │────────▶│  my_agent() │───────▶│  1.0    │  → 95% avg!
│ Task C  │────────▶│             │───────▶│  0.95   │
└─────────┘         └─────────────┘        └─────────┘
```

---

## TL;DR

| Term | Simple Definition |
|------|-------------------|
| **Rollout** | One run of your agent on one task |
| **Reward** | Score from 0-1 saying how good the answer was |
| **Training Data** | Tasks APO uses to find problems & improve |
| **Validation Data** | Tasks APO uses to measure real improvement |
