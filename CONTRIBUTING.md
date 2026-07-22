# Contributing

Pull requests should preserve the research and disclosure contracts.

1. Describe the economic hypothesis, expected behavior, and conditions that
   would contradict it.
2. Freeze direction, timing, sample splits, costs, and selection gates before
   inspecting evaluation results.
3. Keep public code formula-agnostic and use precomputed oriented scores.
4. Add focused tests for timing, exposure, turnover, costs, and PnL identities.
5. Use synthetic or explicitly public data in examples.
6. Report mixed, null, and sensitivity results alongside improvements.
7. Do not commit proprietary data, exact private formulas, holdings, strategy
   factories, or local filesystem paths.

Review a change with:

```bash
git diff --check
git diff --cached --name-status
git grep -n "$HOME"
python -m pytest -q tests/test_sample_package.py
python examples/run_sample_package.py
python examples/render_public_results.py
```

The test suite includes an AST-based dependency-boundary check for the public
sample package.
