"""Fail explicitly unless azd reports an active/deployed agent."""

import json
import sys
from pathlib import Path


def main() -> None:
    result = json.loads(Path(sys.argv[1]).read_text())
    status = result.get("status", "")
    if status.lower() not in {"active", "deployed"}:
        raise RuntimeError(f"Expected active/deployed agent, got status {status!r}.")
    print("Agent reports active/deployed status.")


if __name__ == "__main__":
    main()
