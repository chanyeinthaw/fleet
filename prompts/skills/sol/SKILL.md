---
name: sol
metadata:
  harness: [pi, codex, claude]
disable-model-invocation: true
description: Coordinate delegated work with configurable worker models, worker-owned verification, and optional independent review.
---

# Sol

The primary agent leads using the model the user selected. Never require or change the primary model. Activate this workflow only when explicitly requested.

## Configuration

Accept model and reasoning choices from the invocation, for example:

```text
$sol ocg/deepseek-v4.1-flash high for worker, gpt-6.1-sol low for reviewer
```

Resolve aliases against the harness's available model catalog. Ask when an alias is ambiguous.

- Worker: use the specified model. If omitted, ask before delegating. Accept implementer or implementor as aliases for worker.
- Reviewer: use the specified model; otherwise use the current primary model in a fresh subagent.
- Reasoning: honor explicit settings. Otherwise use the selected model's default.
- Concurrency: default to two active children unless the user specifies another limit.
- Never silently substitute models or reasoning settings. If a requested setting is unavailable, ask how to proceed.

Keep these choices for the current task. Use delegation tools that support the requested provider, model, and options, and check the returned selection. Do not assume a native agent list includes every available model.

## Modes

### Delegate

A worker completes a bounded task, including relevant verification. Tasks may involve research, investigation, implementation, or verification. The primary inspects the result, coordinates any integration, and decides whether it meets the acceptance criteria. No separate reviewer.

### Full

A worker completes the task and relevant verification. The primary coordinates any integration. A fresh, read-only reviewer then inspects the accumulated result.

The reviewer reports blocking findings or accepts the result. A worker fixes accepted findings and runs the affected checks, then the primary requests a fresh review.

### Select the mode

Honor an explicit mode. If the user specifies a reviewer, use full mode. Otherwise default to delegate mode. In full mode without a reviewer model, use the primary model in a fresh subagent.

## Primary responsibilities

Keep scope, delegation, coordination, and final acceptance in the primary session. Delegate task-level design, investigation, implementation, and verification to workers. Resolve decisions that affect multiple tasks or change the requirements in the primary session.

Delegate bounded tasks through completion. Before parallel work, assign exclusive file ownership and define interfaces. Keep shared wiring with one named worker. Use a shared checkout for disjoint edits; use isolated worktrees when the work needs independent changes to overlapping files. Account for whether uncommitted changes reach an isolated checkout.

Each child receives a self-contained brief containing:

- Objective and acceptance criteria.
- Relevant codebase context.
- Exact file ownership and prohibited changes.
- Interface and dependency contracts.
- Constraints and authorized behavior changes.
- Verification requirements.

Workers report the result, changed files or supporting evidence, checks run and their outcomes, and unresolved issues. Keep reports concise; include enough evidence for acceptance without making the primary repeat the task.

Do not copy the entire conversation into child context. For native Codex children, use `fork_turns="none"` and an appropriate available agent profile. Do not allow recursive delegation unless the user authorizes it.

## Integration and verification

Inspect the result and supporting evidence against the acceptance criteria. For code changes, inspect the diff and its scope. Use worker verification results when they cover the accepted changes; do not routinely rerun their checks or repeat their investigation. Run additional checks only to cover integration changes, missing evidence, failures, or a concrete concern.

Delegate integration work when needed. The primary may handle small coordination fixes, but should not take over a worker's task by default. After integration changes, have the responsible worker run affected checks unless running them directly is simpler.

Do not add imports or registrations for modules that do not exist yet. Coordinate dependency handoffs before starting dependent work.

Distinguish completed work, worker verification, independent verification, and unresolved work. Do not expand into another task or implementation wave without authorization.

## Independent review

In full mode, use a fresh reviewer after any integration and relevant verification. The reviewer:

- Remains read-only.
- Examines the actual result and supporting evidence against the requirements.
- Reports concrete bugs, regressions, and missing safeguards.
- Does not implement fixes.

Assess findings against source and evidence. Fix valid findings. Record a reason for rejecting a finding.

Use a new review task after corrections. Include the original requirements, prior findings, fixes, and unresolved objections. Do not treat an old approval as acceptance of changed code.

## Questions and failures

Answer child questions from existing requirements when possible. Ask the user when a decision changes scope, behavior, or authority.

Before retrying a failed child, inspect partial changes and confirm that the previous task is no longer active. Allow one fresh retry for a transient provider failure. If it fails again, report the blocker and ask how to proceed. Never silently switch models or enter a retry loop.

## Stop and finish

Track every active child. On a stop request, cancel all active children and stop further work. Report cancellation requests honestly rather than claiming confirmed termination prematurely.

Finish with a concise summary of results, verification performed and by whom, and remaining gaps. Do not claim success while required work remains.
