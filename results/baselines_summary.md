# Výsledky baseline

60 inštancií; greedy 1 beh na inštanciu, náhodné hľadanie 10 seedov × rozpočet 1000 vyhodnotení. Priemerné f a prestupy sú iba z prípustných riešení; σ f = priemer cez inštancie zo smerodajnej odchýlky f (prípustných riešení) cez seedy. Vygenerované skriptom `scripts/run_baselines.py`.

## Podľa metódy a skupiny (všetky časy spolu)

| metóda | skupina | behov | prípustné | priem. f [min] | σ f cez seedy | priem. prestupy | iba pešo | čas behu [s] |
|---|---|---|---|---|---|---|---|---|
| greedy | K | 18 | 100 % | 24,0 | – | 0,06 | 50 % | 0,003 |
| greedy | S | 24 | 100 % | 52,0 | – | 0,42 | 33 % | 0,005 |
| greedy | D | 18 | 61 % | 82,4 | – | 1,55 | 28 % | 0,005 |
| nahodne | K | 180 | 100 % | 24,9 | 0,9 | 0,04 | 53 % | 0,208 |
| nahodne | S | 240 | 100 % | 60,7 | 9,7 | 0,37 | 50 % | 0,219 |
| nahodne | D | 180 | 56 % | 97,7 | 19,0 | 1,58 | 23 % | 0,188 |
| greedy | spolu | 60 | 88 % | 48,8 | – | 0,53 | 37 % | 0,004 |
| nahodne | spolu | 600 | 87 % | 55,5 | 9,4 | 0,49 | 43 % | 0,207 |

## Podľa metódy, skupiny a času odchodu

| metóda | skupina | čas | behov | prípustné | priem. f [min] | σ f cez seedy | priem. prestupy | iba pešo | čas behu [s] |
|---|---|---|---|---|---|---|---|---|---|
| greedy | K | ut0730 | 6 | 100 % | 23,4 | – | 0,17 | 50 % | 0,005 |
| greedy | K | ut1300 | 6 | 100 % | 24,9 | – | 0,00 | 50 % | 0,003 |
| greedy | K | so2200 | 6 | 100 % | 23,8 | – | 0,00 | 50 % | 0,002 |
| greedy | S | ut0730 | 8 | 100 % | 50,6 | – | 0,25 | 38 % | 0,005 |
| greedy | S | ut1300 | 8 | 100 % | 51,7 | – | 0,25 | 38 % | 0,005 |
| greedy | S | so2200 | 8 | 100 % | 53,7 | – | 0,75 | 25 % | 0,006 |
| greedy | D | ut0730 | 6 | 50 % | 75,0 | – | 1,67 | 17 % | 0,004 |
| greedy | D | ut1300 | 6 | 67 % | 98,4 | – | 1,25 | 33 % | 0,004 |
| greedy | D | so2200 | 6 | 67 % | 71,9 | – | 1,75 | 33 % | 0,005 |
| nahodne | K | ut0730 | 60 | 100 % | 24,3 | 1,1 | 0,12 | 40 % | 0,208 |
| nahodne | K | ut1300 | 60 | 100 % | 25,5 | 0,7 | 0,00 | 58 % | 0,225 |
| nahodne | K | so2200 | 60 | 100 % | 24,8 | 1,0 | 0,00 | 60 % | 0,193 |
| nahodne | S | ut0730 | 80 | 100 % | 60,6 | 10,1 | 0,41 | 50 % | 0,208 |
| nahodne | S | ut1300 | 80 | 100 % | 61,8 | 10,7 | 0,33 | 54 % | 0,225 |
| nahodne | S | so2200 | 80 | 100 % | 59,7 | 8,2 | 0,36 | 46 % | 0,224 |
| nahodne | D | ut0730 | 60 | 60 % | 97,3 | 19,2 | 1,42 | 18 % | 0,192 |
| nahodne | D | ut1300 | 60 | 62 % | 107,8 | 19,6 | 1,57 | 23 % | 0,189 |
| nahodne | D | so2200 | 60 | 47 % | 84,7 | 17,6 | 1,82 | 28 % | 0,185 |

## Greedy vs. náhodné hľadanie (počet inštancií)

Porovnáva sa g greedy s mediánom g náhodného hľadania cez seedy (rozdiel do 0,05 min = rovnaké).

| skupina | čas | greedy lepší | rovnaké | greedy horší |
|---|---|---|---|---|
| K | ut0730 | 2 | 3 | 1 |
| K | ut1300 | 1 | 5 | 0 |
| K | so2200 | 1 | 5 | 0 |
| K | spolu | 4 | 13 | 1 |
| S | ut0730 | 5 | 3 | 0 |
| S | ut1300 | 4 | 4 | 0 |
| S | so2200 | 4 | 4 | 0 |
| S | spolu | 13 | 11 | 0 |
| D | ut0730 | 4 | 0 | 2 |
| D | ut1300 | 3 | 1 | 2 |
| D | so2200 | 4 | 1 | 1 |
| D | spolu | 11 | 2 | 5 |
| spolu | ut0730 | 11 | 6 | 3 |
| spolu | ut1300 | 8 | 10 | 2 |
| spolu | so2200 | 9 | 10 | 1 |
| spolu | spolu | 28 | 26 | 6 |

## Kandidáti náhodného hľadania

Podiel zo všetkých vygenerovaných (a vyhodnotených) kandidátov.

| skupina | čas | prípustní | neprípustní | nedekódovateľní |
|---|---|---|---|---|
| K | ut0730 | 8,7 % | 22,0 % | 69,3 % |
| K | ut1300 | 9,3 % | 28,9 % | 61,9 % |
| K | so2200 | 24,2 % | 18,9 % | 56,9 % |
| S | ut0730 | 5,3 % | 27,1 % | 67,6 % |
| S | ut1300 | 5,3 % | 29,9 % | 64,8 % |
| S | so2200 | 6,4 % | 22,8 % | 70,9 % |
| D | ut0730 | 1,8 % | 29,7 % | 68,5 % |
| D | ut1300 | 1,9 % | 33,8 % | 64,4 % |
| D | so2200 | 1,9 % | 21,1 % | 77,0 % |
| spolu | ut0730 | 5,3 % | 26,3 % | 68,4 % |
| spolu | ut1300 | 5,5 % | 30,7 % | 63,8 % |
| spolu | so2200 | 10,4 % | 21,1 % | 68,5 % |

Porušenia cez všetkých kandidátov (kandidát môže mať viac porušení): O3 66,9 %, O1 25,0 %, O6 15,8 %.
