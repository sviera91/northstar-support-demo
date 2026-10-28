# Teach the App, using the agent

Use the [GitHub Copilot App](https://github.com/features/copilot/copilot-app)
as the build-time workbench. Install only documented, trusted capabilities and
review requested permissions. An unavailable optional plugin must not block
the core Python example.

| App concept | Practical exercise | Evidence to inspect |
| --- | --- | --- |
| Repository sessions | Open this repo and ask for an implementation plan | File context and plan before edits |
| Collaboration modes | Plan first, then approve bounded implementation | Mode and tool permissions are separate |
| Instructions | Read AGENTS.md; keep synthetic-data and date invariants | Rules in the actual changes |
| Skills | Use the public microsoft-foundry skill for the hosted-agent lifecycle | The skill's current recipe and prerequisite checks |
| MCP | Ask Microsoft Learn MCP for current hosted-agent protocol/region guidance | First-party URLs, not an unsourced answer |
| Plugins | Install the Azure skills plugin if not already available | Packaged skills/canvas capabilities, permissions |
| Canvases | Inspect configuration and deployment in Foundry Canvas | Shared configuration, not assumed deployment success |
| Focused sessions | Put independent work in a new worktree | New worktree isolates; current checkout shares |
| Copilot Fusion | Choose build-time effort and inspect its output | Not a model or feature of the runtime agent |
| Review and Actions | Inspect the diff, CI, private deploy and remote response | Correct source SHA and deployed version |

## Starting task prompt

> Build Northstar Support from this repository's policy pack and synthetic order
> fixtures. First propose a small implementation plan. Use a read-only order
> lookup and deterministic return eligibility, fixed server date 2026-11-04,
> with day 30 included. Ask for missing order number/condition. Never invent
> facts or execute refunds. Use the microsoft-foundry skill, and consult public
> Microsoft Learn MCP documentation for deployment details. Keep all Azure
> configuration private. Show tests and the diff before deployment.

## Honest checkpoints

These are **rehearsal milestones**, not claims that prerecorded deployment
evidence exists. Create tags only after reaching each state.

| Checkpoint | Required state |
| --- | --- |
| CP0 | Prepared opening agent has a successful remote invocation |
| CP1 | Reviewed brief and scaffold |
| CP2 | Working local model-backed invocation, tools and rules |
| CP3 | Deliberately seeded `< 30` bug and failing day-30 regression |
| CP4 | Corrected `<= 30` helper, passing regression, reviewed diff |
| CP5 | Corrected source deployed by Actions; remote invocation and version verified |

For the regression demo, create a **new worktree/branch** from the working
baseline. Say explicitly: "I seeded this boundary bug for the exercise."
Change only `elapsed_days <= 30` to `elapsed_days < 30` in `returns.py`.
Run the existing regression: it must fail for day 30. Ask Copilot to fix the
cause without weakening the test or policy, rerun it, and inspect the diff.
Do not reset or discard somebody else's dirty checkout.

## Eight behavior checks

Run the prompts in `evals/behavior-checks.json` against a model-backed local
agent and the deployed agent when rehearsing. Review both the answer and real
tool-call evidence. The deterministic unit tests do **not** prove these
language-model behaviors.

For outage testing, set `NORTHSTAR_SIMULATE_OUTAGE=1` in your **local** process,
restart it, and test the outage case. Remove the flag and restart afterward.
Never silently substitute a fabricated response or another endpoint.

Use the natural two-turn headphones prompt; don't put a test's expected answer
or the server date into the customer's mouth. Start a fresh conversation for
each independent check, but preserve history within the two-turn case.

The instruction-override prompt can be blocked by Foundry's safety filter
before the agent runs. A response with `status=incomplete` and
`incomplete_details.reason=content_filter` demonstrates that platform guard,
not independent proof of the agent's own instruction resistance. The local
website displays an explicit refusal rather than an infrastructure error.

With the pinned preview hosting SDK, recorded `function_call.arguments` can
contain a repeated JSON object. The correlated tool output and customer answer
were correct in the rehearsal checks, but that arguments string is not valid
JSON and must not be presented as a clean trace or blindly replayed. Keep raw
evidence private and distinguish this SDK serialization limitation from the
actual eligibility result. Do not repair traces by guessing or halving strings.

## Presenter pacing and fallback

Demonstrate the App controls before the implementation, then inspect local
tool evidence, the boundary regression, the diff and the private Actions run.
Show a remote response from the deployed version; calling a cloud model from
your laptop is not proof that agent code is hosted.

Stop live troubleshooting after 90 seconds. Use a clearly labeled rehearsal
capture or known working checkpoint. Never present fallback footage as a live
success. Do not screen-share private deployment logs or resource URLs without
reviewing them for Azure metadata first.
