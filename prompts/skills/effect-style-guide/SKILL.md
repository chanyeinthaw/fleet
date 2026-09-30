---
name: effect-style-guide
description: My coding conventions for Effect. Use when writing or reviewing Effect code.
metadata:
  harness: [pi, codex, claude]
---

# Effect style guide

Use `Effect.gen` and `yield*` for business logic, and `.pipe` for composition and simple transforms. Use both styles together; each has its place.

```ts
Effect.gen(function* () {
  // business logic lives here
}).pipe(
  // composition happens here
)
```

## Multi-step operations

Use `Effect.gen` for sequential operations.

```ts
const createUser = (userData) =>
  Effect.gen(function* () {
    const db = yield* Database
    const validated = yield* validateUserData(userData)
    const hashed = yield* hashPassword(validated.password)
    const user = yield* db.users.create({ ...validated, password: hashed })
    return yield* enrichUserData(user)
  })
```

## Conditional logic

Use ordinary conditional logic inside `Effect.gen`. Avoid walls of `Effect.map`, `Effect.andThen`, or `Effect.flatMap` chains for business branches.

```ts
const processPayment = (payment) =>
  Effect.gen(function* () {
    const config = yield* Config

    if (payment.amount > config.largePaymentThreshold) {
      return yield* processLargePayment(payment)
    }

    return yield* processStandardPayment(payment)
  })
```

## Layer composition

Use `.pipe` to compose dependency layers.

```ts
const appLayer = Layer.empty.pipe(
  Layer.provide(Database.Layer),
  Layer.provide(Logger.Layer),
  Layer.provideMerge(Metrics.Layer),
  Layer.provideMerge(Cache.Layer),
)
```

## Simple transforms

Simple transforms do not need their own generators. A small pipe can also sit inside a generator.

```ts
const usernames = yield* getActiveUsers().pipe(
  Effect.map((users) => users.map((u) => u.username)),
)
```

## Combine both styles

Keep business logic inside the generator and cross-cutting concerns outside in `.pipe`.

```ts
const fetchUserPosts = (userId) =>
  Effect.gen(function* () {
    const db = yield* Database
    const cache = yield* Cache

    const cached = yield* cache.get(`posts:${userId}`)
    if (cached) return cached

    const posts = yield* db.posts.findByUser(userId)
    yield* cache.set(`posts:${userId}`, posts)

    return posts
  }).pipe(
    Effect.withSpan("fetch_user_posts"),
    Effect.retry(retryPolicy),
    Effect.catchTag("DatabaseError", () => Effect.succeed([])),
  )
```

## Decision matrix

| Task | Style |
| --- | --- |
| Injecting/retrieving dependencies | `Effect.gen` |
| Conditional logic | `Effect.gen` |
| Sequential operations | `Effect.gen` |
| Error handling | `.pipe` |
| Adding tracing | `.pipe` |
| Layer building | `.pipe` |
| Simple transforms | `.pipe` |

## Avoid pipe chains for sequential logic

Avoid this shape for a multi-step business workflow:

```ts
Effect.succeed(order).pipe(
  Effect.andThen(validateOrder),
  Effect.andThen(calculateTotals),
  Effect.andThen(applyDiscounts),
  Effect.andThen(processPayment),
  Effect.andThen(sendConfirmation),
)
```

Write the steps in a generator instead:

```ts
Effect.gen(function* () {
  const validated = yield* validateOrder(order)
  const withTotals = yield* calculateTotals(validated)
  const discounted = yield* applyDiscounts(withTotals)
  const payment = yield* processPayment(discounted)
  return yield* sendConfirmation(payment)
})
```
