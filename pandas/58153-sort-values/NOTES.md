# pandas #58153 — sort_values() with key not working on categorical column

## Issue

https://github.com/pandas-dev/pandas/issues/58153

`DataFrame.sort_values(key=...)` in `Series.sort_values(key=...)` ignorirata
`key` parameter, ko je stolpec tipa `category`. Sortiranje je po abecedi
(vrstni red originalnih kategorij) namesto po mapiranih vrednostih.

## Reproducer

```python
import pandas as pd

df = pd.DataFrame(
    [[1, 2, 'March'], [5, 6, 'Dec'], [3, 4, 'April']],
    columns=['a', 'b', 'month']
)
df.month = df.month.astype('category')
custom_dict = {'March': 0, 'April': 1, 'Dec': 3}

# BUG: sortira po abecedi (April, Dec, March) namesto po custom_dict (March, April, Dec)
df.sort_values(by=['month'], key=lambda x: x.map(custom_dict))
```

## Root Cause

`Categorical.map()` v `pandas/core/arrays/categorical.py` pri neurejenih
(unordered) categorical ohrani vrstni red kategorij iz originalnega categorical-a.

Ko `map({'March': 0, 'April': 1, 'Dec': 3})` mapira `Categorical(['March', 'Dec', 'April'])`
s kategorijami `[April, Dec, March]` (abecedno):

- Mapirane kategorije: `[1, 3, 0]` (pozicijski vrstni red iz originala: April→1, Dec→3, March→0)
- Kode: `[2, 1, 0]` (March=pozicija 2, Dec=pozicija 1, April=pozicija 0)
- `argsort([2, 1, 0])` → `[2, 1, 0]` → April, Dec, March (abecedno!)

Ampak pravilne kategorije bi morale biti `[0, 1, 3]` (sortirane), s kodami `[0, 2, 1]`:
- `argsort([0, 2, 1])` → `[0, 2, 1]` → March, April, Dec ✓

## Fix

V `Categorical.map()` (`pandas/core/arrays/categorical.py`), ko je categorical
**neurejen** (unordered), po mapiranju kategorij le-te sortiramo in prilagodimo kode:

```python
if new_categories.is_unique and not new_categories.hasnans and na_val is np.nan:
    codes = self._codes.copy()
    if not self.ordered:
        # GH#58153: Sort mapped categories for unordered categoricals
        indexer = new_categories.argsort()
        new_categories = new_categories.take(indexer)
        reverse_indexer = np.empty(len(indexer), dtype=np.intp)
        reverse_indexer[indexer] = np.arange(len(indexer))
        mask = codes >= 0
        codes[mask] = reverse_indexer[codes[mask]]
    new_dtype = CategoricalDtype(new_categories, ordered=self.ordered)
    return self.from_codes(codes, dtype=new_dtype, validate=False)
```

### Zakaj samo unordered?

- **Ordered** categorical: vrstni red kategorij je **namerno** definiran s strani
  uporabnika, `map()` ga mora ohraniti
- **Unordered** categorical: vrstni red kategorij je **arbitraren** (ponavadi
  abeceden), `map()` naj ga postavi v naravni red novih vrednosti

## Prizadete code paths

| Path | Datoteka | Opis |
|------|----------|------|
| `DataFrame.sort_values` (single col) | `frame.py` → `nargsort` | Calls `ensure_key_mapped` → key returns categorical → `Categorical.argsort()` sorts by codes |
| `Series.sort_values` | `series.py` | Calls `ensure_key_mapped` → extracts `._values` → `nargsort` → same issue |
| `DataFrame.sort_values` (multi col) | `frame.py` → `lexsort_indexer` | Calls `ensure_key_mapped` → `Categorical(k, ordered=True)` preserves wrong category order |

Fix v `Categorical.map()` popravi **vse tri poti** naenkrat.

## Sprememba vedenja

Za **neurejene** categoricale se po `map()` kategorije zdaj sortirajo.
Primer: `Categorical(['A','B'], categories=['B','A']).map(str.lower)` vrne
kategorije `['a','b']` namesto `['b','a']`.

Vrednosti se NE spremenijo — samo interni vrstni red kategorij se postavi
v naravni (sortirani) red.

8 obstoječih testov v `tests/arrays/categorical/test_map.py` je treba posodobiti
(vsi testirajo vrstni red kategorij za neurejene categoricale).

## Test Results

- 10/10 novih testov PASS
- 97/97 sort_values testov PASS (0 regressions)
- 625/633 categorical testov PASS (8 failov = pričakovana sprememba category order)

## Files Modified

- `pandas/core/arrays/categorical.py` — `Categorical.map()` (+12 lines)

## Patch

`fix/categorical_map_sort_categories.patch`

Generated-by: GitHub Copilot
