# 08 — Intent Model B doc (deferred build)

## Goal
Design-only: allow v2 solver network without rewriting v1 core.

## Outputs
- `docs/intent-model-B.md` covering: EIP-712 intent struct, settlement contracts (Eth + Base escrow), Dutch-auction filler selection, collateral/slashing, reorg/finality handling, how v1 `find_best_path`/`find_split` becomes the auction reserve-price oracle, `DirectExecutor -> IntentExecutor` migration, and v2 scope: HyperEVM chain + `(hyper:HYPE)` / WHYPE bridge edges.
- Sequence diagram (mermaid) intent lifecycle: sign -> auction -> fill on dest -> prove on source -> settle/slash.
- Explicit non-goals: no filler implementation in v1.

## Acceptance
- Doc merged; v1 `api.py`/`pathfinder.py` signatures require no breaking change to adopt B later (review checklist in doc).
