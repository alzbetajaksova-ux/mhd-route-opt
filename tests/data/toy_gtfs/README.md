# Toy GTFS – malá testovacia sieť

Ručne navrhnutá sieť 9 zastávok s reálnymi súradnicami z GTFS DPB (centrum
Bratislavy), 4 linky, 61 spojov. CSV súbory vytvára `generuj.py` (po úprave siete
ho spusti znova: `python tests/data/toy_gtfs/generuj.py`). Sieť používajú A, B aj C.

## Zastávky

| stop_id | názov | lat | lon |
|---|---|---|---|
| 01 | Hlavná stanica | 48.157543 | 17.106771 |
| 02 | Račianske mýto | 48.158001 | 17.120529 |
| 03 | Trnavské mýto | 48.157486 | 17.126970 |
| 04 | Blumentál | 48.153374 | 17.118761 |
| 05 | Americké nám. | 48.150867 | 17.117905 |
| 06 | Hodžovo nám. | 48.148163 | 17.108303 |
| 07 | Poštová | 48.146641 | 17.108572 |
| 08 | Most SNP | 48.139763 | 17.105650 |
| 09 | Krížna | 48.154678 | 17.123686 |

`stop_id` majú úvodnú nulu zámerne: ak sa ID nečítajú ako `str`, z „01“ sa stane 1.

## Linky a cestovný poriadok

Všetky spoje premávajú pravidelne každých 10 min (12 spojov, 7:xx – 8:xx), aby sa
čakanie dalo prepočítať ručne. Čas pri zastávke = začiatok spoja + posun.

| linka | služba | smer | zastávky (posun v min) | začiatky |
|---|---|---|---|---|
| 1 | PD | 0 | 01 (0) → 02 (4) → 03 (7) | 7:00, 7:10, …, 8:50 |
| 1 | PD | 1 | 03 (0) → 02 (3) → 01 (7) | 7:05, 7:15, …, 8:55 |
| 2 | PD | 0 | 02 (0) → 04 (3) → 05 (5) → 07 (9) → 08 (13) | 7:05, 7:15, …, 8:55 |
| 3 | PD | 0 | 06 (0) → 01 (6) | 7:05, …, 8:55 **a 24:05** |
| 4 | SO | 0 | 03 (0) → 09 (2) → 05 (5) | 7:00, 7:10, …, 8:50 |

`trip_id` = `{linka}_{smer}_{HHMM začiatku}`, napr. `2_0_0705`, `3_0_2405`.

Služby (`calendar.txt`, platnosť 16. 11. – 31. 12. 2026): **PD** = po – pi,
**SO** = sobota. Výnimka (`calendar_dates.txt`): **17. 11. 2026** (utorok, sviatok)
je PD zrušená (typ 2) a SO pridaná (typ 1).

Referenčné dátumy: po 16. 11. (PD), ut 17. 11. (iba SO – sviatok), so 21. 11. (SO),
ne 22. 11. (nič), ut 24. 11. (PD), ne 15. 11. (nič – pred začiatkom platnosti).

## Prvky siete a na čo slúžia

| prvok | test |
|---|---|
| linka 1 jazdí oboma smermi | O2: 01 → 03 aj 03 → 01 sa dá; `zastavky_za('1', '02')` = {03, 01} |
| linka 2 jazdí iba jedným smerom | O2: 08 → 02 je nedekódovateľný |
| zastávka 02 na linkách 1 aj 2 | prestup bez chôdze (iba `min_prestup` 60 s) |
| 07 Poštová (l. 2) – 06 Hodžovo nám. (l. 3): 221,54 m | prestup s chôdzou (< 400 m) |
| 08 Most SNP (l. 2) – 06 Hodžovo nám. (l. 3): 1 240,92 m | porušenie O5 (> 400 m) |
| linka 4 iba v sobotu | O4: v utorok 24. 11. nedekódovateľný |
| výnimka 17. 11. | aktívne služby: iba SO; linka 1 nejde, linka 4 ide |
| spoj `3_0_2405` (24:05 → 24:11) | časy po polnoci (24:05:00 = 86 700 s), horizont O6 |
| posledné spoje okolo 9:00 | O3: spoj v deň premáva, ale nie v časovom okne |

## Pešie vzdialenosti (ručne)

Pešia vzdialenosť = haversine (R = 6 371 000 m) × 1,3; čas = ceil(d / 1,3) s.

| úsek | pešia vzdialenosť | čas chôdze |
|---|---|---|
| 07 ↔ 06 | 221,54 m | 171 s |
| 08 ↔ 06 | 1 240,92 m | 955 s |
| Patrónka (48.168411, 17.076723) → 01 | 3 295,77 m | 2 536 s |

## Očakávané výsledky (parametre podľa `Parametre()`)

Ak nie je uvedené inak: dátum po 16. 11. 2026, t0 = 7:00:00 (25 200 s), štart a cieľ
ležia presne na súradniciach uvedených zastávok (chôdza 0 m).

