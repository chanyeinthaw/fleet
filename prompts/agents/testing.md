# Testing

- Tautological tests are considered harmful.
- Do not perform automated-browser testing unless explicitly asked.
- New test files are opt-in. Do not create unit, integration, end-to-end, or spec files, or new test-only helpers/fixtures, unless the user explicitly requests their creation or approves it first. A request to implement, fix, test, or verify something does not by itself authorize new test files. Assume no by default; ask only when creating them has a concrete benefit, not as a routine step.
- Prefer running existing tests and direct browser(if opt-in)/runtime checks without adding test files. When test changes are in scope, exercise observable behavior rather than asserting source-code strings, implementation shapes, or that tests exist.
