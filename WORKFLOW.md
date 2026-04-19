# Open-Source Bug Fixing — Celoten Workflow

Od prijavljenega buga do mergeanega fixa. Konkretno za pandas/arrow, ampak princip velja za večino velikih OSS projektov.

---

## 1. Bug Report (Issue)

**Kdo:** Kdorkoli — uporabnik, ki naleti na problem.
**Kje:** GitHub Issues (`github.com/pandas-dev/pandas/issues`)
**Kaj vsebuje dober bug report:**
- Opis problema (kaj se zgodi vs. kaj bi se moralo)
- Minimalni reproducer (koda, ki pokaže bug)
- Verzija pandas/python/OS
- Pričakovani output vs. dejanski output

**Primer:** [#58153](https://github.com/pandas-dev/pandas/issues/58153) — `sort_values(key=...)` na categorical stolpcu ignorira `key` parameter.

**Kaj se zgodi potem:**
- Maintainerji dodajo labele (Bug, Categorical, Needs Triage...)
- Včasih kdo potrdi bug ali doda kontekst
- Issue čaka, da se ga kdo loti

---

## 2. Kdo popravlja?

**Kdorkoli lahko.** To je bistvo open-source. Ni treba bit "član tima".

Možni scenariji:
- **Core maintainer** — zaposleni ali dolgoleten contributor, ki pozna kodo
- **Zunanji contributor** — kdorkoli s GitHub accountom (= mi)
- **Triage bot/CodeTriage** — servisi, ki razpošiljajo issue-je prostovoljcem

**Kako "vzameš" bug:**
- Napišeš komentar na issue: "I'd like to work on this" (ni obvezno, ampak vljudno)
- Forkneš repo in začneš delat
- Nihče te ne blokira — če pošlješ dober PR, ga bodo pogledali

---

## 3. Reprodukcija buga

**Najpomembnejši korak.** Preden karkoli popravljaš, moraš bug videt.

```bash
# Ustvari venv z isto verzijo
python -m venv .venv && source .venv/bin/activate
pip install pandas  # ali build from source

# Poženi reproducer iz issue-ja
python reproduce.py
```

Če ne moreš reproducirati → bug je morda že fixan, ali pa je specifičen za neko verzijo/OS.

---

## 4. Iskanje root cause

**Najtežji del.** Tu se dejansko razume kodo.

Pristop:
1. Začni z reproducer kodom
2. Sledi kodo navzdol: `sort_values()` → `nargsort()` → `Categorical.map()` → aha!
3. Uporabi debugger, print statements, git blame
4. Preveri git historijo — kdaj se je obnašanje spremenilo? (`git bisect`)
5. Beri obstoječe teste — kaj je bilo **namerno** in kaj je bug

**Primer naše izkušnje (#58153):**
- Začeli smo v `nargsort()` — napačna smer
- Potem `Series.sort_values()` — bližje, ampak zlomilo obstoječ test
- Pravi root cause: `Categorical.map()` ohranja vrstni red kategorij iz originalnega categoricala

**Lekcija:** Fixing simptoma ≠ fixing buga. Išči pravi vzrok.

---

## 5. Implementacija fixa

**Pravila:**
- **Minimalen diff** — spremeni čim manj kode. Reviewerji ne marajo velikih sprememb.
- **Ne refaktoriraj** ob poti. Samo fix.
- **Backward compatibility** — ne zlomi obstoječega obnašanja razen če je to bug
- **Edge cases** — kaj če so mešani tipi? Kaj če je empty? Kaj če je ordered vs unordered?

**Primer (naš fix v `categorical.py`):**
```python
if not self.ordered:
    try:
        indexer = new_categories.argsort()
    except TypeError:
        # Mixed types (e.g. str and float) can't be compared
        pass
    else:
        new_categories = new_categories.take(indexer)
        # ... remap codes
```

Zakaj `try/except`? Ker mešani tipi (str + float) ne morejo biti sortirani. To smo odkrili šele ko je CI padel.

---

## 6. Testi

**Brez testov PR ne bo mergan.** Vedno.

Kaj moraš napisat:
- **Regression test** — test, ki reproducira originalni bug (mora FAIL-at brez fixa)
- **Edge case testi** — prazni podatki, NaN, mešani tipi, ordered vs unordered
- **Update obstoječih testov** — če se pričakovano obnašanje spremeni

Kaj moraš pognati:
```bash
# Specifični testi za tvoj fix
python -m pytest pandas/tests/arrays/categorical/test_map.py -v

# Širši testi — preveri da nisi zlomil kaj drugega
python -m pytest pandas/tests/series/methods/test_sort_values.py -v
python -m pytest pandas/tests/frame/methods/test_sort_values.py -v

# Idealno: celoten test suite (ampak traja ure — to naredi CI)
```

---

## 7. Pull Request (PR)

**Struktura PR-ja na pandas:**

1. **Fork** repo na svoj GitHub account
2. **Branch** iz main: `git checkout -b fix-categorical-map-sort-categories`
3. **Commit(s)** — jasen message z `GH#XXXXX` referenco
4. **Push** na svoj fork: `git push origin fix-categorical-map-sort-categories`
5. **Odpri PR** proti `pandas-dev:main`

**PR opis mora vsebovati:**
- Kaj je bug (s povezavo na issue)
- Kaj je root cause
- Kaj fix naredi
- Kakšen je behavioral change (če je)
- Katere teste si dodal/spremenil

**Primer:** [PR #65286](https://github.com/pandas-dev/pandas/pull/65286)

---

## 8. CI (Continuous Integration)

**Ko odpreš PR, se avtomatsko požene ~45 CI jobov:**

| Job | Kaj preverja |
|-----|-------------|
| Unit Tests | Celoten test suite (~170k testov) na Linux, macOS, Windows |
| Linux-Musl | Alpine Linux (minimalen OS — ujame specifične probleme) |
| Numpy Nightly | Prihodnja verzija numpy — ujame deprecation warnings |
| Pyarrow Nightly | Isto za pyarrow |
| Docstring validation | Ali so docstringi pravilni |
| Pre-commit hooks | Formatting, linting (ruff, mypy) |
| ASV Benchmarks | Performance — ali si upočasnil kaj |
| Doc Build | Ali se dokumentacija zbuilda |

**Če CI pade:**
- Poglej kateri job je padel
- Preberi error log (Annotations sekcija)
- Fixaj in pushaj nov commit (ali amend + force push)
- CI se požene znova

**Naša izkušnja:**
- 1. run: 3 faili — `TypeError: '<' not supported between instances of 'str' and 'float'`
- Fix: dodali `try/except TypeError` za mešane tipe
- 2. run: čakamo...

---

## 9. Code Review

**Ko CI passne, maintainerji pregledajo kodo.**

Kdo reviewja:
- Core maintainerji (imajo write access)
- Včasih avtomatski bot dodeli reviewerja
- Včasih moraš čakat dneve/tedne (to so prostovoljci!)

Kaj gledajo:
- **Pravilnost** — ali fix dejansko reši problem
- **Edge cases** — kaj si spregledal
- **Stil kode** — ali sledi konvencijam projekta
- **Testi** — ali so dovolj obsežni
- **Dokumentacija** — ali changelog entry, docstring updates
- **Performance** — ali je fix O(n) ali O(n²)

Možni outcomes:
- ✅ **Approve** — vse OK, ready za merge
- 🔄 **Request changes** — moraš popravit nekaj in pushati znova
- 💬 **Comment** — vprašanja, diskusija, predlogi

**Tipični review komentarji:**
- "Can you add a test for the case when..."
- "This should go in the whatsnew entry for the next release"
- "Nit: use `foo` instead of `bar`" (stilski popravki)
- "Can you squash the commits?"

---

## 10. Iteracija

**Redko gre skozi v prvem poskusu.** Tipičen cikel:

```
PR → CI fail → fix → CI pass → Review → Changes requested → Fix → Review → Approve
```

Stvari ki jih reviewerji pogosto zahtevajo:
- **whatsnew entry** — vpis v `doc/source/whatsnew/vX.Y.Z.rst`
- **Squash commits** — združi vse v en čist commit
- **Bolj specifičen test** — teste za edge case ki si ga spregledal
- **Drugačen pristop** — včasih reviewer pozna boljšo rešitev

---

## 11. Merge

**Ko je PR approved in CI zelen:**

- Maintainer klikne "Squash and merge" (ali "Rebase and merge")
- Tvoj fix je zdaj v `main` branchu
- Issue se avtomatsko zapre (če si v PR napisal "Closes #58153")

---

## 12. Release

**Fix pride v naslednjo verzijo pandas.**

- pandas dela release cca vsake 1-2 meseca (patch) ali 6 mesecev (minor)
- Fix se pojavi v changelog-u pod "Bug Fixes"
- Uporabniki ga dobijo z `pip install --upgrade pandas`

---

## Povzetek — Timeline za en bug fix

| Korak | Čas | Kdo |
|-------|-----|-----|
| Bug report | Dan 0 | Uporabnik |
| Čakanje na contributorja | Dnevi → meseci | Nihče (čaka) |
| Reprodukcija + root cause | 1-4 ure | Ti |
| Implementacija + testi | 2-8 ur | Ti |
| PR + CI | 30 min (CI traja ~10-30 min) | Ti + GitHub Actions |
| CI debug + fixanje | 0-∞ ur | Ti |
| Code review | 1 dan → tedni | Maintainerji |
| Iteracija | 0-N ciklov | Ti + Maintainerji |
| Merge | 1 klik | Maintainer |
| Release | Tedni → meseci | Release manager |

---

## Koristni ukazi

```bash
# Fork + clone
gh repo fork pandas-dev/pandas --clone

# Nova branch za fix
git checkout -b fix-description-of-bug

# Commit z referenco na issue
git commit -m "BUG: Fix description (GH#XXXXX)"

# Push na fork
git push origin fix-description-of-bug

# Odpri PR
gh pr create --base main --head fix-description-of-bug \
  --title "BUG: Fix description (#XXXXX)" \
  --body "Description..."

# Preveri CI status
gh pr checks

# Po review popravkih
git add -A && git commit --amend --no-edit && git push --force-with-lease
```

---

## Naši PR-ji

| # | Bug | Repo | PR | Branch | Status |
|---|-----|------|----|--------|--------|
| 1 | [#58153](https://github.com/pandas-dev/pandas/issues/58153) — Categorical.map() sort categories | pandas | [#65286](https://github.com/pandas-dev/pandas/pull/65286) | `fix-categorical-map-sort-categories` | Odprto |
| 2 | [#58321](https://github.com/pandas-dev/pandas/issues/58321) — Arrow str.split regex inference | pandas | [#65287](https://github.com/pandas-dev/pandas/pull/65287) | `fix-arrow-str-split-regex` | Odprto |
| 3 | [#35410](https://github.com/pandas-dev/pandas/issues/35410) — Truncated DataFrame formatters | pandas | [#65288](https://github.com/pandas-dev/pandas/pull/65288) | `fix-truncated-formatters` | Odprto |
| 4 | [#65218](https://github.com/pandas-dev/pandas/issues/65218) — DataFrame.agg + numeric_only | pandas | [#65289](https://github.com/pandas-dev/pandas/pull/65289) | `fix-agg-list-numeric-only` | Odprto |
| 5 | [#65112](https://github.com/pandas-dev/pandas/issues/65112) — Arrow str[0] getitem | pandas | [#65292](https://github.com/pandas-dev/pandas/pull/65292) | `fix-arrow-str-getitem` | Odprto |
| 6 | [#55508](https://github.com/pandas-dev/pandas/issues/55508) — Bar plot xticks positions | pandas | [#65293](https://github.com/pandas-dev/pandas/pull/65293) | `fix-bar-xticks` | Odprto |
| 7 | [#41017](https://github.com/apache/arrow/issues/41017) — DictionaryBuilder ordered flag | arrow | [#49797](https://github.com/apache/arrow/pull/49797) | `fix-dictionary-builder-ordered` | Odprto |

**Samo analiza (brez PR):**
| Bug | Repo | Razlog |
|-----|------|--------|
| [#58152](https://github.com/pandas-dev/pandas/issues/58152) — pyarrow dict ordered | pandas | Workaround že obstaja, root cause je v Arrow (#41017) |
