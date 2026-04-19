"""
Bug Analysis for pandas #58152
pyarrow dictionary type ordered argument not respected

This script traces the exact code path to understand the bug and its workaround.
"""

import pyarrow as pa
import pandas as pd

print(f"pandas: {pd.__version__}")
print(f"pyarrow: {pa.__version__}")
print()

# =============================================================================
# 1. The upstream pyarrow bug (apache/arrow#41017)
# =============================================================================
print("=" * 70)
print("1. UPSTREAM PYARROW BUG (apache/arrow#41017)")
print("=" * 70)

dicttyp = pa.dictionary(pa.int8(), pa.string(), ordered=True)
print(f"   Original type ordered: {dicttyp.ordered}")  # True

arr = pa.array(["foo", "bar", "foo"], dicttyp)
print(f"   pa.array() result ordered: {arr.type.ordered}")  # False — BUG
print(f"   → pa.array() drops the ordered flag!")
print()

# =============================================================================
# 2. How pandas works around it (in _box_pa_array)
# =============================================================================
print("=" * 70)
print("2. PANDAS WORKAROUND (in _box_pa_array)")
print("=" * 70)

# When pd.Series(..., dtype=ArrowDtype(dicttyp)) is called:
# 1. _from_sequence calls _box_pa_array with pa_type=dicttyp
# 2. pa.array(value, type=pa_type) creates array with ordered=0 (pyarrow bug)
# 3. Check: pa_array.type != pa_type → True (ordered mismatch)
# 4. dictionary_encode() → re-encodes (still ordered=0)
# 5. cast(pa_type) → restores ordered=1

s = pd.Series(["foo", "bar", "foo"], dtype=pd.ArrowDtype(dicttyp))
print(f"   pd.Series dtype: {s.dtype}")
print(f"   Underlying ordered: {s.array._pa_array.type.ordered}")  # True — FIXED
print(f"   → Workaround works via type mismatch detection + cast()")
print()

# =============================================================================
# 3. Edge case: Direct ArrowExtensionArray construction
# =============================================================================
print("=" * 70)
print("3. EDGE CASE: Direct ArrowExtensionArray(pa.array(...))")
print("=" * 70)

bad_arr = pa.array(["foo", "bar", "foo"], dicttyp)
print(f"   pa.array ordered: {bad_arr.type.ordered}")  # False

s_direct = pd.Series(pd.arrays.ArrowExtensionArray(bad_arr))
print(f"   Direct construction ordered: {s_direct.dtype.pyarrow_dtype.ordered}")  # False
print(f"   → Edge case: __init__ takes array as-is, no workaround applied")
print()

# =============================================================================
# 4. Operations preservation test
# =============================================================================
print("=" * 70)
print("4. OPERATIONS THAT PRESERVE ORDERED")
print("=" * 70)

s = pd.Series(["foo", "bar", "foo"], dtype=pd.ArrowDtype(dicttyp))
print(f"   copy(): {s.copy().dtype.pyarrow_dtype.ordered}")
print(f"   concat(): {pd.concat([s, s]).dtype.pyarrow_dtype.ordered}")
print(f"   slice [0:2]: {s[0:2].dtype.pyarrow_dtype.ordered}")
print(f"   unique(): {s.unique().dtype.pyarrow_dtype.ordered}")
print(f"   with None: {pd.Series(['a', None, 'b'], dtype=pd.ArrowDtype(dicttyp)).dtype.pyarrow_dtype.ordered}")
print(f"   empty: {pd.Series([], dtype=pd.ArrowDtype(dicttyp)).dtype.pyarrow_dtype.ordered}")
print()
print("CONCLUSION: Main path is fixed. Regression test needed.")
