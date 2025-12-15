# APO Integration Guide

## Using APO with Any Agent Framework

The APO framework is **framework-agnostic** - you just need to wrap your agent in a function with the right signature.

## Integration Pattern

The APO only requires:
1. A function decorated with `@rollout`
2. Signature: `(task: YourTaskType, prompt_template: PromptTemplate) -> float`
3. Returns a reward (0.0 to 1.0)

## LangGraph Example

```python
from langgraph.graph import StateGraph, END
from langchain_openai import AzureChatOpenAI
from agentlightning.litagent import rollout
from agentlightning.types import PromptTemplate

# Your LangGraph agent definition
def create_langgraph_agent(prompt: str):
    """Create a LangGraph agent with the given system prompt."""
    
    llm = AzureChatOpenAI(
        azure_deployment="gpt-4.1",
        api_version="2024-02-15-preview"
    )
    
    # Define your graph state
    class AgentState(TypedDict):
        messages: list
        result: str
    
    # Define nodes
    def call_model(state: AgentState):
        messages = [{"role": "system", "content": prompt}] + state["messages"]
        response = llm.invoke(messages)
        return {"result": response.content}
    
    # Build graph
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", call_model)
    workflow.set_entry_point("agent")
    workflow.add_edge("agent", END)
    
    return workflow.compile()

# APO-compatible wrapper
@rollout
def langgraph_agent(task: MyTaskType, prompt_template: PromptTemplate) -> float:
    """Wrap LangGraph agent for APO optimization."""
    
    # 1. Format the prompt using APO's template
    system_prompt = prompt_template.format(**task["task_input"])
    
    # 2. Create and run your LangGraph agent
    agent = create_langgraph_agent(system_prompt)
    result = agent.invoke({"messages": [{"role": "user", "content": task["query"]}]})
    
    # 3. Calculate reward (your evaluation logic)
    reward = evaluate_result(result["result"], task["expected"])
    
    return reward
```

## Key Points

| Component | What APO Optimizes | What You Control |
|-----------|-------------------|------------------|
| `prompt_template` | ✅ APO tunes this | Use `prompt_template.format()` |
| Agent logic | ❌ Unchanged | LangGraph, LangChain, CrewAI, etc. |
| Reward function | ❌ Unchanged | Your evaluation metric |

## Works With Any Framework

### AutoGen

```python
@rollout
def autogen_agent(task, prompt_template) -> float:
    prompt = prompt_template.format(**task["input"])
    assistant = AssistantAgent("assistant", system_message=prompt)
    # ... run autogen conversation
    return reward
```

### CrewAI

```python
@rollout  
def crewai_agent(task, prompt_template) -> float:
    prompt = prompt_template.format(**task["input"])
    agent = Agent(role="analyst", goal=prompt, ...)
    # ... run crew
    return reward
```

### Plain OpenAI

```python
@rollout
def openai_agent(task, prompt_template) -> float:
    prompt = prompt_template.format(**task["input"])
    response = client.chat.completions.create(
        messages=[{"role": "system", "content": prompt}, ...]
    )
    return reward
```

## How It Works

The `@rollout` decorator handles all the tracing and integration with APO's optimization loop. Your agent just needs to:

1. **Use the `prompt_template`** - Call `prompt_template.format()` with your task variables
2. **Return a reward** - A float between 0.0 and 1.0 indicating task success

APO will automatically:
- Run your agent on training tasks
- Analyze what works and what doesn't
- Generate improved prompt variations
- Evaluate on validation tasks
- Select the best performing prompt

## Complete Example Structure

```
your_project/
├── agent.py           # Your @rollout wrapped agent
├── data.json          # Training/validation tasks
├── apo_runner.py      # APO configuration and training loop
└── requirements.txt
```

### apo_runner.py

```python
from agentlightning import Trainer
from agentlightning.adapter import TraceToMessages
from agentlightning.algorithm.apo import APO
from agentlightning.types import Dataset, PromptTemplate

from your_agent import your_agent, YourTaskType, load_tasks

def main():
    # Load datasets
    train_data, val_data = load_tasks()
    
    # Configure APO
    algo = APO[YourTaskType](
        openai_client,
        val_batch_size=10,
        gradient_batch_size=4,
        beam_width=2,
        branch_factor=2,
        beam_rounds=2,
    )
    
    # Initial prompt template
    initial_prompt = PromptTemplate(
        template="Your baseline prompt with {variables}...",
        engine="f-string",
    )
    
    # Create trainer
    trainer = Trainer(
        algorithm=algo,
        n_runners=8,
        initial_resources={"prompt_template": initial_prompt},
        adapter=TraceToMessages(),
    )
    
    # Run optimization
    trainer.fit(
        agent=your_agent,
        train_dataset=train_data,
        val_dataset=val_data
    )

if __name__ == "__main__":
    main()
```
