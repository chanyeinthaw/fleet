# Harness

- Pi does not support subagents natively. If a skill or other instruction asks for subagent work, do it directly in the current session unless you are operating in T3 Code. In T3Code you can use `orchestrator_capabilities` to figure out subagent and thread capabilities.
- Executor is code-mode MCP and API integration layer. It is not a subagent tooling. When it is available, use it to discover and invoke configured integrations and their tools when those integrations are relevant to the task.
