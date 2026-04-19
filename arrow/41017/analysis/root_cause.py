"""
Root Cause Analysis for apache/arrow#41017
pa.array() constructor does not retain ordered attribute for dictionary type

## Bug Location

File: cpp/src/arrow/array/builder_dict.h
Class: DictionaryBuilderBase<BuilderType, T>

## Root Cause

The `type()` method reconstructs the DictionaryType without the `ordered` flag:

    std::shared_ptr<DataType> type() const override {
        return ::arrow::dictionary(indices_builder_.type(), value_type_);
        //     ^^^^ ordered defaults to false!
    }

And `FinishInternal()` uses `type()` to set the output array's type:

    (*out)->type = type();

The builder has no `ordered_` member variable, so even though the caller
created it with a DictionaryType that has ordered=true, the builder doesn't
store or propagate that information.

## Fix

In `DictionaryBuilderBase`:
1. Add `bool ordered_ = false;` member variable
2. In Init methods, extract ordered from the type if it's DictionaryType
3. In `type()`, pass `ordered_` as third argument:
   `return ::arrow::dictionary(indices_builder_.type(), value_type_, ordered_);`

## Affected Code Path

1. Python: `pa.array(["foo", "bar"], type=pa.dictionary(pa.int8(), pa.string(), ordered=True))`
2. Cython: `_sequence_to_array()` → `ConvertPySequence()`
3. C++: `MakeConverter()` → creates `DictionaryConverter`
4. C++: `DictionaryConverter::Init()` → `MakeDictionaryBuilder(pool, type, ...)`
5. C++: Builder builds array → `FinishInternal()` → `type()` → ordered lost!

## Why DictionaryArray.from_arrays() works

`from_arrays()` takes `ordered` as an explicit parameter and constructs
the DictionaryType directly, bypassing the builder entirely.
"""

import pyarrow as pa

print(f"pyarrow: {pa.__version__}")
print()

# The bug
dicttyp = pa.dictionary(pa.int8(), pa.string(), ordered=True)
arr = pa.array(["foo", "bar", "foo"], type=dicttyp)
print(f"pa.array() ordered: {arr.type.ordered}")  # False — BUG

# The workaround that works
indices = pa.array([0, 1, 0], type=pa.int8())
dictionary = pa.array(["foo", "bar"])
arr2 = pa.DictionaryArray.from_arrays(indices, dictionary, ordered=True)
print(f"from_arrays() ordered: {arr2.type.ordered}")  # True — works

# cast() works too
arr3 = arr.cast(dicttyp)
print(f"cast() ordered: {arr3.type.ordered}")  # True — works
