# Copyright (c) Microsoft. All rights reserved.
"""
LangGraph Wealth Onboarding Agent with Agent Lightning Instrumentation

This example demonstrates how to integrate a LangGraph agent with APO
for automatic prompt optimization in a wealth management KYC/AML use case.
"""

import os
import json
from typing import TypedDict, List, Optional, Literal, Annotated
from pathlib import Path

from langgraph.graph import StateGraph, END
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from agentlightning.litagent import rollout
from agentlightning.types import PromptTemplate

from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)


# ==============================================================================
# Data Types
# ==============================================================================
class ClientDetails(TypedDict, total=False):
    # Inheritance fields
    relationship_to_deceased: str
    deceased_name: str
    date_of_death: str
    jurisdiction: str
    # Business fields
    business_name: str
    business_type: str
    years_in_operation: int
    annual_revenue: int
    profit_margin: float


class WealthOnboardingTask(TypedDict):
    id: str
    client_name: str
    claim_type: str
    claimed_amount: int
    currency: str
    documents_provided: List[str]
    client_details: ClientDetails
    red_flags: List[str]
    expected_decision: str
    expected_risk: str
    reason: str
    task_input: str


# ==============================================================================
# LangGraph State Definition
# ==============================================================================
class AgentState(TypedDict):
    """State that flows through the LangGraph nodes."""
    # Input
    case_details: str
    system_prompt: str
    
    # Analysis results
    document_analysis: str
    red_flag_analysis: str
    risk_level: str
    
    # Output
    decision: str
    reason: str
    final_output: str


# ==============================================================================
# LangGraph Node Functions
# ==============================================================================
def analyze_documents(state: AgentState) -> AgentState:
    """Node 1: Analyze the provided documents."""
    llm = AzureChatOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1-mini"),
        temperature=0.0,
    )
    
    analysis_prompt = f"""Analyze the documents provided in this case.
List which required documents are present and which are missing.
Be concise (max 100 words).

Case:
{state['case_details']}"""

    response = llm.invoke([HumanMessage(content=analysis_prompt)])
    
    return {**state, "document_analysis": response.content}


def check_red_flags(state: AgentState) -> AgentState:
    """Node 2: Check for red flags and risk indicators."""
    llm = AzureChatOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1-mini"),
        temperature=0.0,
    )
    
    red_flag_prompt = f"""Identify any red flags or risk indicators in this case.
Consider: PEP connections, unusual profit margins, new businesses, high values, jurisdiction risks.
Rate risk as: low, medium, or high.
Be concise (max 100 words).

Case:
{state['case_details']}

Document Analysis:
{state['document_analysis']}"""

    response = llm.invoke([HumanMessage(content=red_flag_prompt)])
    
    # Extract risk level from response
    risk_level = "medium"  # default
    response_lower = response.content.lower()
    if "high risk" in response_lower or "risk: high" in response_lower:
        risk_level = "high"
    elif "low risk" in response_lower or "risk: low" in response_lower:
        risk_level = "low"
    
    return {**state, "red_flag_analysis": response.content, "risk_level": risk_level}


def make_decision(state: AgentState) -> AgentState:
    """Node 3: Make the final decision based on analysis."""
    llm = AzureChatOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1-mini"),
        temperature=0.0,
    )
    
    # Use the APO-optimized system prompt
    decision_prompt = f"""{state['system_prompt']}

Document Analysis:
{state['document_analysis']}

Red Flag Analysis:
{state['red_flag_analysis']}

Case Details:
{state['case_details']}"""

    response = llm.invoke([
        SystemMessage(content="You are a compliance analyst."),
        HumanMessage(content=decision_prompt)
    ])
    
    # Parse decision and reason from response
    decision = None
    reason = None
    
    for line in response.content.strip().split('\n'):
        line_lower = line.strip().lower()
        if line_lower.startswith('decision:'):
            decision = line_lower.replace('decision:', '').strip()
        elif line_lower.startswith('reason:'):
            reason = line.strip()[7:].strip()
    
    if not decision:
        decision = "escalate"  # default to safe option
    if not reason:
        reason = "Unable to determine - escalating for review"
    
    final_output = f"decision: {decision}\nreason: {reason}"
    
    return {
        **state, 
        "decision": decision, 
        "reason": reason,
        "final_output": final_output
    }


