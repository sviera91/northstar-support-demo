# Recreate the demo in your own Azure environment

## Prerequisites and costs

- Python 3.13+, uv, Git, GitHub CLI, Azure CLI, Azure Developer CLI 1.37.1+.
- Foundry azd extension `microsoft.foundry`; the tested agents extension is
  `azure.ai.agents` 1.0.0-beta.22.
- An Azure subscription with suitable model quota and hosted-agent availability.
  The checked baseline region is `northcentralus`; recheck for your subscription.
- Azure permissions to create an isolated resource group, managed identity,
  federated credential and scoped role assignments.

Install the tools from official documentation. Sign in yourself with MFA; never
paste credentials into chat or source. `azd` can use your Azure CLI authentication.

Public CI and deterministic tests require no Azure resources. Foundry's portal
being free does **not** mean hosted compute or model inference is free.
The October 28, 2026 public retail quote for North Central US was $0.0994/vCPU-hour
and $0.0118/GiB-hour: the selected 0.5 vCPU / 1 GiB is about **$0.0615 per
active session-hour**, plus model tokens and any other consumed services.
This is an estimate, not your bill or a spending guarantee.

Hosted compute scales to zero after session inactivity (15-minute default).
Each concurrent session has its own sandbox and cost. Do not run load tests.
There is no ACR, App Service, database, paid search, or custom frontend here.
Use cost alerts in your own account; alerts are not a hard cap.

## Public source / private deployment

Fork or clone this public repository. Create a separate **private** GitHub repo
for deployment. Keep its visibility private: workflow logs, environment URLs,
errors and ARM outputs can reveal Azure metadata even when credentials are
masked. A public workflow using secrets alone does not solve that privacy issue.

The reusable workflow `.github/workflows/azure-deploy.yml` has no push/PR trigger.
Call it only from your private deployment repository, pinning a reviewed full
source commit SHA:

```yaml
name: Deploy reviewed demo
on:
  workflow_dispatch:
    inputs:
      operation:
        type: choice
        options: [provision, deploy]
        required: true
permissions:
  contents: read
  id-token: write
jobs:
  deploy:
    uses: YOUR-OWNER/northstar-support-demo/.github/workflows/azure-deploy.yml@FULL_REVIEWED_COMMIT_SHA
    with:
      source_repository: YOUR-OWNER/northstar-support-demo
      source_sha: FULL_REVIEWED_COMMIT_SHA
      operation: ${{ inputs.operation }}
    secrets: inherit
```

There are no automatic deployments from forks, public pushes, or pull requests.
Do not change this to `pull_request_target` or expose Azure credentials to PR code.
Review the source and pinned workflow before every deploy.

## One-time bootstrap (operator-owned)

Create an empty demo resource group in the selected subscription and a
user-assigned managed identity in that group. Add a GitHub OIDC federated
credential with:

- Issuer: `https://token.actions.githubusercontent.com`
- Subject: `repo:YOUR-OWNER/YOUR-PRIVATE-DEPLOY-REPO:environment:demo`
- Audience: `api://AzureADTokenExchange`

Some GitHub OIDC configurations include immutable owner/repository IDs in
`sub`, such as `repo:OWNER@OWNER_ID/REPO@REPO_ID:environment:demo`. Inspect your
actual configured subject and match it exactly; do not broaden the trust or
remove the environment boundary. Never print or store the full OIDC token.

Ensure `Microsoft.CognitiveServices` is registered in the subscription before
provisioning. Resource-provider registration is a one-time operator task;
the resource-group-scoped Actions identity cannot register it.

Create a GitHub environment named `demo` in the private repo; restrict its
deployment branch to your reviewed default branch. Enable required reviewers
if your plan supports it. Manual dispatch and a trusted private default branch
are still necessary; an environment name alone is not an approval gate.

Grant that identity **Contributor** and **Foundry Owner** on the isolated
resource group only, not the subscription. Foundry Owner has Foundry data
permissions and a constrained list of roles it can assign. Review the current
role definition and your organization's policies; do not broaden to Owner or
User Access Administrator to bypass errors.

