# ⚡ Sparky Demo Script
## Agent Lightning + Automatic Prompt Optimization Dashboard
### 30-Minute Demo for Agent Developers

---

## 🎯 Demo Overview

**What is Sparky?**
- A visual dashboard extension for Microsoft Agent Lightning
- Shows prompt optimization results in real-time
- Makes APO (Automatic Prompt Optimization) accessible and understandable

**What is Agent Lightning?**
- Microsoft's framework for training/optimizing AI agents with **zero code changes**
- Works with ANY agent framework (LangChain, AutoGen, CrewAI, plain OpenAI)
- Supports RL, APO, Fine-tuning algorithms

---

## ⏱️ Demo Timeline

| Time | Section | Focus |
|------|---------|-------|
| 0-5 min | **The Problem** | Why prompt engineering is hard |
| 5-12 min | **Agent Lightning Intro** | Core concepts & architecture |
| 12-22 min | **Live Demo** | Run APO, show Sparky dashboard |
| 22-28 min | **Code Walkthrough** | How to integrate in your agents |
| 28-30 min | **Q&A** | Questions |

---

## 📋 Part 1: The Problem (5 min)

### Talking Points

> "How many of you have spent hours tweaking prompts trying to get better results?"

**The manual prompt engineering cycle:**
1. Write a prompt
2. Test it on a few examples
3. Find edge cases that fail
4. Tweak the prompt
5. Repeat forever...

**Problems:**
- Time consuming (hours/days)
- No systematic approach
- Hard to measure improvement
- Often makes one thing better, another worse

**What if we could automate this?**

---

## 📋 Part 2: Agent Lightning Intro (7 min)

### Show the README banner

```
Open: /root/agent-lightning/README.md
```

### Key Architecture Points

```
┌─────────────────────────────────────────────────────────────┐
│                    YOUR AGENT (unchanged)                    │
│         LangChain / AutoGen / CrewAI / Plain OpenAI         │
└────────────────────────┬────────────────────────────────────┘
                         │
                    @rollout decorator
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   AGENT LIGHTNING                            │
│  ┌──────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │ Tracer   │→ │ LightningStore│→ │ APO Algorithm      │    │
│  │ (spans)  │  │ (traces/tasks)│  │ (prompt optimizer) │    │
│  └──────────┘  └──────────────┘  └────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    SPARKY DASHBOARD                          │
│         Real-time visualization of optimization              │
└─────────────────────────────────────────────────────────────┘
```

### The Magic: Zero Code Change (Almost)

**Before Agent Lightning:**
```python
def my_agent(task):
    prompt = "You are a helpful assistant..."
    response = openai.chat(prompt + task)
    return response
```

**After Agent Lightning:**
```python
@rollout  # <-- Just add this!
def my_agent(task, prompt_template: PromptTemplate):
    prompt = prompt_template.format(**task)  # <-- Use template
    response = openai.chat(prompt + task)
    return calculate_reward(response)  # <-- Return reward
```

---

## 📋 Part 3: Live Demo (10 min)

### Step 1: Start the Backend

```bash
cd /root/agent-lightning/examples/apo/backend
uvicorn main:app --reload
```

### Step 2: Start Sparky Frontend

```bash
cd /root/agent-lightning/examples/apo/frontend
npm run dev
```

### Step 3: Open Sparky Dashboard

```
http://localhost:5173
```

### Demo Flow - Walk Through UI

1. **Header** → "Sparky" - our cute name for the dashboard
2. **Run APO Section** → Click "Start APO" to run optimization
   - Select "Room Selector" use case
   - Show it testing multiple prompt variations
3. **Optimization Results** → After completion, show:
   - **Accuracy Gain**: +4.8% improvement
   - **Token Cost**: Shows cost change (can go up or down)
   - **Best Score**: 97.3% accuracy
   - **Winner**: Version that performed best

4. **Charts** → 
   - Bar chart: Score by version (visual ranking)
   - Scatter plot: Cost vs Performance tradeoff

5. **Version Comparison Table** → 
   - Click a row to expand and see actual prompt text
   - Show evolution from v0 (seed) to winning version
   - Highlight: "Look how it went from verbose to structured!"

### Key Demo Narrative

> "Watch what happened: We started with a generic prompt (v0).
> Agent Lightning automatically generated variations:
> - v1: Added structure
> - v2: Reduced tokens
> - v3: Added chain-of-thought
> - v4: Combined best ideas
> 
> The algorithm tested each on real tasks, measured success rate,
> and found that v4 performs 4.8% better than our original!"

---

## 📋 Part 4: Code Walkthrough (6 min)

### Show the Agent Code

**File: `room_selector.py`**

