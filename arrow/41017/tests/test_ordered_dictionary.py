"""
Test for apache/arrow#41017: pa.array() drops ordered flag on DictionaryType.

This test requires building pyarrow from the patched Arrow C++ source.
It documents the expected behavior after the fix.
"""
import pyarrow as pa


def test_pa_array_preserves_ordered_flag():
    """pa.array() should preserve the ordered flag from DictionaryType."""
    dict_type = pa.dictionary(pa.int8(), pa.string(), ordered=True)
    result = pa.array(["a", "b", "a"], type=dict_type)
    assert result.type.ordered is True, (
        f"Expected ordered=True, got ordered={result.type.ordered}"
    )


def test_pa_array_unordered_stays_unordered():
    """pa.array() with ordered=False should remain unordered."""
    dict_type = pa.dictionary(pa.int8(), pa.string(), ordered=False)
    result = pa.array(["a", "b", "a"], type=dict_type)
    assert result.type.ordered is False


def test_pa_array_ordered_with_various_value_types():
    """ordered flag should be preserved for all value types."""
    for value_type in [pa.string(), pa.int64(), pa.float64(), pa.binary()]:
        dict_type = pa.dictionary(pa.int8(), value_type, ordered=True)
        data = {
            pa.string(): ["a", "b", "a"],
            pa.int64(): [1, 2, 1],
            pa.float64(): [1.0, 2.0, 1.0],
            pa.binary(): [b"a", b"b", b"a"],
        }[value_type]
        result = pa.array(data, type=dict_type)
        assert result.type.ordered is True, (
            f"ordered flag lost for value_type={value_type}"
        )


def test_dictionary_builder_preserves_ordered():
    """DictionaryArray built from builder should preserve ordered flag."""
    dict_type = pa.dictionary(pa.int8(), pa.string(), ordered=True)
    builder = pa.DictionaryArray.from_arrays(
        pa.array([0, 1, 0], type=pa.int8()),
        pa.array(["a", "b"], type=pa.string()),
        ordered=True,
    )
    assert builder.type.ordered is True


def test_pandas_series_with_arrow_ordered_dict():
    """Regression test for pandas#58152."""
    try:
        import pandas as pd
    except ImportError:
        return  # skip if pandas not available

    dict_type = pa.dictionary(pa.int8(), pa.string(), ordered=True)
    arrow_dtype = pd.ArrowDtype(dict_type)
    series = pd.Series(["a", "b", "a"], dtype=arrow_dtype)
    pa_type = series.array._pa_array.type
    assert pa_type.ordered is True, (
        f"pandas Series lost ordered flag: {pa_type}"
    )


if __name__ == "__main__":
    print("NOTE: Tests 1-3 will FAIL on unpatched pyarrow (bug #41017)")
    print("      Tests 4-5 should pass even without the patch")
    print()

    tests = [
        test_pa_array_preserves_ordered_flag,
        test_pa_array_unordered_stays_unordered,
        test_pa_array_ordered_with_various_value_types,
        test_dictionary_builder_preserves_ordered,
        test_pandas_series_with_arrow_ordered_dict,
    ]

    for test in tests:
        try:
            test()
            print(f"  PASS: {test.__name__}")
        except AssertionError as e:
            print(f"  FAIL: {test.__name__}: {e}")
        except Exception as e:
            print(f"  ERROR: {test.__name__}: {e}")
