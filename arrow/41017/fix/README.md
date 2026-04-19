# Apache Arrow #41017 — Fix: DictionaryBuilder drops `ordered` flag

## Root Cause

`DictionaryBuilderBase<BuilderType, T>::type()` in `builder_dict.h` calls:
```cpp
return ::arrow::dictionary(indices_builder_.type(), value_type_);
```
The `ordered` parameter defaults to `false`. The builder never stores or
propagates the `ordered` flag from the original `DictionaryType`.

## Fix (2 files, +23 −7 lines)

### `cpp/src/arrow/array/builder_dict.h`

1. Add `bool ordered_ = false;` member variable
2. Add `void set_ordered(bool ordered)` setter
3. Pass `ordered_` to `::arrow::dictionary()` in `type()`:
   ```cpp
   return ::arrow::dictionary(indices_builder_.type(), value_type_, ordered_);
   ```

### `cpp/src/arrow/builder.cc`

1. Add `bool ordered;` field to `DictionaryBuilderCase` struct
2. In `CreateFor<ValueType>()`, call `builder->set_ordered(ordered)` after
   construction (for all 3 builder creation paths)
3. Pass `dict_type.ordered()` when constructing `DictionaryBuilderCase` in:
   - `MakeBuilderImpl::Visit(const DictionaryType&)`
   - `MakeDictionaryBuilder()`

## Call Chain (how ordered gets from Python to C++ and back)

```
pa.array(["a","b"], type=dict(int8,string,ordered=True))
  → _sequence_to_array()  [array.pxi]
    → ConvertPySequence()  [python_to_arrow.cc]
      → DictionaryConverter::Init()  [converter.h]
        → MakeDictionaryBuilder(pool, type, ...)  [builder.cc]
          → DictionaryBuilderCase{..., ordered=True}.Make()
            → CreateFor<StringType>()
              → new DictionaryBuilder<StringType>(...)
              → builder->set_ordered(true)        ← NEW
      → DictionaryConverter::Append(values)
        → builder.Append(...)
      → builder.FinishInternal()                  [builder_dict.h]
        → (*out)->type = type()
          → dictionary(int8, string, ordered=true) ← FIXED
```

## Patch

See `ordered_dictionary_builder.patch`
