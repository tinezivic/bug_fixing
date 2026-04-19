# pandas #58152 — BUG: pyarrow dictionary type ordered argument not respected

## Issue

- **pandas**: https://github.com/pandas-dev/pandas/issues/58152
- **upstream pyarrow**: https://github.com/apache/arrow/issues/41017

## Summary

When creating a `pd.Series` with a pyarrow ordered dictionary type (`ordered=True`),
the `ordered` flag was being lost because `pa.array()` drops the `ordered` attribute
(upstream pyarrow bug).

## Status

The main user-facing bug is **already fixed** in pandas 3.0.2 via an existing workaround
in `_box_pa_array` — the type mismatch is detected and `cast(pa_type)` restores `ordered`.

However:
1. **No regression test exists** — this fix could regress silently
2. **No comment references #58152** in the workaround code
3. **Edge case**: Direct `ArrowExtensionArray(pa.array(..., type=dicttyp))` still loses
   ordered because it bypasses `_box_pa_array`

## Contribution

This project prepares a PR-ready contribution:
- Regression test for #58152
- Comment in source code referencing the issue
- Edge case fix for direct ArrowExtensionArray construction

## Structure

```
├── analysis/
│   └── bug_analysis.py          # Detailed investigation script
├── fix/
│   ├── array.py.patch           # Patch for pandas/core/arrays/arrow/array.py
│   └── apply_fix.sh             # Script to apply the fix to a pandas checkout
├── tests/
│   ├── test_reproducer.py       # Standalone reproducer (run independently)
│   └── test_arrow_ordered.py    # PR-ready test for pandas test suite
└── README.md
```