# ==============================================================================
# LangGraph Builder
# ==============================================================================
def create_wealth_onboarding_graph() -> StateGraph:
    """Create the LangGraph workflow for wealth onboarding."""
    
    # Build the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("analyze_documents", analyze_documents)
    workflow.add_node("check_red_flags", check_red_flags)
    workflow.add_node("make_decision", make_decision)
    
    # Define edges (linear flow)
    workflow.set_entry_point("analyze_documents")
    workflow.add_edge("analyze_documents", "check_red_flags")
    workflow.add_edge("check_red_flags", "make_decision")
    workflow.add_edge("make_decision", END)
    
    return workflow.compile()


# ==============================================================================
# Prompt Template (APO will optimize this)
# ==============================================================================
def prompt_template_baseline() -> PromptTemplate:
    """Baseline prompt template that APO will optimize."""
    return PromptTemplate(
        template=(
            "You are a wealth management compliance analyst evaluating client onboarding.\n"
            "Review the documentation for inheritance or business profit claims.\n"
            "\n"
            "DECISION OPTIONS:\n"
            "- approve: All required documentation present, low risk\n"
            "- conditional_approve: Documentation mostly complete, minor items needed\n"
            "- escalate: High-value or high-risk case requiring senior review\n"
            "- decline: Insufficient documentation or unacceptable risk\n"
            "\n"
            "Return exactly two lines:\n"
            "decision: [approve|conditional_approve|escalate|decline]\n"
            "reason: [Brief explanation in 100 characters or less]\n"
            "\n"
            "No additional text allowed.\n"
            "\n"
            "Case details:\n"
            "{task_input}"
        ),
        engine="f-string",
    )


# ==============================================================================
# Reward Calculation
# ==============================================================================
def calculate_reward(decision: str, expected_decision: str, expected_risk: str) -> float:
    """Calculate reward based on decision accuracy and risk appropriateness."""
    reward = 0.0
    valid_decisions = ["approve", "conditional_approve", "escalate", "decline"]
    
    # Format validity (40% of score)
    if decision in valid_decisions:
        reward += 0.4
    
    # Decision accuracy (40% of score)
    if decision == expected_decision:
        reward += 0.4
    else:
        # Partial credit for close decisions
        close_pairs = [
            ("approve", "conditional_approve"),
            ("conditional_approve", "escalate"),
            ("escalate", "decline")
        ]
        for pair in close_pairs:
            if decision in pair and expected_decision in pair:
                reward += 0.2
                break
    
    # Risk appropriateness (20% of score)
    if expected_risk == "high" and decision in ["escalate", "decline"]:
        reward += 0.2
    elif expected_risk == "low" and decision in ["approve", "conditional_approve"]:
        reward += 0.2
    elif expected_risk == "medium" and decision in ["conditional_approve", "escalate"]:
        reward += 0.2
    
    return reward


# ==============================================================================
# APO-Instrumented Agent (with @rollout decorator)
# ==============================================================================
@rollout
def langgraph_wealth_agent(task: WealthOnboardingTask, prompt_template: PromptTemplate) -> float:
    """
    LangGraph-based wealth onboarding agent wrapped for APO optimization.
    
    The @rollout decorator enables:
    - Automatic tracing of agent execution
    - Integration with APO's optimization loop
    - Reward collection for gradient computation
    """
    
    # 1. Format the prompt using APO's template
    system_prompt = prompt_template.format(task_input=task["task_input"])
    
    # 2. Create and run the LangGraph agent
    graph = create_wealth_onboarding_graph()
    
    initial_state = AgentState(
        case_details=task["task_input"],
        system_prompt=system_prompt,
        document_analysis="",
        red_flag_analysis="",
        risk_level="",
        decision="",
        reason="",
        final_output=""
    )
    
    # Run the graph
    result = graph.invoke(initial_state)
    
    # 3. Calculate reward
    reward = calculate_reward(
        decision=result["decision"],
        expected_decision=task["expected_decision"],
        expected_risk=task["expected_risk"]
    )
    
    print(f"[LangGraph] Decision: {result['decision']} | Expected: {task['expected_decision']} | Reward: {reward}")
    
    return reward


