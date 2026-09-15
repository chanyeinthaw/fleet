# Harness

- Pi does not support subagents. If a skill or other instruction asks for subagent work, do it directly in the current session.
- Executor is code-mode MCP and API integration layer. It is not a subagent tooling. Use it to discover and invoke configured integrations and their tools when those integrations are relevant to the task.
