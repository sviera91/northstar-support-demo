# Coding Agent Instructions

This project is a **Microsoft Foundry hosted agent** — a containerized AI agent that runs in [Foundry Agent Service](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/hosted-agents). The platform handles containerization, hosting, security, scaling, and observability so you can focus on agent logic.

This project was built with the microsoft-foundry skill. Before working on or answering questions about foundry agents, read the microsoft-foundry skill first.

## Invariants

- All customer and order data must remain synthetic.
- Never commit Azure identifiers, endpoints, credentials, local `.azure/` state,
  logs, or presenter-specific configuration.
- Keep the server-side date fixed at 2026-11-04; day 30 is included.
- Eligibility is not refund authorization. No write-capable runtime tools.
- Run `pytest -q` before changing the deterministic eligibility contract.
- Skills/MCP/plugins used by Copilot are build-time capabilities, not automatically
  tools of the deployed agent.
- Keep virtual environments, dependency certificate bundles and generated
  dependency archives outside synced storage. For local uv commands, set
  `UV_PROJECT_ENVIRONMENT="$HOME/.local/share/northstar-support/venv"` first;
  never recreate `.venv` in a OneDrive/SharePoint checkout. Git ignores do not
  prevent OneDrive sync.

## Key files

- `src/northstar_support/main.py`: Responses hosting and explicit tool registration.
- `src/northstar_support/returns.py`: deterministic business logic.
- `src/northstar_support/policies.md`: versioned policy pack.
- `azure.yaml`: portable deployment definition; no presenter Azure values.

## Development workflow

The **Azure Developer CLI (`azd`)** manages the full lifecycle:

```bash
azd ai agent run                           # Run locally on http://localhost:8088
azd ai agent invoke --local "your message" # Test the local agent
azd deploy                                 # Deploy to Foundry
azd ai agent invoke "your message"         # Invoke the deployed agent
```

## Microsoft Foundry Skill

Install the **Microsoft Foundry Skill** for guided deployment, evaluation, and troubleshooting workflows.

Direct install (preferred, works with any coding agent):

```bash
npx skills add https://github.com/microsoft/azure-skills --skill microsoft-foundry
```

Or install the Azure Skills Plugin:

- **Copilot CLI**: `/plugin marketplace add microsoft/azure-skills` then `/plugin install azure@azure-skills`
- **Claude Code**: `/plugin install azure@claude-plugins-official`

Then ask naturally, e.g. `Use the Microsoft Foundry Skill to deploy this agent.`

## References

- [Hosted agents overview](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/hosted-agents)
- [Microsoft Foundry Skill](https://learn.microsoft.com/en-us/azure/foundry/how-to/develop/use-microsoft-foundry-skill)