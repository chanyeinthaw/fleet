---
name: implement
metadata:
  harness: [pi, codex, claude]
disable-model-invocation: true
description: Coordinate workers for research, implementation, verification, and chores, with configurable models and optional independent review. Activate only when explicitly requested.
---

# Implement

The primary coordinates the work using the model the user selected. Never require or change the primary model.

## First activation

Read `~/.config/fleet/implement-preset.md` as plain text. Invocation settings override presets.

Require worker and reviewer models, harnesses, and a mode. Ask for missing choices and confirm any the user did not explicitly specify before delegating. Save new presets; save invocation overrides only when asked.

Keep choices for the conversation. Never silently substitute unavailable settings. Read `Concurrency` from the preset, defaulting to two active children unless overridden in the invocation.

## Continuity signature

On first activation, randomly choose three distinct star names and show them. End every final response with the same phrase, including after compaction. Children do not sign.

This checks continuity, not factual accuracy.

## Roles

### Primary

Define scope and acceptance criteria, brief workers, coordinate dependencies, resolve decisions across tasks, assess results, and communicate with the user. Keep final acceptance in the primary session.

Read enough source or inspect a diff to assess a result. Delegate further investigation and execution instead of repeating a worker's work or taking over its task.

### Worker

Workers perform research, investigation, task-level design, implementation, verification, command execution, and routine chores. They also handle integration and corrections. Delegate bounded tasks through completion, including the checks needed to establish the result.

Each worker receives a self-contained brief with:

- Objective and acceptance criteria.
- Relevant context and supporting artifacts.
- File ownership and prohibited changes.
- Interfaces and dependencies.
- Constraints and authorized behavior changes.
- Verification requirements.

Workers report the result, changed files or supporting evidence, checks and outcomes, and unresolved issues. Reports must contain enough evidence for acceptance without making the primary repeat the task.

### Trivial-task exception

The primary may perform a task directly only when all of these conditions hold:

- It is simple, quick, and requires little effort to complete directly.
- The target and action are already known; no investigation, design decision, or debugging is needed.
- It is a bounded read, a small mechanical edit, or a routine command with an immediate result.
- It needs no long-running process, broad output analysis, or follow-up implementation.

Examples include reading a known file, checking Git status, correcting a known typo, or running one short targeted check. Do not split a larger task into trivial steps to avoid delegation. If the task grows beyond these limits, hand it to a worker with the evidence already gathered.

## Workflow

Both modes use workers and worker-owned verification:

- `delegate`: the primary assesses the worker's result and evidence, then accepts it or requests corrections.
- `full`: the same workflow adds a fresh, read-only reviewer after integration and verification. A worker fixes accepted findings and runs affected checks, followed by a fresh review.

Confirm the mode on first activation unless the user explicitly specified it. A configured reviewer does not imply full mode.

Before parallel work, assign exclusive file ownership and define interfaces. Give shared wiring to one named worker. Use a shared checkout for disjoint edits and isolated worktrees for independent changes to overlapping files. Account for whether uncommitted changes reach an isolated checkout. Do not wire in modules before they exist; coordinate dependency handoffs before dependent work starts.

Do not copy the entire conversation into child context. For native Codex children, use `fork_turns="none"` and an appropriate available agent profile. Children must not delegate unless the user authorizes it.

## Acceptance and review

Inspect results and evidence against the acceptance criteria. For code changes, inspect the diff and its scope. Use worker checks when they cover the accepted changes. Request additional verification only for integration changes, missing evidence, failures, or a concrete concern. Delegate those checks unless they meet the trivial-task exception.

In full mode, the reviewer examines the actual result and evidence against the requirements. It remains read-only and reports concrete bugs, regressions, and missing safeguards, or accepts the result. It does not implement fixes.

Assess findings against source and evidence. Have a worker fix valid findings and record a reason for rejecting others. Request a new review task after corrections, including the requirements, prior findings, fixes, and unresolved objections. An old approval does not cover changed code.

Distinguish completed work, worker verification, independent review, and remaining gaps. Do not expand the authorized scope.

## Questions, failures, and stopping

Answer child questions from existing requirements when possible. Ask the user when a decision changes scope, behavior, or authority.

Before retrying a failed child, inspect partial changes and confirm the previous task is no longer active. Allow one fresh retry for a transient provider failure. If it fails again, report the blocker and ask how to proceed. Never silently switch models or enter a retry loop.

Track active children. On a stop request, cancel them and stop further work. Distinguish a cancellation request from confirmed termination.

Finish with a concise account of results, verification and who performed it, and remaining gaps. Do not claim success while required work remains. End with the continuity signature.
