# pandas #58152 — ArrowDtype dictionary ordered flag

## Bug v enem stavku

`pd.Series(["a", "b"], dtype=ArrowDtype(dictionary(int8, string, ordered=True)))`
izgubi `ordered=True` — Series ima `ordered=False`.

## Zakaj se to zgodi

Pandas interno kliče `pa.array(data, type=dict_type)` za konverzijo Python
podatkov v Arrow array. PyArrow-jev `pa.array()` gre skozi C++ DictionaryBuilder,
ki ima bug — `DictionaryBuilderBase::type()` ne posreduje `ordered` flaga
naprej (vedno vrne `ordered=False`). To je Apache Arrow bug #41017.

## Kako pandas to workaround-a (od v2.2+)

V `pandas/core/arrays/arrow/array.py`, metoda `_box_pa_array()`:

```python
if pa_type is not None and data.type != pa_type:
    data = data.cast(pa_type)
```

Po `pa.array()` klicu pandas preveri ali se tip ujema z zahtevanim. Ker
`ordered` ne preživeli, se tipa NE ujemata → pandas naredi `cast(pa_type)`,
ki **obnovi** `ordered=True`. Workaround deluje, ampak je neučinkovit (cast
ki ne bi bil potreben).

## Kaj smo naredili

- **Analiza**: potrdili bug, identificirali workaround v pandas kodi
- **Testi**: 5 regression testov ki preverjajo da workaround drži:
  - `test_basic_ordered` — osnovna funkcionalnost
  - `test_unordered_default` — ordered=False mora ostati False
  - `test_roundtrip_ordered` — konverzija pandas→arrow→pandas ohrani ordered
  - `test_various_value_types` — deluje za string, int, float, binary
  - `test_comparison_operators` — ordered dictionary podpira >, <, >=, <=

## Kaj pomeni "ordered" dictionary

Dictionary type v Arrow je kot "categorical" v pandas. `ordered=True` pomeni
da imajo kategorije naraven vrstni red (npr. "low" < "medium" < "high") in
omogoča primerjalne operatorje. `ordered=False` pomeni da so kategorije
samo labeli brez vrstnega reda (npr. barve: "red", "blue", "green").

## Kje leži pravi bug

Pravi bug je v Apache Arrow C++ — glej `arrow/41017/NOTES.md`.
Pandas samo obide bug z workaroundom.

## Datoteke

- `analysis/bug_analysis.py` — skripta ki reproducira bug in pokaže workaround
- `tests/test_reproducer.py` — standalone reproducer
- `tests/test_arrow_ordered.py` — pytest regression testi (5/5 pass)
- `fix/array.py.patch` — dodaja GH#58152 komentar k pandas workaroundu
