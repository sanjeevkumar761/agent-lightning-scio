# Copyright (c) Microsoft. All rights reserved.

"""This sample code demonstrates how to use an existing APO algorithm to tune the prompts."""

import logging
from typing import Tuple, cast

import os
from openai import AsyncOpenAI
from room_selector import RoomSelectionTask, load_room_tasks, prompt_template_baseline, room_selector

from agentlightning import Trainer
from agentlightning.logging import setup as setup_logging
from agentlightning.adapter import TraceToMessages
from agentlightning.algorithm.apo import APO
from agentlightning.types import Dataset


def load_train_val_dataset() -> Tuple[Dataset[RoomSelectionTask], Dataset[RoomSelectionTask]]:
    dataset_full = load_room_tasks()
    train_split = len(dataset_full) // 2
    dataset_train = [dataset_full[i] for i in range(train_split)]
    dataset_val = [dataset_full[i] for i in range(train_split, len(dataset_full))]
    return cast(Dataset[RoomSelectionTask], dataset_train), cast(Dataset[RoomSelectionTask], dataset_val)


def setup_apo_logger(file_path: str = "apo.log") -> None:
    """Dump a copy of all the logs produced by APO algorithm to a file."""

    file_handler = logging.FileHandler(file_path)
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] (Process-%(process)d %(name)s)   %(message)s")
    file_handler.setFormatter(formatter)
    logging.getLogger("agentlightning.algorithm.apo").addHandler(file_handler)



def main() -> None:
    setup_logging()
    setup_apo_logger()

    # Explicit Azure OpenAI client construction
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
    azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")
    if not azure_endpoint or not azure_api_key:
        raise RuntimeError("AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY must be set in the environment.")

    openai_client = AsyncOpenAI(
        base_url=azure_endpoint,
        api_key=azure_api_key,
        default_headers={"api-key": azure_api_key}
    )

    algo = APO[RoomSelectionTask](
        openai_client,
        val_batch_size=10,
        gradient_batch_size=4,
        beam_width=2,
        branch_factor=2,
        beam_rounds=2,
        _poml_trace=True,
    )
    trainer = Trainer(
        algorithm=algo,
        n_runners=8,
        initial_resources={
            "prompt_template": prompt_template_baseline()
        },
        adapter=TraceToMessages(),
    )
    dataset_train, dataset_val = load_train_val_dataset()
    trainer.fit(agent=room_selector, train_dataset=dataset_train, val_dataset=dataset_val)


if __name__ == "__main__":
    main()
