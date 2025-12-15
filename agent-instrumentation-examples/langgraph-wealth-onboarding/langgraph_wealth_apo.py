# Copyright (c) Microsoft. All rights reserved.
"""
APO Runner for LangGraph Wealth Onboarding Agent

This script runs Automatic Prompt Optimization (APO) on the LangGraph
wealth onboarding agent to find the optimal prompt for KYC/AML decisions.
"""

import logging
import json
from typing import Tuple, cast, List
from pathlib import Path

from openai import AsyncOpenAI

from agentlightning import Trainer
from agentlightning.logging import setup as setup_logging
from agentlightning.adapter import TraceToMessages
from agentlightning.algorithm.apo import APO
from agentlightning.types import Dataset

from langgraph_wealth_agent import (
    WealthOnboardingTask,
    langgraph_wealth_agent,
    prompt_template_baseline,
    format_task_input
)

from dotenv import load_dotenv
import os

# Load environment variables
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)


# ==============================================================================
# Dataset Loading
# ==============================================================================
def load_train_val_dataset() -> Tuple[Dataset[WealthOnboardingTask], Dataset[WealthOnboardingTask]]:
    """Load and split wealth onboarding dataset."""
    data_path = Path(__file__).parent.parent.parent / "backend" / "wealth_onboarding_data.json"
    
    with open(data_path) as f:
        data = json.load(f)
    
    # Convert scenarios to task format
    tasks: List[WealthOnboardingTask] = []
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
    
    # Split into train/val
    train_split = len(tasks) // 2
    dataset_train = tasks[:train_split]
    dataset_val = tasks[train_split:]
    
    return cast(Dataset[WealthOnboardingTask], dataset_train), cast(Dataset[WealthOnboardingTask], dataset_val)


# ==============================================================================
# Logging Setup
# ==============================================================================
def setup_apo_logger(file_path: str = "langgraph_apo.log") -> None:
    """Dump a copy of all the logs produced by APO algorithm to a file."""
    file_handler = logging.FileHandler(file_path)
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] (%(name)s) %(message)s")
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
    
    if not azure_endpoint or not azure_api_key:
        raise RuntimeError("AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY must be set")
    
    # Create OpenAI client for APO's gradient computation
    openai_client = AsyncOpenAI(
        base_url=azure_endpoint,
        api_key=azure_api_key,
        default_headers={"api-key": azure_api_key}
    )

    # Load datasets
    dataset_train, dataset_val = load_train_val_dataset()
    
    print("=" * 70)
    print("LangGraph Wealth Onboarding - Automatic Prompt Optimization")
    print("=" * 70)
    print(f"\nTraining tasks: {len(dataset_train)}")
    print(f"Validation tasks: {len(dataset_val)}")
    
    # Configure APO algorithm
    algo = APO[WealthOnboardingTask](
        openai_client,
        val_batch_size=10,      # Tasks per validation batch
        gradient_batch_size=4,  # Tasks for gradient computation
        beam_width=2,           # Top prompts to keep
        branch_factor=2,        # Variants per prompt
        beam_rounds=2,          # Optimization rounds
        _poml_trace=True,       # Enable detailed tracing
    )

    # Create trainer with initial prompt template
    trainer = Trainer(
        algorithm=algo,
        n_runners=8,  # Parallel workers
        initial_resources={
            "prompt_template": prompt_template_baseline()
        },
        adapter=TraceToMessages(),
    )

    print("\nStarting APO optimization with LangGraph agent...")
    print("This will run multiple rounds of prompt optimization.\n")

    # Run optimization
    trainer.fit(
        agent=langgraph_wealth_agent,
        train_dataset=dataset_train,
        val_dataset=dataset_val
    )

    print("\n" + "=" * 70)
    print("Optimization Complete!")
    print("=" * 70)
    print("\nCheck langgraph_apo.log for detailed optimization results.")


if __name__ == "__main__":
    main()
