# 4 Overenie na príkladoch

**Unit testy.** Model overuje 34 testov osoby A na ručne navrhnutej sieti
(`tests/data/toy_gtfs/`, 9 zastávok, 4 linky, spoje každých 10 min). Pre 16 scenárov sú
f, g a porušenia vypočítané ručne v `tests/data/toy_gtfs/README.md`:

- priama trasa v smere aj proti smeru obojsmernej linky,
- prestup na tej istej zastávke (iba τ = 60 s) a prestup s chôdzou 222 m,
- trasa iba pešo,
- porušenie O1 (štart 3,3 km od zastávky, g = f + 200), O5 (prestup 1 241 m) a O6
  (4 prestupy; príchod po t₀ + 3 h),
- spoj po polnoci (24:05),
- nedekódovateľné prípady: O2 (opačný smer jednosmernej linky, neznáma linka alebo
  zastávka), O4 (sobotná linka v utorok, zrušená služba vo sviatok) a O3 (posledný
  spoj pred t₀).

Ďalšie testy overujú načítanie GTFS a kalendár, pešiu vzdialenosť, počítadlo
vyhodnotení, inštancie a baseline (30 testov osoby B) a operátory okolia (51 testov,
kapitola 7). Celkovo `pytest` spustí 115 testov a všetky prechádzajú.

**Príklady na reálnych dátach.** Skript `scripts/demo_examples.py` ohodnotí päť ručne
zostavených kandidátov v utorok 24. 11. 2026 s odchodom o 7:30 a vypíše itinerár s
názvami zastávok, časmi, linkami a chôdzou. Úplný výpis je v
`results/demo_examples.md`. Štart a cieľ ležia na súradniciach zastávok, preto je
chôdza 0 m okrem prípadov (c) a (d).

| trasa | kandidát | vypočítané | z cestovného poriadku | f / g [min] | porušenia |
|---|---|---|---|---|---|
| (a) priama | 93 Hlavná stanica → Jiráskova | odchod 7:30:00, príchod 7:43:00 | [doplniť z dpb.sk / imhd.sk] | 13,00 / 13,00 | – |
| (b) 1 prestup | 93 Hlavná stanica → Zochova, 31 Zochova → Lanfranconi | 93: 7:30:00 → 7:35:00; čakanie 3,75 min (vrátane τ); 31: 7:38:45 → 7:44:00 | [doplniť] | 19,00 / 19,00 | – |
| (c) iba pešo | Hodžovo nám. → Zochova | 461 m, 5,92 min | [doplniť: vzdialenosť z mapy] | 5,92 / 5,92 | – |
| (d) neprípustná | štart pri Hlavnej stanici, 93 až z Hodžovho nám. → Jiráskova | chôdza 1 404 m (> 800 m); 93: 7:50:00 → 7:59:00 | [doplniť] | 29,00 / 229,00 | O1 |
| (e) nedekódovateľná | 93 Jiráskova → Hlavná stanica z nástupišťa v smere do Petržalky | linka v tomto smere na Hlavnú stanicu nejde | – | ∞ / ∞ | O2 |

Výsledky zodpovedajú formulácii. V prípade (b) je prestup na tom istom nástupišti,
takže sa pripočíta iba τ = 60 s a cestujúci čaká na prvý spoj linky 31 po 7:36:00.
f = 19 min sa skladá zo 14 min cesty a penalizácie α = 5 min za jeden prestup.
V prípade (d) je chôdza 1 404 m dlhšia ako d_max = 800 m, preto g = f + λ = 29 + 200 =
229 min. Kandidát ostáva dekódovateľný a porovnateľný. V prípade (e) dekóder nenájde
spoj, lebo výstup neleží za nástupom v smere jazdy linky, a vráti f = g = ∞.

[doplniť po ručnom overení: či sa časy odchodov a príchodov zhodujú s cestovným
poriadkom linky 93 a 31 na dpb.sk / imhd.sk a či vzdialenosť v (c) zodpovedá meraniu
na mape.]
