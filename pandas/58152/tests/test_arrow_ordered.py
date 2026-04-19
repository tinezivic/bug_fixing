"""
PR-ready test for pandas #58152
BUG: pyarrow dictionary type ordered argument not respected

This test should be added to pandas/tests/extension/test_arrow.py

The bug was caused by pa.array() dropping the ordered flag for dictionary types
(upstream: https://github.com/apache/arrow/issues/41017). pandas works around
this in _box_pa_array by detecting the type mismatch and casting back to the
requested type.
"""

import numpy as np
import pytest

import pyarrow as pa

import pandas as pd
from pandas import ArrowDtype, Series
import pandas._testing as tm
from pandas.arrays import ArrowExtensionArray


def test_dictionary_ordered_preserved():
    # GH#58152 - ordered flag should be preserved for dictionary types
    dicttyp = pa.dictionary(pa.int8(), pa.string(), ordered=True)
    result = Series(["foo", "bar", "foo"], dtype=ArrowDtype(dicttyp))

    assert result.dtype.pyarrow_dtype.ordered is True
    assert result.array._pa_array.type.ordered is True


def test_dictionary_ordered_preserved_with_nulls():
    # GH#58152
    dicttyp = pa.dictionary(pa.int8(), pa.string(), ordered=True)
    result = Series(["foo", None, "bar"], dtype=ArrowDtype(dicttyp))

    assert result.dtype.pyarrow_dtype.ordered is True
    assert result.array._pa_array.type.ordered is True


def test_dictionary_ordered_preserved_empty():
    # GH#58152
    dicttyp = pa.dictionary(pa.int8(), pa.string(), ordered=True)
    result = Series([], dtype=ArrowDtype(dicttyp))

    assert result.dtype.pyarrow_dtype.ordered is True


def test_dictionary_ordered_preserved_operations():
    # GH#58152 - ordered should survive common operations
    dicttyp = pa.dictionary(pa.int8(), pa.string(), ordered=True)
    ser = Series(["foo", "bar", "foo"], dtype=ArrowDtype(dicttyp))

    # copy
    assert ser.copy().dtype.pyarrow_dtype.ordered is True

    # slice
    assert ser[0:2].dtype.pyarrow_dtype.ordered is True

    # concat
    assert pd.concat([ser, ser]).dtype.pyarrow_dtype.ordered is True

    # unique
    assert ser.unique().dtype.pyarrow_dtype.ordered is True


def test_dictionary_unordered_not_affected():
    # GH#58152 - ensure unordered dictionaries still work correctly
    dicttyp = pa.dictionary(pa.int8(), pa.string(), ordered=False)
    result = Series(["foo", "bar", "foo"], dtype=ArrowDtype(dicttyp))

    assert result.dtype.pyarrow_dtype.ordered is False
