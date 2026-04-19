"""
Tests for GH#58153: sort_values() with key not working on categorical column.

The bug was that when sort_values(key=...) was used on a categorical column,
the key function's result (from .map()) retained categorical dtype with
categories in the original positional order, causing sorting by category codes
rather than by the mapped values.

Root cause: Categorical.map() for unordered categoricals preserved the original
category ordering. Fix: sort the mapped categories and remap codes for unordered
categoricals in Categorical.map().
"""

import numpy as np
import pytest

import pandas as pd
from pandas import (
    Categorical,
    DataFrame,
    Series,
)
import pandas._testing as tm


class TestSortValuesCategoricalKey:
    """Tests for sort_values with key parameter on categorical columns."""

    def test_sort_values_key_categorical_map(self):
        """GH#58153 - Original reproducer: sort by custom dict on categorical col."""
        df = DataFrame(
            [[1, 2, "March"], [5, 6, "Dec"], [3, 4, "April"]],
            columns=["a", "b", "month"],
        )
        df["month"] = df["month"].astype("category")
        custom_dict = {"March": 0, "April": 1, "Dec": 3}

        result = df.sort_values(by=["month"], key=lambda x: x.map(custom_dict))
        expected = df.iloc[[0, 2, 1]]
        tm.assert_frame_equal(result, expected)

    def test_sort_values_key_categorical_map_descending(self):
        """GH#58153 - Descending sort with key on categorical column."""
        df = DataFrame(
            {"month": Categorical(["March", "Dec", "April"])}
        )
        custom_dict = {"March": 0, "April": 1, "Dec": 3}

        result = df.sort_values(
            by="month", key=lambda x: x.map(custom_dict), ascending=False
        )
        expected = df.iloc[[1, 2, 0]]
        tm.assert_frame_equal(result, expected)

    def test_sort_values_key_categorical_map_with_nan(self):
        """GH#58153 - Key on categorical column with NaN values."""
        df = DataFrame(
            {"month": Categorical(["March", "Dec", "April", None])}
        )
        custom_dict = {"March": 0, "April": 1, "Dec": 3}

        result = df.sort_values(by="month", key=lambda x: x.map(custom_dict))
        expected = df.iloc[[0, 2, 1, 3]]
        tm.assert_frame_equal(result, expected)

    def test_sort_values_key_categorical_map_na_first(self):
        """GH#58153 - Key on categorical column, NaN first."""
        df = DataFrame(
            {"month": Categorical(["March", "Dec", "April", None])}
        )
        custom_dict = {"March": 0, "April": 1, "Dec": 3}

        result = df.sort_values(
            by="month", key=lambda x: x.map(custom_dict), na_position="first"
        )
        expected = df.iloc[[3, 0, 2, 1]]
        tm.assert_frame_equal(result, expected)

    def test_series_sort_values_key_categorical_map(self):
        """GH#58153 - Series.sort_values with key on categorical."""
        s = Series(["March", "Dec", "April"], dtype="category")
        custom_dict = {"March": 0, "April": 1, "Dec": 3}

        result = s.sort_values(key=lambda x: x.map(custom_dict))
        expected = s.iloc[[0, 2, 1]]
        tm.assert_series_equal(result, expected)

    def test_sort_values_key_categorical_map_multicolumn(self):
        """GH#58153 - Multi-column sort with key on categorical column."""
        df = DataFrame(
            {"a": [1, 1, 1], "month": Categorical(["March", "Dec", "April"])}
        )
        custom_dict = {"March": 0, "April": 1, "Dec": 3}

        result = df.sort_values(
            by=["a", "month"],
            key=lambda x: x.map(custom_dict) if x.name == "month" else x,
        )
        expected = df.iloc[[0, 2, 1]]
        tm.assert_frame_equal(result, expected)

    def test_sort_values_key_categorical_map_string_values(self):
        """GH#58153 - Key maps categorical to strings."""
        s = Series(["b", "c", "a"], dtype="category")

        result = s.sort_values(
            key=lambda x: x.map({"a": "z", "b": "y", "c": "x"})
        )
        expected = s.iloc[[1, 0, 2]]  # x, y, z → c, b, a
        tm.assert_series_equal(result, expected)


class TestCategoricalMapCategoryOrder:
    """Tests that Categorical.map() produces sorted categories for unordered."""

    def test_map_unordered_sorts_categories(self):
        """GH#58153 - Unordered categorical map should sort new categories."""
        cat = Categorical(["March", "Dec", "April"])
        mapped = cat.map({"March": 0, "April": 1, "Dec": 3})

        assert mapped.tolist() == [0, 3, 1]
        assert mapped.categories.tolist() == [0, 1, 3]  # sorted
        assert not mapped.ordered

    def test_map_ordered_preserves_category_order(self):
        """GH#58153 - Ordered categorical map should preserve category order."""
        cat = Categorical(
            ["March", "Dec", "April"],
            categories=["March", "Dec", "April"],
            ordered=True,
        )
        mapped = cat.map({"March": 0, "April": 1, "Dec": 3})

        assert mapped.tolist() == [0, 3, 1]
        assert mapped.categories.tolist() == [0, 3, 1]  # order preserved
        assert mapped.ordered

    def test_map_unordered_with_nan(self):
        """GH#58153 - Unordered categorical map with NaN."""
        cat = Categorical(["March", None, "Dec", "April"])
        mapped = cat.map({"March": 0, "April": 1, "Dec": 3})

        assert mapped[0] == 0
        assert mapped[2] == 3
        assert mapped[3] == 1
        assert np.isnan(mapped[1])
        assert mapped.categories.tolist() == [0, 1, 3]  # sorted
