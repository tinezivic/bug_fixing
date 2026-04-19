# Apache Arrow #41017 — DictionaryBuilder izgubi ordered flag

## Bug v enem stavku

`pa.array(["a", "b"], type=dictionary(int8, string, ordered=True))` vrne
array z `ordered=False`. Flag se izgubi v C++ DictionaryBuilderju.

## Kje točno je bug

`cpp/src/arrow/array/builder_dict.h`, vrstica 492 (pred fixom):

```cpp
std::shared_ptr<DataType> type() const override {
    return ::arrow::dictionary(indices_builder_.type(), value_type_);
    //                                                  ^ manjka ordered
}
```

Funkcija `::arrow::dictionary()` ima tretji parameter `bool ordered = false`.
Ker builder nikjer ne shrani `ordered` flaga, ga ne more posredovati — vedno
dobi default `false`.

## Celoten call chain

```
Python:  pa.array(["a","b"], type=dict(int8, string, ordered=True))
  ↓
Cython:  _sequence_to_array()                    [array.pxi]
  ↓
C++:     ConvertPySequence()                      [python_to_arrow.cc]
  ↓
C++:     DictionaryConverter::Init()              [converter.h]
         → MakeDictionaryBuilder(pool, type, ...) [builder.cc]
           type vsebuje ordered=True ✓
  ↓
C++:     DictionaryBuilderCase::CreateFor<T>()    [builder.cc]
         → new DictionaryBuilder<StringType>(value_type, pool)
           PROBLEM: konstruktor dobi samo value_type (string),
           ne celoten DictionaryType — ordered se izgubi ✗
  ↓
C++:     builder.Append("a"), builder.Append("b") — podatki se dodajo OK
  ↓
C++:     builder.FinishInternal()                 [builder_dict.h]
         → (*out)->type = type()
           → dictionary(int8, string)             — ordered=false ✗
```

## Kaj popravek naredi

Tri stvari:

### 1. builder_dict.h — DictionaryBuilderBase (glavna template)

```cpp
// NOVO: member variable
bool ordered_ = false;

// NOVO: setter
void set_ordered(bool ordered) { ordered_ = ordered; }

// POPRAVLJENO: type() posreduje ordered
std::shared_ptr<DataType> type() const override {
    return ::arrow::dictionary(indices_builder_.type(), value_type_, ordered_);
}
```

### 2. builder_dict.h — DictionaryBuilderBase<NullType> (specializacija)

Isti fix kot zgoraj. NullType specializacija je ločen razred (ne podeduje
od glavne template), zato rabi svoj `ordered_` + `set_ordered()`.

### 3. builder.cc — DictionaryBuilderCase struct

```cpp
// NOVO: field v struct
bool ordered;

// POPRAVLJENO: CreateFor() nastavi ordered po konstrukciji
auto* builder = new AdaptiveBuilderType(start_int_size, value_type, pool);
builder->set_ordered(ordered);
out->reset(builder);
```

Plus oba klicalca (`MakeBuilderImpl::Visit` in `MakeDictionaryBuilder`)
zdaj posredujeta `dict_type.ordered()` v `DictionaryBuilderCase`.

## Zakaj ne dodamo ordered v konstruktor?

DictionaryBuilderBase ima **8+ konstruktorjev** (za različne value type
kombinacije — FixedSizeBinary, parametrizirane, z dictionary init, adaptive
vs fixed index type...). Dodajanje parametra v vse bi bil velik diff z
veliko možnostmi za napake. `set_ordered()` po konstrukciji je čistejši
pristop — ena točka spremembe, brez tveganja za breaking change.

## Zakaj DictionaryArray.from_arrays() deluje pravilno?

```python
pa.DictionaryArray.from_arrays(indices, dictionary, ordered=True)
```

Ta pot **ne gre** skozi DictionaryBuilder. Direktno sestavi DictionaryArray
iz indeksov + slovarja + ordered flaga, brez builderja. Zato nikoli ni
imel tega buga.

## Kaj bi te lahko vprašali na review

**V: Zakaj set_ordered() namesto konstruktor parametra?**
O: 8+ konstruktorjev, veliko template specialization. Post-construction
setter je minimalen invaziven pristop ki ne lomi obstoječega API-ja.

**V: Ali to vpliva na performance?**
O: Nič. Ena bool assignment po konstrukciji builderja. Zanemarljivo.

**V: Ali to popravlja Python-level bug?**
O: Da. `pa.array()` iz Python-a gre skozi `MakeDictionaryBuilder` →
naš fix pravilno posreduje `ordered` iz `DictionaryType` v builder.

**V: Kaj pa FinishDelta?**
O: `FinishDelta` kliče `FinishWithDictOffset` ki ne nastavi tipa —
to naredi `FinishInternal` ki kliče `type()`. Pokrito.

**V: Kaj pa NullType?**
O: NullType specializacija je ločen razred, ima svoj `type()` in
`FinishInternal()`. Oba sta popravljena.

**V: Zakaj ni Python testa v PR-ju?**
O: Python testi zahtevajo build pyarrow iz C++ sourca, kar CI naredi
avtomatsko. C++ testi pokrivajo builder logiko direktno.

## Statistika

- 3 datoteke spremenjene
- +83 −9 vrstic (fix + 3 C++ testi)
- 3 C++ testi: `MakeBuilderPreservesOrdered`, `MakeBuilderUnorderedByDefault`,
  `MakeDictionaryBuilderPreservesOrdered`

## Datoteke

- `analysis/root_cause.py` — dokumentira root cause
- `fix/ordered_dictionary_builder.patch` — celoten git diff
- `fix/README.md` — kratek opis fixa
- `tests/test_ordered_dictionary.py` — Python testi (failajo na nepatchanem
  pyarrow, potrditev buga)