# ==============================================================================
# Data Loading
# ==============================================================================
def format_task_input(scenario: dict) -> str:
    """Format a scenario into task_input string."""
    if scenario["claim_type"] == "inheritance":
        details = scenario["client_details"]
        return f"""CLIENT: {scenario['client_name']}
CLAIM TYPE: Inheritance
CLAIMED AMOUNT: {scenario['claimed_amount']:,} {scenario['currency']}

DECEASED INFO:
- Name: {details.get('deceased_name', 'Unknown')}
- Date of Death: {details.get('date_of_death', 'Unknown')}
- Relationship: {details.get('relationship_to_deceased', 'Unknown')}
- Jurisdiction: {details.get('jurisdiction', 'Unknown')}

DOCUMENTS PROVIDED: {', '.join(scenario['documents_provided'])}

RED FLAGS: {', '.join(scenario['red_flags']) if scenario['red_flags'] else 'None'}"""
    else:  # business_profit
        details = scenario["client_details"]
        profit_margin = details.get('profit_margin', 0)
        return f"""CLIENT: {scenario['client_name']}
CLAIM TYPE: Business Profit
CLAIMED AMOUNT: {scenario['claimed_amount']:,} {scenario['currency']}

BUSINESS INFO:
- Business Name: {details.get('business_name', 'Unknown')}
- Business Type: {details.get('business_type', 'Unknown')}
- Years in Operation: {details.get('years_in_operation', 'Unknown')}
- Annual Revenue: {details.get('annual_revenue', 0):,}
- Profit Margin: {profit_margin:.0%}

DOCUMENTS PROVIDED: {', '.join(scenario['documents_provided'])}

RED FLAGS: {', '.join(scenario['red_flags']) if scenario['red_flags'] else 'None'}"""


def load_sample_tasks() -> List[WealthOnboardingTask]:
    """Load sample tasks for testing."""
    # Try to load from JSON file, otherwise use inline samples
    data_path = Path(__file__).parent.parent.parent / "backend" / "wealth_onboarding_data.json"
    
    if data_path.exists():
        with open(data_path) as f:
            data = json.load(f)
        
        tasks = []
        for scenario in data["scenarios"][:5]:  # Just first 5 for demo
            task = WealthOnboardingTask(
                id=scenario["id"],
                client_name=scenario["client_name"],
                claim_type=scenario["claim_type"],
                claimed_amount=scenario["claimed_amount"],
                currency=scenario["currency"],
                documents_provided=scenario["documents_provided"],
                client_details=scenario["client_details"],
                red_flags=scenario["red_flags"],
                expected_decision=scenario["expected_decision"],
                expected_risk=scenario["expected_risk"],
                reason=scenario["reason"],
                task_input=format_task_input(scenario)
            )
            tasks.append(task)
        return tasks
    
    # Inline sample if file not found
    return [
        WealthOnboardingTask(
            id="sample_001",
            client_name="John Smith",
            claim_type="inheritance",
            claimed_amount=250000,
            currency="USD",
            documents_provided=["death_certificate", "will", "probate_documents", "bank_statements"],
            client_details={
                "relationship_to_deceased": "Son",
                "deceased_name": "Robert Smith",
                "date_of_death": "2024-06-15",
                "jurisdiction": "New York, USA"
            },
            red_flags=[],
            expected_decision="approve",
            expected_risk="low",
            reason="Complete documentation, direct family relationship",
            task_input="""CLIENT: John Smith
CLAIM TYPE: Inheritance
CLAIMED AMOUNT: 250,000 USD

DECEASED INFO:
- Name: Robert Smith
- Date of Death: 2024-06-15
- Relationship: Son
- Jurisdiction: New York, USA

DOCUMENTS PROVIDED: death_certificate, will, probate_documents, bank_statements

RED FLAGS: None"""
        )
    ]


# ==============================================================================
# Main - Test the agent
# ==============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("LangGraph Wealth Onboarding Agent - Test Run")
    print("=" * 60)
    
    # Load sample tasks
    tasks = load_sample_tasks()
    print(f"\nLoaded {len(tasks)} sample tasks")
    
    # Get baseline prompt
    prompt = prompt_template_baseline()
    
    # Run agent on each task
    total_reward = 0.0
    for i, task in enumerate(tasks):
        print(f"\n--- Task {i+1}: {task['client_name']} ({task['claim_type']}) ---")
        reward = langgraph_wealth_agent(task, prompt)
        total_reward += reward
    
    print(f"\n{'=' * 60}")
    print(f"Average Reward: {total_reward / len(tasks):.2%}")
    print("=" * 60)
