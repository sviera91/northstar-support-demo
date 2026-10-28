# Adapted from Microsoft Foundry samples. See THIRD_PARTY_NOTICES.md.
import json
import logging
import os
from pathlib import Path
from typing import Annotated, Literal

from agent_framework import Agent, tool
from agent_framework.foundry import FoundryChatClient
from agent_framework_foundry_hosting import ResponsesHostServer
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from pydantic import Field

from returns import lookup

ROOT = Path(__file__).parent
logger = logging.getLogger(__name__)


@tool(approval_mode="never_require")
def lookup_order(
    order_id: Annotated[str, Field(description="Customer-supplied order number, such as CHI1001.")],
    condition: Annotated[
        Literal["unknown", "unopened", "opened", "defective"],
        Field(description="Customer-stated condition. Use unknown if they have not said."),
    ] = "unknown",
) -> str:
    """Read a fictional order and calculate return eligibility; never changes orders or issues refunds."""
    result = lookup(
        order_id, condition, simulate_outage=os.getenv("NORTHSTAR_SIMULATE_OUTAGE") == "1"
    )
    logger.info("lookup_order outcome=%s", result["status"])
    return json.dumps(result)


def build_agent() -> Agent:
    load_dotenv()
    model = os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME")
    if not model:
        raise RuntimeError("Set AZURE_AI_MODEL_DEPLOYMENT_NAME to your deployed model name.")
    client = FoundryChatClient(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        model=model,
        credential=DefaultAzureCredential(),
    )
    instructions = (ROOT / "instructions.md").read_text() + "\n" + (ROOT / "policies.md").read_text()
    return Agent(
        client=client,
        name="Northstar Support",
        instructions=instructions,
        tools=[lookup_order],
        default_options={"store": False},
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ResponsesHostServer(build_agent()).run()
