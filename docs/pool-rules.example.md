# Pool rules (example)

This is the generic placeholder companion to `adapters/pools.example.json`,
referenced by `workflows/*.states.json` (`runtime.pool_map` and `runtime.pool_doc`).
Replace every `[ADD_*]` placeholder with your own setup. No keys, no real account
ids, no personal data.

## What a pool is

A pool groups **providers by subscription**. The subscription, not the provider
app and not the gateway route, is the unit of quota, rate limits, weekly caps,
and failover. `pool_id` values must match the enum in
`contracts/ledger_event.schema.json` (`pool-a` through `pool-e`, `pool-payg`,
`pool-local`, `pool-unknown`).

## Critical owner rule

**A host-native app and a gateway mirror of the same subscription are ONE pool.**

Example: provider X reachable both from the host-native CLI (`host_native`) and
through your LLM gateway (`[ADD_LLM_GATEWAY]`) still has one shared cap. A
"failover" that moves a worker from the host-native route to the gateway route
of the same subscription does not free capacity; it just burns the same cap
twice. Failover must change the `subscription_pool`, which in code means the
ledger `failover.from_pool` and `failover.to_pool` must differ, and neither may
be two routes of one subscription.

## Other rules kept in this pack

- Builder and critic in a gauntlet round may not run on the same pool
  (`builder_critic_same_lab` is an illegal transition).
- PAYG hops can require a one-time owner OK first (`flags/payg_confirm.on`).
- When a pool is exhausted (429 / cap), the workflow goes to `SUB_DEAD` and asks
  the owner; it never silently dies or quietly downgrades the model.
