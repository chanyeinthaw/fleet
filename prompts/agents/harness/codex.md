# Harness

- When spawning Codex subagents, always pass `fork_turns="none"` and include all required context in the subagent prompt.
- When you spawn subagents, use available subagent profiles instead of spawning a default subagent.
- When you use `unslop` skill, do not mention to me like this "I’m applying the required `unslop` skill so the answer stays direct.", just use it silently.
