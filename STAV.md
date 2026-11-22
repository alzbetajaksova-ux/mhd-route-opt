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

## Osoba B – inštancie a baseline ✅ hotové

| súbor | stav | poznámka |
|---|---|---|
| `src/mhd/instances.py`, `scripts/make_instances.py`, `data/instances.json` | ✅ | 60 inštancií, seed 42; `nacitaj_instancie(cesta)` |
| `src/mhd/baselines/random_search.py`, `greedy.py` | ✅ | `nahodny_kandidat`, `nahodne_hladanie`, `greedy` |
| `tests/test_instances.py`, `tests/test_baselines.py` | ✅ | `pytest` prechádza (64 testov) |
| `scripts/run_baselines.py`, `results/baselines.csv`, `baselines_summary.md`, `baselines_box.png` | ✅ | 600 120 vyhodnotení, ~2 min |
| `README.md` | ✅ | sekcie `demo_examples.py` a `bench_eval.py` doplní C |
| `report/kap3_instancie.md`, `kap5_baseline.md`, `kap6_vysledky.md` | ✅ | texty pre C |

Dôležité pre C:

- `nahodny_kandidat(cp, p, par, rng, pamat=None)` – vždy spĺňa O2, ≤ 4 úseky;
  pri opakovaných volaniach na tej istej požiadavke podaj `Pamat(cp, p)` (zrýchlenie).
- `nahodne_hladanie` vracia `VysledokHladania` s počtami prípustných /
  neprípustných / nedekódovateľných kandidátov a `porusenia` (Counter).
- `greedy(hod, cp, p, par)` vracia `(VysledokHladania, počet volaní najblizsi_odchod)`.
- Na reálnych dátach je ~67 % náhodných kandidátov nedekódovateľných (O3) –
  hlavne nočné a zriedkavé linky, ktoré v daný deň premávajú, ale nie v časovom okne.
- Skripty volajú `sys.stdout.reconfigure(encoding="utf-8")` – inak vo Windows
  konzole pri presmerovaní výstupu padá výpis s diakritikou.

## Osoba C – overenie a správa

| súbor | stav | poznámka |
|---|---|---|
| `src/mhd/neighborhood.py`, `tests/test_neighborhood.py` | ✅ | 6 operátorov + `nahodny_sused`, `susedia`; 51 testov |
| `scripts/demo_examples.py`, `results/demo_examples.md` | ✅ | 5 trás, ručne overené na imhd.sk (zhoda na minútu) |
| `scripts/bench_eval.py`, `results/bench.md` | ✅ | `ohodnot` ~36 µs, prípustných 7,2 %, najčastejšie O3 |
| `report/kap4_overenie.md`, `report/kap7_metody.md` | ✅ | |
| `report/sprava.md` | ✅ | zložená správa (8 kapitol); doplniť mená riešiteľov |
| `README.md` – sekcie o skriptoch C | ✅ | |
| finálne PDF vo Word šablóne | ⏳ | |
