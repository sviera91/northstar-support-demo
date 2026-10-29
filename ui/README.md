# Local customer-care website

This thin UI makes the fictional customer experience visible. The **agent code
runs in Foundry**, not in this proxy. The page has no canned agent answers.
Its initial greeting and suggested questions are UI copy, not model output.
Customer-facing copy and agent replies use ordinary store-support language;
one footer disclosure identifies the fictional workshop scenario. Deployment
details and policy identifiers stay out of routine customer conversations.

1. Deploy and verify the hosted agent as described in `docs/deployment.md`.
2. Authenticate locally to Azure with an identity allowed to invoke that agent.
3. Copy `ui/.env.example` to `ui/.env`. Set the exact Responses endpoint returned
   by `azd ai agent show`, including its API-version query if present.
4. From the repository root, create/use an environment outside synced storage:

   ```bash
   export UV_PROJECT_ENVIRONMENT="$HOME/.local/share/northstar-support/venv"
   uv sync --project src/northstar_support --frozen
   "$UV_PROJECT_ENVIRONMENT/bin/python" ui/server.py
   ```

   Do not create `.venv` inside a OneDrive/SharePoint checkout: dependency
   certificate bundles are synced too, regardless of `.gitignore`.

5. Open `http://127.0.0.1:7071`. Add `?scoutTheme=light` or `?scoutTheme=dark`
   to choose a theme. Stop with Ctrl+C.

The local server uses `DefaultAzureCredential` and obtains short-lived Azure
tokens server-side. The endpoint and token are never sent to the browser.
Conversation history lives in process memory, keyed by an HttpOnly cookie;
select **New chat** to clear both the visible conversation and its server-side
history before an independent check. Refreshing alone only clears the visible
messages. New chat does not call Foundry, reset rate limits, or clear other
browser sessions. Wait for any reply to finish before resetting.
Requests have size, turn and rate limits.
The server binds only to loopback and checks Host/Origin; it is **not ready for
anonymous public hosting**. A hosted version needs access control, HTTPS,
managed identity, cross-instance state and an abuse/cost policy.

Neither the page nor `/health` proves the agent is reachable. Only a successful
chat response from the real endpoint does. Errors remain visible and are never
replaced with simulated success.

An upstream safety-filter rejection is shown as a request refusal (HTTP 422),
not a service outage. Rejected requests do not enter conversation history.
Other incomplete responses and upstream failures remain explicit errors;
partial assistant text is not presented as a completed answer.
