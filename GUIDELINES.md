# PR Guidelines — pandas / matplotlib / arrow

Naše delovno pravilo: **ne pošlji PR-ja preden ne preberem te datoteke.**

---

## Skupno za vse tri repo-je

### Commit message / PR naslov
- **pandas**: `BUG: <kratki opis>` | `ENH:` | `DOC:` | `TST:` | `PERF:` | `TYP:` | `CLN:`
- **matplotlib**: `BUG: <kratki opis>` | `ENH:` | `DOC:` | `TST:` | `MNT:`
- **arrow**: `GH-<number>: [Component] <kratki opis>` — primer: `GH-41017: [C++] Preserve ordered flag in DictionaryBuilder`

### Branch
- Vedno na `feature/fix` branchu, ne na `main`
- PR targetira `main` (ali `upstream/main`)

### Obvezno pred PR-jem
- [ ] Testi so napisani (ali obstoječi testi pokrivajo spremembo)
- [ ] `pre-commit run --files <file>` je prešel (ruff, isort, clang-format)
- [ ] CI je zelen preden pingaš reviewerje

### Kaj mora PR description vsebovati
- Opis: zakaj je sprememba potrebna
- Reference na issue: `Closes #1234` ali `Fixes #1234`
- **Testiranje**: kaj smo testirali — in **kaj nismo**
- Kratki primer če je relevantno

---

## pandas-dev/pandas

### Sources
- https://pandas.pydata.org/pandas-docs/stable/development/contributing.html
- https://pandas.pydata.org/pandas-docs/stable/development/contributing_codebase.html

### Naslov PR-ja
Začne z enim od prefiksov:
```
BUG / ENH / DOC / TST / BLD / PERF / TYP / CLN
```

### Testi
- Testi živijo v `pandas/tests/`
- Osnovna struktura: funkcionalni testi `def test_*`
- Primerjava: `tm.assert_series_equal(result, expected)` / `tm.assert_frame_equal(...)`
- Parametrize: `@pytest.mark.parametrize`
- Izjeme: `pytest.raises(ValueError, match="message")`
- Opozorila: `tm.assert_produces_warning(DeprecationWarning, match="...")`
- Dodaj komentar `# GH <issue_number>` ob novem testu

### Kje so testi
| Tip spremembe | Mapa |
|---|---|
| Series metoda | `tests/series/methods/test_<method>.py` |
| DataFrame metoda | `tests/frame/methods/test_<method>.py` |
| Indexing | `tests/indexing/` |
| Extension Array | `tests/arrays/` |
| IO | `tests/io/` |
| Plotting | `tests/plotting/` |

### Dokumentacija
- Dodaj entry v `doc/source/whatsnew/v<X.Y.Z>.rst`
- Format: `:issue:`1234`` za referenco
- Bugfix → ustrezna bugfix sekcija (ne `Other`)

### Pre-commit (pandas)
```bash
pre-commit run --files pandas/path/to/changed.py
# ali za cel diff:
pre-commit run --from-ref=upstream/main --to-ref=HEAD --all-files
```

### Zagon testov
```bash
pytest pandas/tests/path/to/test_file.py -xvs
# hitrejše (4 cpuji, brez slow/network/db):
pytest pandas -n 4 -m "not slow and not network and not db and not single_cpu"
```

### Backwards compatibility
- Ne lomi API brez deprecation warninga
- Deprecation: `FutureWarning` + `.. deprecated:: X.Y.Z` v docstringu

---

## matplotlib/matplotlib

### Sources
- https://matplotlib.org/devdocs/devel/pr_guide.html
- https://matplotlib.org/devdocs/devel/contribute.html

### Naslov PR-ja
```
BUG: Fix <kratki opis>
ENH: Add <kratki opis>
DOC: Update <kratki opis>
```
Naslov opisuje problem/rešitev, ne samo "Addresses issue #XXXX".

