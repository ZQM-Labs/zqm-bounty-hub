# ZQM Bounty Hub — Integration Patterns Reference

## Orchestrator wiring
- Entry: `ZQM-BountyHub-Orchestrator/orchestrator.py`
- Adapters: `ZQM-BountyHub-Orchestrator/adapters/<platform>_adapter.py`
- Runtime: `zqm_parallel_runner`, `zqm_gpu_accelerator`
- Evidence: `OUTPUT_ROOT/evidence/<run_id>_<task_id>_raw.json`
- Manifest: `OUTPUT_ROOT/<run_id>_<platform>_manifest.json`

## Adapter contract
```python
def run(target_id: str, check_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    ...
```

## Key lessons
- Use env vars for auth: `HACKERONE_API_TOKEN`, `BUGCROWD_API_KEY`, `INTIGRITI_API_KEY`
- `detect_device` should return a single best device, not a list, for manifest metadata
- Parallel execution: ThreadPoolExecutor for I/O-bound adapter runs, ProcessPoolExecutor for CPU-bound
- GPU detection falls back to CPU automatically; manifest should record `fallback_used`
- Task expansion: `check.target_ids[]` should resolve against payload `targets[]` deterministically
- Evidence write must happen after adapter.run(), not deferred
- Orchestrator must import `zqm_parallel_runner` directly, not `zqm_gpu_accelerator.skill`

## Dogfood sequence
1. Write payload with distinct target_ids per platform
2. Run orchestrator with `--engine thread --workers 2`
3. Inspect `.out*/<platform>_manifest.json` for result_count and result_hash
4. Inspect `.out*/evidence/*` for per-task status
5. Patch adapter if status != expected
