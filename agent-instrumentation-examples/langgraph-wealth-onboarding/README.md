# LangGraph Wealth Onboarding Agent with APO

This example demonstrates how to use **LangGraph** with **Agent Lightning's APO** (Automatic Prompt Optimization) for a wealth management client onboarding use case.

## Overview

The agent evaluates wealth client claims for:
- **Inheritance claims** (probate, wills, death certificates)
- **Business profit claims** (financial statements, tax returns)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    APO Optimization Loop                     │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │  Training   │ -> │  Gradient   │ -> │   New       │     │
│  │  Rollouts   │    │  Analysis   │    │   Prompts   │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│         │                                     │             │
│         v                                     v             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              LangGraph Agent                         │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌────────┐ │   │
│  │  │ Analyze │->│ Check   │->│ Decide  │->│ Format │ │   │
│  │  │ Docs    │  │ RedFlags│  │         │  │ Output │ │   │
│  │  └─────────┘  └─────────┘  └─────────┘  └────────┘ │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Setup

```bash
pip install langgraph langchain-openai agentlightning python-dotenv
```

## Files

- `langgraph_wealth_agent.py` - LangGraph agent with @rollout decorator
- `langgraph_wealth_apo.py` - APO training runner
- `wealth_data.json` - Training/validation scenarios

## Usage

```bash
# Run APO optimization
python langgraph_wealth_apo.py

# Or run a single agent test
python langgraph_wealth_agent.py
```

## Key Concepts

1. **@rollout decorator** - Wraps your agent for APO tracing
2. **PromptTemplate** - APO optimizes this automatically
3. **StateGraph** - LangGraph's state machine for agent logic
4. **Reward function** - Your success metric (0.0 to 1.0)