### PR template (OBVEZNO izpolniti)
```markdown
## PR summary
Zakaj je sprememba potrebna? Kaj rešuje? Zakaj ta implementacija?
Closes #<number>

## AI Disclosure
Opis kako smo uporabili AI (GitHub Copilot / Claude Sonnet 4.6 za analizo in code generation).

## PR checklist
- [ ] "closes #0000" je v PR opisu
- [ ] Nova/spremenjena koda ima teste
- [ ] (če plotting) primer v examples gallery
- [ ] (če nova feature/API) entry v what's new + directive
- [ ] Dokumentacija sledi guidelines
```

### AI Policy (matplotlib je strožji!)
- **Dovoljeno**: razumevanje kode, ideje za rešitev, prevod/proofreading opisa
- **Prepovedano**: boti/agenti ki direktno ustvarjajo issues/PRe/komentarje
- **Prepovedano**: reševati issue ki ga ne bi mogel rešiti brez AI
- **Prepovedano**: AI output brez da razumeš in verificiraš kaj počne
- Low-value AI PRe bodo **zaprli**, pri resnih primerih **ban**

### Testi
- `lib/matplotlib/tests/`
- `pytest lib/matplotlib/tests/test_axes.py -xvs`
- pre-commit: `prek` (spelling, formatting)

### Dokumentacija
- Vsaka nova feature → docstring + primer v `Examples` sekciji
- API sprememba → `doc/api/next_api_changes/`
- Nova feature → entry v `doc/user/whats_new`

### Approval
- Koda spremembe (src/lib): **2 approvalova** od core developerjev
- Dokumentacija/primeri: **1 approval** dovolj

---

## apache/arrow

### Sources
- https://github.com/apache/arrow/blob/main/CONTRIBUTING.md
- https://arrow.apache.org/docs/developers/guide/

### Naslov PR-ja (obvezno!)
```
GH-<issue_number>: [Component] Kratki opis
```
Primeri komponent: `[C++]`, `[Python]`, `[Java]`, `[C++][Python]`

Primer: `GH-41017: [C++] Preserve ordered flag in DictionaryBuilder`

### Issue MORA obstajati pred PR-jem
- Vsaka sprememba funkcionalnosti → GitHub issue
- Izjema: drobne doc spremembe (< 2 datoteki, < 500 besed) → prefix `MINOR:`

### Komentar "take" za assignment
- Dodaj komentar `take` na issue da te assignajo

### Testi (C++)
- Testi v `cpp/src/arrow/` → `_test.cc` datoteke
- Build: `cmake .. && make -j4 arrow-test-<module> && ctest`
- Specifičen test: `./build/debug/arrow-test-<module> --gtest_filter="TestName"`

### Testi (Python)
- `pyarrow/tests/`
- `pytest pyarrow/tests/test_<module>.py -xvs`

### Večje spremembe
- Najprej razprava na `arrow-dev` mailing listu

---

## Naš workflow (skupni checklist)

```
1. Poiščemo bug (GitHub issues)
2. Razumemo root cause (static analysis, reproducer)
3. Napišemo fix
4. Napišemo / preverimo teste
5. pre-commit run
6. git add && git commit -m "BUG/ENH/GH-XXX: ..."
7. git push origin <branch>
8. gh pr create (z izpolnjenim templateom)
9. PR description: Summary + Testing (honest!) + AI Disclosure
10. Čakamo na CI + review
```

### AI Disclosure (naš standard)
```
This fix was developed with the assistance of GitHub Copilot (Claude Sonnet 4.6).
The diagnosis, code analysis, and root cause identification were performed by the contributor.
The AI assisted with code generation and diff review.
[Testing status: either "tested locally" OR "not runtime-tested, based on static analysis"]
```

### Kar NE delamo
- Ne trdimo da smo testirali če nismo
- Ne pošljemo PR brez da razumemo fix
- Ne ignoriramo CI napak
- Ne pišemo changelog/whatsnew entry za Bambu Studio (ni Python projekt)