In the private repo, store these as Actions secrets, not public variables:

| Secret | Your own value |
| --- | --- |
| AZURE_CLIENT_ID | User-assigned managed identity client ID |
| AZURE_TENANT_ID | Directory ID |
| AZURE_SUBSCRIPTION_ID | Subscription ID |
| AZURE_RESOURCE_GROUP | Isolated demo group name |
| AZURE_AI_PROJECT_NAME | New project name, 3-32 letters/digits/hyphens |
| AZURE_LOCATION | Supported region, for example northcentralus |

No client secret or stored Azure access token is required. Only the exact
private-repository/environment OIDC subject is trusted.

## Provision, test locally, deploy

1. Dispatch the private workflow with `operation: provision`. It runs the
   business-rule suite, then deploys `infra/modules/resources.bicep` at resource
   group scope. Model settings come from `azure.yaml`. The generated
   subscription-scoped `infra/main.bicep` is **not** used by Actions.
2. Read the Foundry project endpoint from the **private** run/ARM output.
   Give your local developer identity Foundry User at the project scope if
   needed. Copy `.env.example` to `.env` inside `src/northstar_support` and
   supply your endpoint and deployed model name. Both are ignored by Git.
3. Configure the matching local azd environment. Existing azd env values
   override `.env`; keep the project endpoint and model aligned:

   ```bash
   azd env new my-demo --no-prompt
   azd env set AZURE_SUBSCRIPTION_ID YOUR_SUBSCRIPTION_ID
   azd env set AZURE_LOCATION northcentralus
   azd env set AZURE_AI_PROJECT_ID YOUR_PROJECT_ARM_ID
   azd env set FOUNDRY_PROJECT_ENDPOINT YOUR_PROJECT_ENDPOINT
   azd env set AZURE_AI_MODEL_DEPLOYMENT_NAME gpt-4.1-mini
   ```

4. From `src/northstar_support`, run `uv sync --frozen`, activate `.venv`,
   then `azd ai agent run --no-client`. This is a local agent calling an Azure
   model, not yet a hosted-code deployment. In another terminal run
   `azd ai agent invoke --local "Can I return CHI1003? The grinder is unopened."`
   Inspect tool evidence and stop the local server after testing.
5. Dispatch the private workflow with `operation: deploy`. It reads the stored
   ARM deployment outputs, deploys the reviewed source through `azd deploy`,
   confirms active/deployed status, and invokes the remote day-30 case.
   A failed or empty response is a failure, not a success-shaped fallback.
6. Rehearse all eight behavior checks; passing deterministic tests and one
   smoke call do not prove model quality or all safety behaviors.

The reusable workflow rejects calls from public repositories. It stores no
artifacts, prints no environment dump, and sends no Azure output back to the
public repository. Do not paste private logs into public issues.

## Cleanup

Review the exact demo group and its resources in Azure. Disable the endpoint
when not needed; idle session compute stops automatically. Delete the isolated
demo resource group only after confirming that it contains no unrelated work.
Group deletion also removes the managed identity; remove stale GitHub secrets
and deployment configuration when retiring the demo. This repository does not
perform automatic destructive cleanup.

## Official sources

- [Hosted agents and sizing](https://learn.microsoft.com/azure/foundry/agents/concepts/hosted-agents)
- [Hosted agent CI/CD](https://learn.microsoft.com/azure/foundry/agents/quickstarts/set-up-cicd-hosted-agent)
- [OIDC with Azure login](https://learn.microsoft.com/azure/developer/github/connect-from-azure#use-the-azure-login-action-with-openid-connect)
- [Foundry Agent Service pricing](https://azure.microsoft.com/pricing/details/foundry-agent-service/)
- [Microsoft Foundry Skill](https://learn.microsoft.com/azure/foundry/how-to/develop/use-microsoft-foundry-skill)
