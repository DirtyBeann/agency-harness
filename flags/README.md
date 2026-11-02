# Harness runtime flags

Drop (or remove) small marker files here. Orchestrators / loop runners must check these **every round**.

| File | Default | When present |
|---|---|---|
| `PAUSE` | **absent** (running) | Loop must stop between rounds and wait until file is deleted |
| `payg_confirm.on` | **absent** (off) | Before first hop to `pool-payg-*`, ask owner once per run |

## How to pause a long loop
```bat
echo. > flags\PAUSE
```
Resume:
```bat
del flags\PAUSE
```

## How to enable soft PAYG confirm
```bat
echo. > flags\payg_confirm.on
```
Disable (default):
```bat
del flags\payg_confirm.on
```

## How to disable Governor
- host: set `agent.governor.disable` to `true` in `host-agent-config` (or remove from picker / don't invoke)
- Per run: pass `governor: false` / skip GOV_REVIEW when `max_rounds < 10` or owner says off
- Nuclear: rename/disable the agent like orchestrator

Never commit secrets into this folder. Marker files only.

## PAYG priority

Hard PAYG refuse is **off** by default in this pack. Soft confirm via payg_confirm.on only.

When hopping to PAYG after sub death, prefer **DeepSeek** then **Z.AI/GLM**. Other vendors: operator console overage limits. See docs/payg-priority.md.