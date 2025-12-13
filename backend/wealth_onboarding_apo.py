# Copyright (c) Microsoft. All rights reserved.
"""
Wealth Client Onboarding APO Example

This example demonstrates Automatic Prompt Optimization (APO) for a wealth management
bank onboarding use case. The agent evaluates client claims for:
- Inheritance claims (death, probate, wills)
- Business profit claims (financial statements, tax returns)
"""
import logging
from typing import Tuple, cast, TypedDict, List, Optional
import json
import os
from pathlib import Path

from openai import OpenAI, AsyncOpenAI
from rich.console import Console

from agentlightning import Trainer
from agentlightning.logging import setup as setup_logging
from agentlightning.adapter import TraceToMessages
from agentlightning.algorithm.apo import APO
from agentlightning.litagent import rollout
from agentlightning.types import Dataset, PromptTemplate

from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

console = Console()


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
    claim_type: str  # 'inheritance' or 'business_profit'
    claimed_amount: int
    currency: str
    documents_provided: List[str]
    client_details: ClientDetails
    red_flags: List[str]
    expected_decision: str  # approve, conditional_approve, escalate, decline
    expected_risk: str  # low, medium, high
    reason: str
    task_input: str  # Formatted input for the prompt template


# ==============================================================================
# Seed Prompt Template
# ==============================================================================
def prompt_template_baseline() -> PromptTemplate:
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
# Dataset Loading
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


def load_wealth_tasks() -> List[WealthOnboardingTask]:
    """Load wealth onboarding scenarios from JSON file."""
    data_path = Path(__file__).parent / "wealth_onboarding_data.json"
    with open(data_path) as f:
        data = json.load(f)
    
    # Convert scenarios to task format
    tasks = []
    for scenario in data["scenarios"]:
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


def load_train_val_dataset() -> Tuple[Dataset[WealthOnboardingTask], Dataset[WealthOnboardingTask]]:
    """Load and split wealth onboarding dataset."""
    dataset_full = load_wealth_tasks()
    train_split = len(dataset_full) // 2
    dataset_train = [dataset_full[i] for i in range(train_split)]
    dataset_val = [dataset_full[i] for i in range(train_split, len(dataset_full))]
    return cast(Dataset[WealthOnboardingTask], dataset_train), cast(Dataset[WealthOnboardingTask], dataset_val)


# ==============================================================================
# Agent Function
# ==============================================================================
def parse_decision(response: str) -> tuple[Optional[str], Optional[str]]:
    """Parse the agent's response to extract decision and reason."""
    decision = None
    reason = None
    
    for line in response.strip().split('\n'):
        line_lower = line.strip().lower()
        if line_lower.startswith('decision:'):
            decision = line_lower.replace('decision:', '').strip()
        elif line_lower.startswith('reason:'):
            reason = line.strip()[7:].strip()
    
    return decision, reason


@rollout
def wealth_onboarding_agent(task: WealthOnboardingTask, prompt_template: PromptTemplate) -> float:
    """
    Wealth onboarding compliance agent.
    
    Evaluates client documentation and returns a reward based on:
    1. Decision accuracy (matches expected)
    2. Risk assessment appropriateness
    3. Response format compliance
    """
    # Create client
    client = OpenAI(
        base_url=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        default_headers={"api-key": os.getenv("AZURE_OPENAI_API_KEY")}
    )
    model = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1-mini")
    
    # Format the user message using the prompt template
    user_message = prompt_template.format(task_input=task["task_input"])
    
    console.print(f"[bold yellow]=== User Message ===[/bold yellow]")
    console.print(user_message[:500] + "..." if len(user_message) > 500 else user_message)
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a compliance analyst."},
            {"role": "user", "content": user_message}
        ],
        temperature=0.0,
        max_tokens=150
    )
    
    response_text = response.choices[0].message.content or ""
    
    console.print(f"[bold yellow]=== Response ===[/bold yellow]")
    console.print(response_text)
    
    # Calculate reward
    decision, reason = parse_decision(response_text)
    expected_decision = task["expected_decision"]
    expected_risk = task["expected_risk"]
    
    reward = 0.0
    
    # Check format validity (40% of score)
    valid_decisions = ["approve", "conditional_approve", "escalate", "decline"]
    if decision in valid_decisions:
        reward += 0.2
    if reason and len(reason) > 5:
        reward += 0.2
    
    # Check decision accuracy (40% of score)
    if decision == expected_decision:
        reward += 0.4
    elif decision and expected_decision:
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
    
    console.print(f"[bold green]=== Reward: {reward} ===[/bold green]")
    console.print(f"Expected: {expected_decision}, Got: {decision}")
    
    return reward


# ==============================================================================
# Logging Setup
# ==============================================================================
def setup_apo_logger(file_path: str = "apo.log") -> None:
    """Dump a copy of all the logs produced by APO algorithm to a file."""
    file_handler = logging.FileHandler(file_path)
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] (Process-%(process)d %(name)s)   %(message)s")
    file_handler.setFormatter(formatter)
    logging.getLogger("agentlightning.algorithm.apo").addHandler(file_handler)


# ==============================================================================
# Main Entry Point
# ==============================================================================
def main() -> None:
    setup_logging()
    setup_apo_logger()

    # Verify Azure configuration
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
    azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    
    if not azure_endpoint or not azure_api_key:
        raise RuntimeError("AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY must be set in the environment.")
    
    openai_client = AsyncOpenAI(
        base_url=azure_endpoint,
        api_key=azure_api_key,
        default_headers={"api-key": azure_api_key}
    )

    # Load datasets
    dataset_train, dataset_val = load_train_val_dataset()
    
    # Configure APO
    algo = APO[WealthOnboardingTask](
        openai_client,
        val_batch_size=10,
        gradient_batch_size=4,
        beam_width=2,
        branch_factor=2,
        beam_rounds=2,
        _poml_trace=True,
    )

    # Create trainer
    trainer = Trainer(
        algorithm=algo,
        n_runners=8,
        initial_resources={
            "prompt_template": prompt_template_baseline()
        },
        adapter=TraceToMessages(),
    )

    print("=" * 60)
    print("Wealth Client Onboarding - Automatic Prompt Optimization")
    print("=" * 60)
    print(f"\nTraining tasks: {len(dataset_train)}")
    print(f"Validation tasks: {len(dataset_val)}")
    print("\nStarting APO optimization...")

    # Run optimization
    trainer.fit(
        agent=wealth_onboarding_agent,
        train_dataset=dataset_train,
        val_dataset=dataset_val
    )

    print("\n" + "=" * 60)
    print("Optimization Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
