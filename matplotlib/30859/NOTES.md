# matplotlib #30859 — relim() ne deluje za Collection artists (scatter itd.)

## Bug v enem stavku

`ax.relim()` ignorira `scatter`, `PathCollection` in ostale `Collection` instance —
ax meje se ne posodobijo po `set_offsets()` ali dodajanju novih točk.

## Zakaj se to zgodi

Dva problema hkrati:

1. `add_collection()` ni klical `collection._set_in_autoscale(True)`, za razliko
   od `add_line()`, `add_patch()`, `add_image()`. Zato je `_get_in_autoscale()`
   pri Collections vračal `False` → `relim()` jih preskočil.

2. `relim()` v `_base.py` ni imel `elif isinstance(a, mcoll.Collection)` veje.
   Vedel je samo za `Line2D`, `Patch`, `Image`. Collections so bile tiho ignorirane.

## Fix

Datoteka: `lib/matplotlib/axes/_base.py`

Sprememba 1 — `add_collection()`:
```python
# dodano po ustvarjanju collection:
collection._set_in_autoscale(True)
```

Sprememba 2 — `relim()`:
```python
elif isinstance(a, mcoll.Collection):
    datalim = a.get_datalim(self.transData)
    if not np.isinf(datalim.minpos).all():
        corners = datalim.get_points()
        self.update_datalim(corners)
```

## Status

- ✅ PR #31530 vložen: https://github.com/matplotlib/matplotlib/pull/31530
- ⏳ Čaka na review

## Testi

`matplotlib/30859/tests/test_debug.py` — lokalni debug testi (6 scenarijev)
Uradni testi bi šli v `lib/matplotlib/tests/test_axes.py`

## Slike

- `analysis/before_fix.png` — posnetek pred fixom
- `analysis/after_fix.png` — posnetek po fixu
