"""
Standalone reproducer for pandas #58152
BUG: pyarrow dictionary type ordered argument not respected

Run: python test_reproducer.py
"""

import sys

import pyarrow as pa
import pandas as pd


def test_ordered_dictionary_series_creation():
    """Original reproducer from the issue."""
    dicttyp = pa.dictionary(pa.int8(), pa.string(), ordered=True)
    assert dicttyp.ordered, "pyarrow type should be ordered"

    s = pd.Series(["foo", "bar", "foo"], dtype=pd.ArrowDtype(dicttyp))

    # The bug: dtype showed ordered=0 instead of ordered=1
    assert s.dtype.pyarrow_dtype.ordered, (
        f"Series dtype should preserve ordered=True, "
        f"got dtype: {s.dtype}"
    )
    # Also check the underlying chunked array
    assert s.array._pa_array.type.ordered, (
        "Underlying ChunkedArray should have ordered=True"
    )


def test_ordered_dictionary_with_nulls():
    dicttyp = pa.dictionary(pa.int8(), pa.string(), ordered=True)
    s = pd.Series(["foo", None, "bar"], dtype=pd.ArrowDtype(dicttyp))
    assert s.dtype.pyarrow_dtype.ordered
    assert s.array._pa_array.type.ordered


def test_ordered_dictionary_empty():
    dicttyp = pa.dictionary(pa.int8(), pa.string(), ordered=True)
    s = pd.Series([], dtype=pd.ArrowDtype(dicttyp))
    assert s.dtype.pyarrow_dtype.ordered


def test_ordered_dictionary_operations_preserve():
    dicttyp = pa.dictionary(pa.int8(), pa.string(), ordered=True)
    s = pd.Series(["foo", "bar", "foo"], dtype=pd.ArrowDtype(dicttyp))

    # copy
    assert s.copy().dtype.pyarrow_dtype.ordered

    # slice
    assert s[0:2].dtype.pyarrow_dtype.ordered

    # concat
    assert pd.concat([s, s]).dtype.pyarrow_dtype.ordered

    # unique
    assert s.unique().dtype.pyarrow_dtype.ordered


def test_ordered_dictionary_int_values():
    """Test with non-string value type."""
    dicttyp = pa.dictionary(pa.int8(), pa.int64(), ordered=True)
    s = pd.Series([1, 2, 1, 3], dtype=pd.ArrowDtype(dicttyp))
    assert s.dtype.pyarrow_dtype.ordered
    assert s.array._pa_array.type.ordered


if __name__ == "__main__":
    tests = [
        test_ordered_dictionary_series_creation,
        test_ordered_dictionary_with_nulls,
        test_ordered_dictionary_empty,
        test_ordered_dictionary_operations_preserve,
        test_ordered_dictionary_int_values,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  PASS: {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {test.__name__}: {e}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
