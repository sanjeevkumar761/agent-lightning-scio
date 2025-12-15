# Agent Lightning Integration Checklist

## ✅ Step-by-Step Checklist for Any New Agent

---

### 1. PREPARE YOUR AGENT

- [ ] **Install Agent Lightning**
  ```bash
  pip install agentlightning
  ```

- [ ] **Add the `@rollout` decorator** to your agent function
  ```python
  from agentlightning.litagent import rollout
  
  @rollout
  def my_agent(task, prompt_template) -> float:
  ```

- [ ] **Change function signature** to accept `(task, prompt_template)`
  - `task` = your task data (dict or TypedDict)
  - `prompt_template` = the prompt APO will optimize

- [ ] **Use `prompt_template.format()`** instead of hardcoded prompts
  ```python
  # Before:
  prompt = "You are a helpful assistant..."
  
  # After:
  prompt = prompt_template.format(**task)
  ```

- [ ] **Return a reward** (float 0.0 to 1.0)
  ```python
  return reward
  ```

---

### 2. CREATE YOUR DATASET

- [ ] **Define task schema** (what each task looks like)
  ```python
  class MyTask(TypedDict):
      id: str
      input: str           # What agent receives
      expected_output: str # What we expect (for grading)
  ```

- [ ] **Create tasks with expected answers** (minimum 20 recommended)
  ```python
  tasks = [
      {"id": "1", "input": "...", "expected_output": "..."},
      {"id": "2", "input": "...", "expected_output": "..."},
      # ... more tasks
  ]
  ```

- [ ] **Split into train/validation** (50/50 or 70/30)
  ```python
  split = len(tasks) // 2
  train_data = tasks[:split]
  val_data = tasks[split:]
  ```

---

### 3. DESIGN YOUR REWARD FUNCTION

- [ ] **Define what "good" means** for your agent
  
- [ ] **Create graded rewards** (better than binary)
  ```python
  reward = 0.0
  if format_correct: reward += 0.2
  if partially_correct: reward += 0.3
  if exactly_correct: reward += 0.5
  return reward
  ```

- [ ] **Consider these components:**
  | Component | Weight | Example |
  |-----------|--------|---------|
  | Format compliance | 20% | Correct JSON, follows template |
  | Partial credit | 20-30% | Close answer, right reasoning |
  | Exact match | 40-50% | Perfect answer |
  | Edge cases | 10% | Handles special scenarios |

---

### 4. CREATE SEED PROMPT

- [ ] **Write your starting prompt template**
  ```python
  from agentlightning.types import PromptTemplate
  
  def seed_prompt() -> PromptTemplate:
      return PromptTemplate(
          template="""Your instructions here...
          
          Input: {input}
          """,
          engine="f-string",
      )
  ```

- [ ] **Use placeholders** matching your task fields: `{input}`, `{context}`, etc.

---

### 5. CONFIGURE APO TRAINING

- [ ] **Create the training script**
  ```python
  from agentlightning import Trainer
  from agentlightning.algorithm.apo import APO
  from agentlightning.adapter import TraceToMessages
  from openai import AsyncOpenAI
  
  def main():
      # OpenAI client (or Azure)
      client = AsyncOpenAI(api_key="...")
      
      # Configure APO
      algo = APO[MyTask](
          client,
          val_batch_size=10,     # Tasks per evaluation
          beam_width=2,          # Keep top N prompts
          branch_factor=2,       # Generate N variations
          beam_rounds=2,         # Optimization rounds
      )
      
      # Create trainer
      trainer = Trainer(
          algorithm=algo,
          n_runners=8,
          initial_resources={"prompt_template": seed_prompt()},
          adapter=TraceToMessages(),
      )
      
      # Run!
      trainer.fit(
          agent=my_agent,
          train_dataset=train_data,
          val_dataset=val_data,
      )
  ```

---

### 6. RUN & MONITOR

- [ ] **Set environment variables**
  ```bash
  export AZURE_OPENAI_ENDPOINT="..."
  export AZURE_OPENAI_API_KEY="..."
  ```

- [ ] **Run training**
  ```bash
  python my_agent_apo.py
  ```

- [ ] **Monitor with Sparky dashboard** (optional)
  ```bash
  # Backend
  uvicorn main:app --reload
  # Frontend
  npm run dev
  ```

---

## 📁 Final File Structure

```
my_project/
├── my_agent.py              # @rollout agent function
├── my_agent_apo.py          # Training script
├── my_tasks.json            # Dataset with expected answers
└── .env                     # API keys
```

---

## 🎯 Quick Reference Template

```python
# my_agent.py
from agentlightning.litagent import rollout
from agentlightning.types import PromptTemplate

@rollout
def my_agent(task: dict, prompt_template: PromptTemplate) -> float:
    # 1. Use the template
    prompt = prompt_template.format(**task)
    
    # 2. Call your LLM
    response = call_llm(prompt)
    
    # 3. Calculate reward
    if response == task["expected"]:
        return 1.0
    return 0.0
```

```python
# my_agent_apo.py
from agentlightning import Trainer
from agentlightning.algorithm.apo import APO
from my_agent import my_agent

trainer = Trainer(
    algorithm=APO(client),
    initial_resources={"prompt_template": seed_prompt()}
)
trainer.fit(agent=my_agent, train_dataset=train, val_dataset=val)
```

---

## ⚡ TL;DR

| Step | Action |
|------|--------|
| 1 | Add `@rollout` decorator |
| 2 | Accept `(task, prompt_template)` |
| 3 | Use `prompt_template.format()` |
| 4 | Return reward (0.0-1.0) |
| 5 | Create dataset with expected answers |
| 6 | Run `trainer.fit()` |