| # | prípad | štart → cieľ | kandidát | priebeh | f | g | porušenia |
|---|---|---|---|---|---|---|---|
| 1 | priama trasa | 01 → 03 | (1: 01→03) | `1_0_0700` 7:00 → 7:07 | 7,0 | 7,0 | – |
| 2 | prestup na tej istej zastávke | 01 → 08 | (1: 01→02), (2: 02→08) | 02 o 7:04 + 60 s = 7:05 → `2_0_0705` (presne stihne) → 08 o 7:18 | 18 + 5 = 23,0 | 23,0 | – |
| 3 | prestup s chôdzou | 02 → 01 | (2: 02→07), (3: 06→01) | 07 o 7:14 + 171 s + 60 s = 7:17:51 → čaká na `3_0_0725` → 01 o 7:31 | 31 + 5 = 36,0 | 36,0 | – |
| 4 | iba pešo | 07 → 06 | [] | chôdza 221,54 m, 171 s | 2,85 | 2,85 | – |
| 5 | O1 | Patrónka → 03 | (1: 01→03) | príchod na 01 o 7:42:16 → `1_0_0750` → 03 o 7:57 | 57,0 | 257,0 | O1 |
| 6 | O5 | 02 → 01 | (2: 02→08), (3: 06→01) | 08 o 7:18 + 955 s + 60 s = 7:34:55 → `3_0_0735` → 01 o 7:41 | 41 + 5 = 46,0 | 246,0 | O5 |
| 7 | O6 – počet prestupov | 01 → 08 | (1: 01→02), (2: 02→04), (2: 04→05), (2: 05→07), (2: 07→08) | 5 úsekov, P = 4; príchod 08 o 7:48 | 48 + 20 = 68,0 | 268,0 | O6 |
| 8 | O6 – horizont | 06 → 01, t0 = 21:10 (76 200 s) | (3: 06→01) | `3_0_2405` odchod 86 700 ≤ t0+H = 87 000, príchod 87 060 > 87 000 | 181,0 | 381,0 | O6 |
| 9 | spoj po polnoci | 06 → 01, t0 = 23:50 (85 800 s) | (3: 06→01) | `3_0_2405` 24:05 → 24:11 (87 060 s) | 21,0 | 21,0 | – |
| 10 | opačný smer (obojsmerná linka) | 03 → 01 | (1: 03→01) | `1_1_0705` 7:05 → 7:12 | 12,0 | 12,0 | – |
| 11 | O2 – opačný smer jednosmernej linky | 08 → 02 | (2: 08→02) | nedekódovateľný | inf | inf | O2 |
| 12 | O4 – sobotná linka v utorok | 03 → 05, ut 24. 11. | (4: 03→05) | linka v ten deň nepremáva → nedekódovateľný | inf | inf | O2 |
| 13 | sobotná linka v sobotu | 03 → 05, so 21. 11. | (4: 03→05) | `4_0_0700` 7:00 → 7:05 | 5,0 | 5,0 | – |
| 14 | výnimka – sviatok | 01 → 03, ut 17. 11. | (1: 01→03) | PD zrušená → nedekódovateľný | inf | inf | O2 |
| 15 | výnimka – sviatok | 03 → 05, ut 17. 11. | (4: 03→05) | SO pridaná → `4_0_0700` | 5,0 | 5,0 | – |
| 16 | O3 – mimo časového okna | 01 → 03, t0 = 9:00 (32 400 s) | (1: 01→03) | posledný spoj 8:50 → nedekódovateľný | inf | inf | O3 |

Pri nedekódovateľnom kandidátovi: `pripustny = False`, `dekodovatelny = False`.
Porušenie O4 (linka v daný deň nepremáva) sa podľa kontraktu hlási ako `'O2'`
(„linka v ten deň nespojí tieto zastávky v tomto smere“). `'O3'` znamená, že spoj
v daný deň existuje, ale nie v okne [čas príchodu, t0 + H].

Počítadlo: po N volaniach `ohodnot` (aj nedekódovateľných) je `pocet_vyhodnoteni == N`.

## Očakávané výsledky metód `CestovnyPoriadok`

| volanie | výsledok |
|---|---|
| aktívne služby 16. 11. / 17. 11. / 21. 11. / 22. 11. / 15. 11. | {PD} / {SO} / {SO} / {} / {} |
| `linky_na_zastavke('02', 16. 11.)` | {1, 2} |
| `linky_na_zastavke('03', 16. 11.)` / `(…, 21. 11.)` | {1} / {4} |
| `zastavky_za('1', '01', 16. 11.)` | {02, 03} |
| `zastavky_za('1', '02', 16. 11.)` | {03, 01} (oba smery) |
| `zastavky_za('2', '08', 16. 11.)` | {} (konečná) |
| `zastavky_za('4', '03', 16. 11.)` / `(…, 21. 11.)` | {} / {09, 05} |
| `zastavky_v_okoli(súradnice 07, 400)` | [('07', 0,0), ('06', 221,54)] |
| `najblizsi_odchod('1', '01', '03', 25 200, 16. 11.)` | ('1_0_0700', 25 200, 25 620) |
| `najblizsi_odchod('1', '01', '03', 25 201, 16. 11.)` | ('1_0_0710', 25 800, 26 220) |
| `najblizsi_odchod('2', '08', '02', 0, 16. 11.)` | None |
