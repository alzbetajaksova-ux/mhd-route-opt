# Meranie modelu a operátorov okolia

Vygenerované skriptom `scripts/bench_eval.py` (seed 0). Python 3.12.7, Windows 11, procesor: AMD64 Family 23 Model 104 Stepping 1, AuthenticAMD. Časy závisia od počítača.

## Načítanie GTFS

- z CSV (bez cache): **4,86 s**
- z cache (`data/cache/*.pkl`): **0,36 s**
- 90 liniek, 1375 zastávok, 35932 spojov

## Vyhodnotenie kandidáta (10000 náhodných kandidátov)

Kandidáti z `nahodny_kandidat` (B) striedavo na 60 inštanciách z `data/instances.json` (≈ 166 na inštanciu). Generovanie trvalo 3,23 s (323 µs na kandidáta, vrátane hľadania zastávok v okolí).

- priemerný čas jedného `ohodnot`: **35,9 µs** (najlepší z 3 behov celej vzorky; priemer behov 36,5 µs)
- vyhodnotenie všetkých 10000 kandidátov: 0,359 s

Podľa počtu úsekov (čas meraný pri každom volaní, preto mierne vyšší):

| počet úsekov | kandidátov | priem. čas `ohodnot` [µs] | medián [µs] |
|---|---|---|---|
| 0 | 665 | 6,7 | 5,8 |
| 1 | 79 | 20,8 | 18,9 |
| 2 | 60 | 29,9 | 29,3 |
| 3 | 63 | 33,8 | 32,2 |
| 4 | 9133 | 62,3 | 40,9 |

| stav kandidáta | kandidátov | priem. čas `ohodnot` [µs] | medián [µs] |
|---|---|---|---|
| prípustní | 723 | 12,8 | 5,9 |
| neprípustní | 2624 | 61,9 | 56,9 |
| nedekódovateľní | 6653 | 61,2 | 29,9 |

## Prípustnosť náhodných kandidátov

| skupina | kandidátov | prípustní | neprípustní | nedekódovateľní |
|---|---|---|---|---|
| K | 3006 | 14,3 % | 23,9 % | 61,9 % |
| S | 4006 | 5,8 % | 26,3 % | 67,8 % |
| D | 2988 | 2,0 % | 28,5 % | 69,5 % |
| spolu | 10000 | **7,2 %** | 26,2 % | 66,5 % |

Porušené obmedzenia (podiel zo všetkých kandidátov; kandidát môže mať viac porušení):

| obmedzenie | kandidátov | podiel |
|---|---|---|
| O3 | 6653 | 66,5 % |
| O1 | 2532 | 25,3 % |
| O6 | 1572 | 15,7 % |

Najčastejšie porušené: **O3**

## Operátory okolia (2000 kandidátov s aspoň jedným úsekom)

Každý operátor sa zavolal raz na každého kandidáta. Podiely dekódovateľných, prípustných a zlepšujúcich (g suseda < g kandidáta) susedov sú z vrátených (nie None) susedov.

### Všetci kandidáti s úsekmi

| operátor | volaní | vráti None | priem. čas [ms] | dekódovateľní | prípustní | zlepšujúci |
|---|---|---|---|---|---|---|
| `zmen_nastup` | 2000 | 19,7 % | 0,50 | 30,2 % | 2,2 % | 4,6 % |
| `zmen_vystup` | 2000 | 8,0 % | 0,03 | 30,9 % | 3,0 % | 15,4 % |
| `posun_prestupu` | 2000 | 4,2 % | 0,43 | 30,4 % | 0,9 % | 2,9 % |
| `vymen_linku` | 2000 | 31,1 % | 0,05 | 26,5 % | 0,9 % | 16,0 % |
| `pridaj_prestup` | 2000 | 98,5 % | 0,00 | 32,3 % | 32,3 % | 3,2 % |
| `odober_prestup` | 2000 | 38,0 % | 0,03 | 41,3 % | 0,8 % | 41,2 % |
| spolu | 12000 | **33,2 %** | 0,17 | 31,5 % | 1,8 % | 14,3 % |

### Iba dekódovateľní kandidáti (614)

Pre metódy 3. fázy je dôležitejšia táto tabuľka: lokálne hľadanie aj GA budú meniť hlavne dekódovateľných kandidátov.

| operátor | volaní | vráti None | dekódovateľní | prípustní | zlepšujúci |
|---|---|---|---|---|---|
| `zmen_nastup` | 614 | 18,2 % | 89,4 % | 6,2 % | 7,6 % |
| `zmen_vystup` | 614 | 6,5 % | 98,3 % | 9,4 % | 48,4 % |
| `posun_prestupu` | 614 | 4,6 % | 97,3 % | 2,9 % | 7,3 % |
| `vymen_linku` | 614 | 42,5 % | 62,0 % | 2,8 % | 21,0 % |
| `pridaj_prestup` | 614 | 96,7 % | 45,0 % | 45,0 % | 0,0 % |
| `odober_prestup` | 614 | 40,1 % | 97,8 % | 1,9 % | 97,6 % |
| spolu | 3684 | **34,8 %** | 90,3 % | 5,3 % | 33,0 % |

### Kandidáti s menej ako 4 úsekmi (47)

| operátor | volaní | vráti None | dekódovateľní | prípustní | zlepšujúci |
|---|---|---|---|---|---|
| `zmen_nastup` | 47 | 10,6 % | 71,4 % | 69,0 % | 23,8 % |
| `zmen_vystup` | 47 | 2,1 % | 69,6 % | 56,5 % | 28,3 % |
| `posun_prestupu` | 47 | 55,3 % | 61,9 % | 61,9 % | 9,5 % |
| `vymen_linku` | 47 | 68,1 % | 53,3 % | 53,3 % | 20,0 % |
| `pridaj_prestup` | 47 | 34,0 % | 32,3 % | 32,3 % | 3,2 % |
| `odober_prestup` | 47 | 83,0 % | 50,0 % | 50,0 % | 50,0 % |
| spolu | 282 | **42,2 %** | 59,5 % | 55,2 % | 20,2 % |

- `nahodny_sused` (najviac 10 pokusov): None v 0,1 % volaní, priemerne 0,29 ms
- susedov, ktorí porušujú O2 alebo majú viac ako 4 úseky: **0**
