# mhd-route-opt – optimalizácia cesty MHD v Bratislave

Školský projekt z predmetu Moderné prístupy v optimalizácii (TUKE), Zadanie 2,
variant 1B. Pre štart, cieľ, dátum a čas odchodu hľadáme trasu MHD
(0 – 4 jazdy + chôdza) s najkratším celkovým časom penalizovaným za prestupy:

- f(x) = (príchod − t₀) / 60 + 5 · P  [min], P = počet prestupov,
- g(x) = f(x) + 200 · V(x), V = počet porušených obmedzení z O1, O5, O6,
- nedekódovateľný kandidát (O2 – O4) má f = g = ∞.

Fáza 2 obsahuje model problému (načítanie GTFS, dekóder, f a g), 60 inštancií
a dve porovnávacie metódy (náhodné hľadanie a greedy).

## Inštalácia

Python 3.11 alebo novší.

```bash
python -m venv .venv
```

Aktivácia: Windows `.venv\Scripts\activate`, Linux/macOS `source .venv/bin/activate`.

```bash
pip install -r requirements.txt
```

`requirements.txt` nainštaluje aj samotný balík `mhd` (`pip install -e .`).
Obsahuje aj `matplotlib` pre graf `results/baselines_box.png`; bez neho
`run_baselines.py` graf iba preskočí.

## Dáta

- `data/gtfs/` – zafixovaný GTFS Dopravného podniku Bratislava (feed 6. 11. 2026,
  platnosť 16. 11. 2026 – 31. 12. 2027; 90 liniek, 1 375 zastávok, 35 932 spojov).
- `data/cache/` – indexy GTFS (pickle) vytvorené pri prvom načítaní; nie sú v gite.
- `data/instances.json` – 60 inštancií (generuje `scripts/make_instances.py`).

## Príkazy (v tomto poradí, z koreňa repozitára)

| príkaz | čo robí | vytvorí | trvanie |
|---|---|---|---|
| `pytest` | unit testy na malej testovacej sieti `tests/data/toy_gtfs/` | – | ~1 s |
| `python scripts/check_model.py` | načíta GTFS, ohodnotí jednu ručnú trasu, zmeria vyhodnotenie | `data/cache/*.pkl` | ~5 s prvýkrát |
| `python scripts/make_instances.py` | 60 inštancií (seed 42) | `data/instances.json` | ~5 s |
| `python scripts/run_baselines.py` | greedy + náhodné hľadanie (seedy 0–9, rozpočet 1 000) na všetkých inštanciách | `results/baselines.csv`, `results/baselines_summary.md`, `results/baselines_box.png` | ~2–3 min |
| `python scripts/demo_examples.py` | 5 overených trás na reálnych dátach (ut 24. 11. 2026, 7:30) | `results/demo_examples.md` | ~1 s |
| `python scripts/bench_eval.py` | meranie: načítanie GTFS, čas `ohodnot` na 10 000 náhodných kandidátoch, podiel prípustných, operátory okolia | `results/bench.md` | ~15 s |

Užitočné prepínače `run_baselines.py`: `--seedy 2 --rozpocet 200` (rýchla skúška),
`--iba-suhrn` (prepočíta súhrn a graf z existujúceho CSV), `--vystup DIR`.
`make_instances.py` má `--seed`. Všetky skripty majú pevný seed, takže
opakované spustenie dá rovnaké výsledky (okrem nameraných časov behu).

### Overené príklady – `scripts/demo_examples.py`

Ohodnotí päť ručne zostavených kandidátov v utorok 24. 11. 2026 s odchodom o 7:30:
(a) priama trasa 93 Hlavná stanica → Jiráskova, (b) trasa s 1 prestupom
93 Hlavná stanica → Zochova, 31 Zochova → Lanfranconi, (c) iba pešo
Hodžovo nám. → Zochova, (d) neprípustná trasa (nástup 1,4 km od štartu, O1) a
(e) nedekódovateľná trasa (linka 93 v opačnom smere, O2). Pre každú vypíše itinerár
s názvami zastávok, časmi, linkami a metrami chôdze, potom f, g a porušenia. Na konci
vypíše tabuľku „vypočítané vs. z cestovného poriadku“, ktorej prázdne stĺpce sa
vypĺňajú ručne podľa dpb.sk / imhd.sk. Výstup uloží aj do `results/demo_examples.md`.
Prepínače: `--gtfs DIR`, `--vystup DIR`.

