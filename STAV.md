# Stav projektu – 2. fáza

Aktualizuje každý člen pri svojom pull requeste.

## Osoba A – model ✅ hotové

| súbor | stav | poznámka |
|---|---|---|
| `src/mhd/params.py`, `src/mhd/model.py` | ✅ | kontrakt – meniť iba po dohode v tíme |
| `src/mhd/gtfs.py` | ✅ | `CestovnyPoriadok`, cache indexov v `data/cache/` |
| `src/mhd/evaluate.py` | ✅ | `Hodnotitel.ohodnot` |
| `src/mhd/geo.py` | ✅ | **prevzala A od B** (dohoda v skupine) – B ho už nerobí |
| `src/mhd/spatial.py` | ✅ | **prevzala A od B** – `PriestorovyIndex` (BallTree, scikit-learn) |
| `tests/data/toy_gtfs/` | ✅ | očakávané výsledky v `README.md` |
| `tests/test_kontrakt.py`, `test_gtfs.py`, `test_geo.py`, `test_evaluate.py` | ✅ | `pytest` prechádza |
| `scripts/check_model.py` | ✅ | 90 liniek / 1 375 zastávok / 35 932 spojov |
| `report/kap2_model.md` | ✅ | text kapitoly 2 pre C |

Namerané (notebook, Python 3.15): načítanie GTFS z CSV ~4 s, z cache 0,3 s;
jedno vyhodnotenie kandidáta ~12 µs; `zastavky_v_okoli(bod, 800 m)` ~140 µs.

Dôležité pre B a C:

- GTFS v `data/gtfs/` platí **od 16. 11. 2026** do 31. 12. 2027 (feed 6. 11. 2026) –
  dátumy inštancií voľte od 16. 11. 2026. Počet spojov je 35 932 (nie 36 354 ako
  v analýze z 1. fázy).
- Pešia vzdialenosť = haversine (R = 6 371 000 m) · 1,3; čas chôdze zaokrúhlený nahor.
- Nedekódovateľný kandidát má `f = g = inf` a v `porusenia` `'O2'` (linka v ten deň
  nespojí zastávky v tomto smere, vrátane O4) alebo `'O3'` (spoj nie je v časovom okne).
- Užitočné aj mimo kontraktu: `cp.aktivne_sluzby(datum)`, `cp.pocty()`, `cp.je_zastavka(stop_id)`.
- Kandidát s neznámou linkou alebo zastávkou nespadne – vráti sa nedekódovateľný (`O2`).

## Osoba B – inštancie a baseline

| súbor | stav |
|---|---|
| `src/mhd/instances.py`, `scripts/make_instances.py`, `data/instances.json` | ⏳ |
| `src/mhd/baselines/random_search.py`, `greedy.py` | ⏳ |
| `scripts/run_baselines.py`, `results/baselines.csv` | ⏳ |

## Osoba C – overenie a správa

| súbor | stav |
|---|---|
| `src/mhd/neighborhood.py` | ⏳ |
| `scripts/demo_examples.py`, `scripts/bench_eval.py` | ⏳ |
| `README.md`, správa | ⏳ |
