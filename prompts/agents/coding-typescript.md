# Coding preferences - Typescript focused

- `any` is the enemy. Inferred types are our friend. Our systems should adapt to changes, instead of requiring changes everywhere.
- If your TS code looks like a Python dev wrote it, it is bad TS code.
- Avoid one-line functions that re just casting wrappers.
- Write TypeScript in ways that Matt Pocock would be proud of.
- If not already specified in project, I generally like to use the following tech: Next.js, Tailwind, React, Vite, pnpm and Effect.
- When building more complex web and react native apps, I like to pull in xstate (alpha), [effect-machine](https://github.com/typeonce-dev/effect-machine) (xstate in effect), Tanstack/React Query, better-auth, [better-upload](https://better-upload.com/) and Effect Schema (or zod)
- Effect should be the default consideration fojr our systems.