### Meranie – `scripts/bench_eval.py`

Zmeria čas načítania GTFS z CSV a z cache, priemerný čas jedného `Hodnotitel.ohodnot`
na 10 000 kandidátoch z `nahodny_kandidat` (striedavo na všetkých inštanciách),
podiel prípustných, neprípustných a nedekódovateľných kandidátov a početnosť
porušení. Pre operátory okolia zmeria podiel volaní, ktoré vrátia None, ich čas a
podiel dekódovateľných, prípustných a zlepšujúcich susedov a overí, že žiadny sused
neporušuje O2. Výsledky uloží do `results/bench.md`. Prepínače:
`--pocet 10000` (počet kandidátov), `--pocet-op 2000` (na koľkých sa skúšajú
operátory), `--seed 0`, `--vystup FILE`. Časy závisia od počítača; ostatné čísla sú
pri rovnakom seede rovnaké.

### Operátory okolia – `src/mhd/neighborhood.py`

```python
import random
from mhd.neighborhood import OPERATORY, nahodny_sused, susedia

rng = random.Random(0)
s = nahodny_sused(k, p, cp, par, rng)         # jeden sused alebo None
vzorka = susedia(k, p, cp, par, rng, limit=10)  # najviac 10 rôznych susedov
```

Operátory `zmen_nastup`, `zmen_vystup`, `posun_prestupu`, `vymen_linku`,
`pridaj_prestup`, `odober_prestup` majú tvar `op(k, p, cp, par, rng) -> Kandidat | None`.
Vrátený sused vždy spĺňa O2 a má najviac 4 úseky; pôvodný kandidát sa nemení.

### Stĺpce `results/baselines.csv`

`instancia, skupina (K/S/D), cas (ut0730/ut1300/so2200), metoda (greedy/nahodne),
seed, f, g, pripustny, prestupy, chodza_m, celkovy_cas_min, pocet_vyhodnoteni,
podiel_pripustnych_kandidatov, podiel_nedekodovatelnych, cas_behu_s`
a doplnkovo `porusenia, pocet_usekov, iba_pesho, podiel_nepripustnych_kandidatov,
porusenia_kandidatov` (napr. `O1:179;O3:689`) a `volani_najblizsi_odchod` (iba greedy).
Podiely kandidátov sa pri greedy nevypĺňajú (vyhodnotí iba 2 kandidátov).

## Použitie v kóde

```python
from mhd.gtfs import CestovnyPoriadok
from mhd.evaluate import Hodnotitel
from mhd.params import Parametre
from mhd.instances import nacitaj_instancie
from mhd.baselines.random_search import nahodne_hladanie, nahodny_kandidat
from mhd.baselines.greedy import greedy

cp = CestovnyPoriadok.nacitaj("data/gtfs")
par = Parametre()
hod = Hodnotitel(cp, par)
p = nacitaj_instancie("data/instances.json")[0]

r = nahodne_hladanie(hod, cp, p, par, rozpocet=1000, seed=0)
print(r.kandidat, r.hodnotenie.f, r.pripustny, r.pocet_pripustnych)
g, volani = greedy(hod, cp, p, par)
```

Každé vyhodnotenie kandidáta ide cez `Hodnotitel.ohodnot`, ktorý počíta volania
(`pocet_vyhodnoteni`), takže rozpočet metód je férovo porovnateľný.

## Štruktúra repozitára

```
data/gtfs/               GTFS DPB (zafixovaná verzia)
data/instances.json      60 inštancií
src/mhd/
  params.py              Parametre modelu                      (A, kontrakt)
  model.py               dátové triedy Usek, Kandidat, ...      (A, kontrakt)
  geo.py, spatial.py     pešia vzdialenosť, index zastávok      (A)
  gtfs.py                CestovnyPoriadok – načítanie a indexy  (A)
  evaluate.py            Hodnotitel.ohodnot – dekóder, f, g     (A)
  instances.py           generovanie a načítanie inštancií      (B)
  baselines/
    random_search.py     nahodny_kandidat, nahodne_hladanie     (B)
    greedy.py            greedy                                 (B)
  neighborhood.py        operátory okolia                       (C)
scripts/                 check_model, make_instances, run_baselines, demo_examples, bench_eval
tests/                   pytest; tests/data/toy_gtfs/ = malá testovacia sieť
results/                 výsledky behov
report/                  texty kapitol správy
```
