"""Translate portable YAML and private ARM outputs without logging Azure values."""

import argparse
import json
import os
from pathlib import Path

import yaml


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=["parameters", "environment"])
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    manifest = yaml.safe_load(Path("azure.yaml").read_text())
    if args.operation == "parameters":
        args.path.write_text(json.dumps({
            "location": {"value": os.environ["AZURE_LOCATION"]},
            "foundryProjectName": {"value": os.environ["AZURE_AI_PROJECT_NAME"]},
            "deployments": {"value": manifest["services"]["ai-project"]["deployments"]},
            "includeAcr": {"value": False},
        }))
        return
    outputs = json.loads(args.path.read_text())
    required = ["AZURE_AI_PROJECT_ID", "FOUNDRY_PROJECT_ENDPOINT", "AZURE_AI_ACCOUNT_NAME"]
    for key in required:
        if not outputs.get(key, {}).get("value"):
            raise RuntimeError(f"Missing required ARM output: {key}")
    values = {key: output["value"] for key, output in outputs.items() if output.get("value")}
    values.update({
        "AZURE_SUBSCRIPTION_ID": os.environ["AZURE_SUBSCRIPTION_ID"],
        "AZURE_TENANT_ID": os.environ["AZURE_TENANT_ID"],
        "AZURE_LOCATION": os.environ["AZURE_LOCATION"],
        "AZURE_AI_MODEL_DEPLOYMENT_NAME": manifest["services"]["ai-project"]["deployments"][0]["name"],
        "AZURE_ENV_NAME": "northstar-ci",
    })
    target = Path(".azure/northstar-ci")
    target.mkdir(parents=True, exist_ok=True)
    (target.parent / "config.json").write_text(json.dumps({"defaultEnvironment": "northstar-ci"}))
    (target / ".env").write_text("".join(f"{key}={json.dumps(value)}\n" for key, value in values.items()))
    (target / ".env").chmod(0o600)


if __name__ == "__main__":
    main()