```python
# The key decorator - this is what makes it optimizable
@rollout
def room_selector(task: RoomSelectionTask, prompt_template: PromptTemplate) -> float:
    """An agent to select a room based on the given requirements."""
    
    # 1. Format prompt using the template (APO will optimize this!)
    user_message = prompt_template.format(**task["task_input"])
    
    # 2. Your normal agent logic - UNCHANGED
    messages = [
        {"role": "system", "content": "You are a scheduling assistant."},
        {"role": "user", "content": user_message},
    ]
    
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=TOOL_DEFINITIONS,  # Agent can use tools
    )
    
    # 3. Return a reward (0.0 to 1.0)
    return room_selection_grader(client, response, task["expected_choice"])
```

### Show the Training Setup

**File: `room_selector_apo.py`**

```python
def main():
    # 1. Create APO algorithm
    algo = APO[RoomSelectionTask](
        openai_client,
        val_batch_size=10,      # Tasks per validation
        beam_width=2,           # Keep top 2 candidates
        branch_factor=2,        # Generate 2 variations per candidate
        beam_rounds=2,          # Run 2 rounds of optimization
    )
    
    # 2. Create trainer with initial prompt
    trainer = Trainer(
        algorithm=algo,
        n_runners=8,  # Parallel execution
        initial_resources={
            "prompt_template": prompt_template_baseline()
        },
    )
    
    # 3. Fit! (This runs the optimization)
    trainer.fit(
        agent=room_selector, 
        train_dataset=dataset_train, 
        val_dataset=dataset_val
    )
```

### Framework Agnostic Integration

**Show INTEGRATION_GUIDE.md**

```python
# LangGraph
@rollout
def langgraph_agent(task, prompt_template) -> float:
    agent = create_langgraph_agent(prompt_template.format(**task))
    result = agent.invoke(...)
    return reward

# AutoGen
@rollout
def autogen_agent(task, prompt_template) -> float:
    assistant = AssistantAgent("assistant", system_message=prompt)
    return reward

# CrewAI
@rollout  
def crewai_agent(task, prompt_template) -> float:
    agent = Agent(role="analyst", goal=prompt, ...)
    return reward
```

---

## 📋 Part 5: Quick Q&A Topics

### Expected Questions & Answers

**Q: What algorithms does Agent Lightning support?**
> APO (Automatic Prompt Optimization), Reinforcement Learning (GRPO, PPO), 
> Supervised Fine-tuning, and more. APO is great for quick wins without model training.

**Q: Does this work with my existing agent framework?**
> Yes! Works with LangChain, LangGraph, AutoGen, CrewAI, Semantic Kernel, 
> or even plain OpenAI SDK. Just add the `@rollout` decorator.

**Q: How do I define a reward function?**
> Return a float 0.0-1.0. Can be rule-based (exact match), 
> LLM-as-judge, or custom metrics. See `room_selection_grader()` for example.

**Q: How long does optimization take?**
> Depends on dataset size and beam settings. Our example with 20 tasks 
> and 2 beam rounds takes ~5 minutes. Production runs might be 30-60 min.

**Q: Can I use this for multi-agent systems?**
> Yes! You can selectively optimize individual agents in a multi-agent system.

---

## 🚀 Checklist Before Demo

- [ ] Backend running: `uvicorn main:app --reload`
- [ ] Frontend running: `npm run dev`  
- [ ] Browser open to `http://localhost:5173`
- [ ] Environment variables set (Azure OpenAI)
- [ ] Have mock data ready (in case API is slow)
- [ ] VS Code open with key files:
  - `room_selector.py` (agent code)
  - `room_selector_apo.py` (training setup)
  - `INTEGRATION_GUIDE.md` (framework examples)

---

## 📎 Key Files to Show

| File | Purpose |
|------|---------|
| `room_selector.py` | The agent with `@rollout` decorator |
| `room_selector_apo.py` | APO training configuration |
| `frontend/src/pages/index.tsx` | Sparky dashboard UI |
| `INTEGRATION_GUIDE.md` | Framework integration examples |

---

## 💡 Demo Tips

1. **Start with the dashboard** - visuals are compelling
2. **Show real prompt evolution** - click table rows to reveal prompts
3. **Emphasize "zero code change"** - just decorator + template
4. **Have backup mock data** - in case live APO is slow
5. **Keep terminal visible** - shows real-time progress

---

## 🔗 Resources to Share

- **Agent Lightning GitHub**: https://github.com/microsoft/agent-lightning
- **Documentation**: https://microsoft.github.io/agent-lightning/
- **Discord**: https://discord.gg/RYk7CdvDR7
- **arXiv Paper**: https://arxiv.org/abs/2508.03680

---

*Good luck with your demo! ⚡*
