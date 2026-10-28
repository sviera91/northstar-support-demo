# Northstar Support

Learn the **GitHub Copilot App** by building a fictional returns-support agent,
then run your code as a **Microsoft Foundry hosted agent**.

This is a presenter-led teaching example, not a production support application.
Every order is fake. There is no customer database, payment integration,
vector search, or real personal data. A thin local customer-care chat UI calls
the real hosted agent through a server-side proxy; it is not separately hosted.

## What runs where

```text
BUILD TIME                               RUNTIME
Copilot App + repository                 Foundry hosted agent (your Python code)
  instructions, sessions, worktrees         versioned policy pack
  skills, plugins, MCP, canvases            lookup_order -> synthetic fixtures
  tests, review and GitHub Actions          deterministic eligibility helper
```

Copilot's skills, plugins and MCP connections do **not** automatically become
tools of the deployed support agent. Its only tool is explicitly registered,
read-only `lookup_order`.

### What the agent actually reads

`instructions.md` and `policies.md` are loaded into the agent's instructions at
startup. The model uses that policy context and the conversation; there is no
vector index, document search, or fine-tuning.

The three orders live in `src/northstar_support/orders.json`, packaged with the
Python agent. They are not database records. The model asks the registered
`lookup_order` tool for an order; `returns.py` reads the fixture and calculates
eligibility against the fixed server date. The tool returns facts and an
eligibility result, and the model explains them. It cannot issue a refund.

The runtime uses Microsoft Agent Framework's `Agent`, `FoundryChatClient`, and
`ResponsesHostServer`. The sample deployment requests `gpt-4.1-mini`; use a
supported model deployment in your own project. Browser messages go through the
local Python proxy to the hosted agent; Azure credentials stay server-side.

## Start without Azure (free)

Python 3.13 or later and [uv](https://docs.astral.sh/uv/) are required.

```bash
git clone https://github.com/sviera91/northstar-support-demo.git
cd northstar-support-demo/src/northstar_support
uv sync --frozen
uv run pytest -q ../../tests
uv run ruff check main.py returns.py ../../tests
```

The deterministic rules need no credentials, model, or cloud resources. Public
CI runs the same rules without Azure access. Model-backed local chat and hosted
deployment require your own Azure subscription and can incur charges.

## Try the customer conversation

- `What's your return policy?`
- `Hi, can I return the headphones I bought?`
  Then: `Sure, it's CHI1001. They're still in the box.`
- `My order never showed up. The number is CHI9999. Where is it?`

The server evaluates all returns as of **2026-11-04**; customers never supply
the current date. `CHI1001` is day 15, `CHI1002` day 45, and `CHI1003` day 30.
Day 30 is included. Eligibility never authorizes or executes a refund.

## Follow the workshop

- [Copilot App teaching exercises and demo checkpoints](docs/workshop.md)
- [Recreate, deploy through Actions, verify and clean up](docs/deployment.md)
- [Eight agent behavior checks](evals/behavior-checks.json)
- [Run the local customer-care website](ui/README.md)
- [Policy pack](src/northstar_support/policies.md)
- [Source provenance and notices](THIRD_PARTY_NOTICES.md)

The hosted baseline uses Microsoft Agent Framework, the Responses protocol,
source-code deployment (no customer-managed ACR), 0.5 vCPU / 1 GiB per active
session, and a small pay-as-you-go model. Package versions are pinned in
`uv.lock` and the exported `requirements.txt`. Model availability, quotas and
hosted-agent regional support must be checked in your own subscription.

## Privacy and limitations

This repository intentionally contains no presenter's Azure identifiers,
endpoints, credentials, deployment logs or private configuration. Deployments
run in a separate private repository against a reviewed source commit.
The portable reusable workflow here does not run on public pushes or PRs.

Order-number-only lookup is **not production authorization**. Prompt rules
are not a complete security boundary. Production use requires authentication,
per-customer authorization, real data governance, operational monitoring,
and broader adversarial and quality evaluation.

MIT licensed; adapted Microsoft sample portions retain their notices.
