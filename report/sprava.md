TECHNICKÁ UNIVERZITA V KOŠICIACH
FAKULTA ELEKTROTECHNIKY A INFORMATIKY
Moderné prístupy v optimalizácii · Zadanie 2 – odovzdávka 2

# Implementácia modelu a baseline pre optimalizáciu cesty MHD

Variant 1B – Optimalizácia cesty MHD ·
Riešitelia: [Meno Priezvisko A], [Meno Priezvisko B], [Meno Priezvisko C] ·
Vyučujúci: Ing. Ján Magyar, PhD.

Pre štart o, cieľ d, dátum a čas odchodu t₀ hľadáme trasu MHD v Bratislave (0 – 4 jazdy
a chôdza) s najkratším celkovým časom penalizovaným za prestupy. Kód, návod na
spustenie (`README.md`) a všetky výsledky sú v priloženom repozitári `mhd-route-opt`.

## 1 Reakcia na spätnú väzbu

Pripomienky k odovzdávke 1 sme zapracovali do opravenej analýzy, ktorá je priložená
k odovzdávke. Model z nej vychádza takto:

1. **d_tr a τ.** Obe hodnoty opisujú ten istý prestup: d_tr = 400 m je jeho pešia časť a
   τ = 1 min je časová rezerva. Čas prestupu je c · dist(a_i, b_{i+1}) / v + τ; na tej
   istej zastávke sa pripočíta iba τ. Limity d_max = 800 m (≈ 10 min) a d_tr = 400 m
   (≈ 5 min) sa porovnávajú so vzdialenosťou po uliciach, t. j. so vzdušnou
   vzdialenosťou × c = 1,3.
2. **Voľba α a λ.** α = 5 min zodpovedá približne najdlhšiemu povolenému pešiemu
   presunu pri prestupe. Citlivosť výsledkov na α overíme v 3. fáze pre
   α ∈ {0, 3, 5, 10}. λ sme zvýšili zo 60 na 200 min. Najhoršia prípustná trasa má
   f ≤ H + α · K_max = 180 + 15 = 195 min, takže prípustný kandidát je vždy lepší ako
   neprípustný. Pri λ = 60 by neprípustný kandidát s f = 20 (g = 80) vyhral nad
   prípustným s f = 100.
3. **Čo sa ráta do V(x).** Iba porušenia O1, O5 a O6. O2 zaručuje konštrukcia kandidáta,
   O3 a O4 dekóder. Kandidát, pre ktorého neexistuje nadväzujúci spoj, je
   nedekódovateľný a má g = ∞.

## 2 Implementácia modelu

**Dáta.** `CestovnyPoriadok` (`src/mhd/gtfs.py`) načíta zafixovaný GTFS DPB (feed
6. 11. 2026, platnosť od 16. 11. 2026; 90 liniek, 1 375 zastávok, 35 932 spojov).
Identifikátory sa čítajú ako reťazce a časy sa prevedú na sekundy od polnoci, aj nad
24:00:00. Aktívne služby pre dátum sa určia z `calendar.txt` a výnimiek
v `calendar_dates.txt`. Indexy obsahujú zoradené odchody pre dvojicu (linka,
zastávka), poradie zastávok každého spoja a zastávky dosiahnuteľné linkou v smere
jazdy. Ukladajú sa do `data/cache/`. Zastávky v okolí bodu hľadá BallTree s
haversinovou metrikou.

**Kandidát a dekóder.** Kandidát je zoznam 0 – 4 úsekov (linka, nástup, výstup);
[] znamená trasu iba pešo. `Hodnotitel.ohodnot` (`src/mhd/evaluate.py`) postupne
pripočíta chôdzu na prvú zastávku a pre každý úsek binárnym vyhľadávaním nájde prvý
spoj aktívny v daný deň, ktorý odchádza po príchode cestujúceho a neskôr zastavuje
na výstupe. Pripočíta čakanie a jazdu, pri prestupe chôdzu a τ = 60 s a nakoniec
chôdzu do cieľa. Výsledkom je itinerár (chôdza / čakanie / jazda s časmi a `trip_id`).

**f, g a obmedzenia.** f = (príchod − t₀)/60 + 5 · P [min] a g = f + 200 · V, kde V je
počet porušených obmedzení z O1 (chôdza k prvej a od poslednej zastávky ≤ 800 m),
O5 (prestup ≤ 400 m) a O6 (≤ 3 prestupy, príchod ≤ t₀ + 3 h). Ak pre úsek neexistuje
spoj, kandidát je nedekódovateľný (f = g = ∞) s porušením `O2` (linka v ten deň
nespojí zastávky v tomto smere, vrátane O4) alebo `O3` (spoj nie je v časovom okne).
Každé volanie zvýši počítadlo `pocet_vyhodnoteni`, ktoré slúži na férový rozpočet
metód.

**Zjednodušenia.** Neuvažujú sa spoje predchádzajúceho dňa po polnoci. Pešia
vzdialenosť sa počíta zo zachádzky, nie z uličnej siete. Pri okružných linkách sa
použije posledný výskyt zastávky v spoji.

## 3 Inštancie

Sadu 60 inštancií generuje `scripts/make_instances.py` s pevným seedom 42 a ukladá ju do
`data/instances.json`. Bod štartu alebo cieľa je náhodná obsluhovaná zastávka posunutá
o 100 – 600 m náhodným smerom. Prijme sa iba vtedy, ak má zastávku do 800 m, takže O1
je vždy splniteľné. 20 dvojíc štart – cieľ sa delí podľa vzdušnej vzdialenosti:
6 krátkych (K, 1 – 3 km), 8 stredných (S, 3 – 7 km) a 6 dlhých (D, nad 7 km). Každá
dvojica sa použije v troch časoch: utorok 24. 11. 2026 o 7:30 (špička), utorok o 13:00
a sobota 28. 11. 2026 o 22:00 (riedke a nočné spoje).

## 4 Overenie na príkladoch

**Unit testy.** 34 testov osoby A overuje model na ručne navrhnutej sieti (9 zastávok,
4 linky). Pre 16 scenárov sú f a g vypočítané ručne: priama trasa v oboch smeroch,
prestup bez chôdze aj s chôdzou, iba pešo, porušenia O1, O5, O6, spoj po polnoci,
O2 (opačný smer), O4 (sobotná linka v utorok, sviatok) a O3. Spolu s testami
inštancií, baseline a operátorov okolia `pytest` spustí 115 testov a všetky
prechádzajú.

**Reálne dáta** (`scripts/demo_examples.py`, utorok 24. 11. 2026 o 7:30, úplný výpis
v `results/demo_examples.md`):

| trasa | kandidát | vypočítané | z cestovného poriadku | f / g [min] | porušenia |
|---|---|---|---|---|---|
| (a) priama | 93 Hlavná stanica → Jiráskova | 7:30:00 → 7:43:00 | [doplniť] | 13,00 / 13,00 | – |
| (b) 1 prestup | 93 Hlavná st. → Zochova, 31 Zochova → Lanfranconi | 7:30 → 7:35; 31: 7:38:45 → 7:44:00 | [doplniť] | 19,00 / 19,00 | – |
| (c) iba pešo | Hodžovo nám. → Zochova | 461 m, 5,92 min | [doplniť z mapy] | 5,92 / 5,92 | – |
| (d) neprípustná | 93 z Hodžovho nám., štart pri Hl. stanici | chôdza 1 404 m; 7:50 → 7:59 | [doplniť] | 29,00 / 229,00 | O1 |
| (e) nedekódovateľná | 93 Jiráskova → Hl. stanica proti smeru | spoj neexistuje | – | ∞ / ∞ | O2 |

V (b) sa prestupuje na tom istom nástupišti, preto sa pripočíta iba τ. f = 14 min
cesty + α = 5 min. V (d) je g = f + λ a kandidát ostáva porovnateľný, v (e) dekóder
vráti g = ∞. [doplniť po ručnom overení na dpb.sk / imhd.sk.]

## 5 Baseline

Obe metódy hodnotia kandidátov iba cez `ohodnot` a porovnávajú ich podľa g. Prípustný
kandidát má g < 200, neprípustný g > 200, preto prípustný vždy vyhrá.

**Náhodné hľadanie** (`baselines/random_search.py`). `nahodny_kandidat` skladá trasu
konštruktívne. S pravdepodobnosťou 0,05 vráti trasu iba pešo. Inak vyberie náhodnú
zastávku do 800 m od štartu, náhodnú linku, ktorá na nej v daný deň stojí, a náhodnú
zastávku za nástupom. Ak je výstup do 800 m od cieľa, s pravdepodobnosťou 0,5 skončí.
Inak prestúpi na zastávku do 400 m, najviac do 4 úsekov. Konštrukcia zaručí O2, O5 a O1
pri štarte. Porušené môže ostať O1 pri cieli a O6 a kandidát môže byť nedekódovateľný
(O3). Metóda vyhodnotí 1 000 kandidátov a vráti najlepšieho podľa g:

- **Neprípustní** sa nezahadzujú. Ak sa nenájde žiadny prípustný, vráti sa najmenej
  porušujúci s príznakom `pripustny = False`.
- **Nedekódovateľní** (g = ∞) sa iba započítajú.

**Greedy** (`baselines/greedy.py`) postupuje po úsekoch. Z aktuálnej polohy a času
preskúša všetky zastávky v dosahu (800 m zo štartu, 400 m pri prestupe), ich linky a
zastávky za nástupom. Vyberie trojicu s najmenším odhadom príchodu do cieľa, ktorý
je príchod na výstup plus chôdza do cieľa. Skončí do 800 m od cieľa, po 4 úsekoch
alebo keď už nejde žiadny spoj. Výsledok porovná s trasou iba pešo. Kandidát je vždy
dekódovateľný, ale môže byť neprípustný (O1, O6). Vtedy vyhrá trasa iba pešo, ak je
prípustná, inak sa vráti s príznakom.

## 6 Výsledky baseline

Greedy bežal na každej inštancii raz, náhodné hľadanie so seedmi 0 – 9 a rozpočtom
1 000 vyhodnotení. Priemerné f je iba z prípustných riešení a σ je smerodajná odchýlka
f cez seedy (`results/baselines_summary.md`).

| metóda | skupina | prípustné riešenia | priem. f [min] | σ f | priem. prestupy | čas behu [s] |
|---|---|---|---|---|---|---|
| greedy | K / S / D | 100 / 100 / 61 % | 24,0 / 52,0 / 82,4 | – | 0,06 / 0,42 / 1,55 | 0,003 – 0,005 |
| náhodné | K / S / D | 100 / 100 / 56 % | 24,9 / 60,7 / 97,7 | 0,9 / 9,7 / 19,0 | 0,04 / 0,37 / 1,58 | 0,19 – 0,22 |

Oproti mediánu náhodného hľadania je greedy lepší na 28 inštanciách, rovnaký na 26 a
horší na 6. Spotrebuje pritom 2 vyhodnotenia namiesto 1 000. Pri dlhých trasách však
v 7 z 18 prípadov skončí neprípustne, lebo krátkozraký výber ho zavedie na zastávky,
odkiaľ sa nedá rozumne pokračovať. Na krátkych trasách vyhrá približne v polovici
prípadov trasa iba pešo.

**Meranie modelu** (`scripts/bench_eval.py`, `results/bench.md`). Načítanie GTFS trvá
4,9 s z CSV a 0,3 s z cache. Jedno `ohodnot` trvá v priemere 36 µs na 10 000
náhodných kandidátoch, pričom 91 % z nich má 4 úseky. Prípustných je iba 7,2 %
kandidátov (K 14,3 %, S 5,8 %, D 2,0 %), neprípustných 26,2 % a nedekódovateľných
66,5 %. Najčastejšie sa porušuje O3 (66,5 % kandidátov), potom O1 (25,3 %) a O6
(15,7 %). Väčšinu rozpočtu náhodného hľadania teda spotrebujú kandidáti, ktorí nemôžu
vyhrať.

## 7 Navrhované metódy

Obe metódy využijú lacné vyhodnotenie (36 µs) a šesť operátorov okolia
(`src/mhd/neighborhood.py`): zmena nástupu, zmena výstupu, posun prestupu, výmena
linky, pridanie a odobratie prestupu. Operátory menia kandidáta v malom kroku a nikdy
neporušia O2 (0 porušení na 12 000 volaniach). Z dekódovateľného kandidáta vytvoria
dekódovateľného suseda v 90,3 % a zlepšujúceho suseda v 33,0 % prípadov. V 33,2 %
volaní však vrátia None, preto sa vyberajú náhodne s opakovaním (`nahodny_sused`).
Obe metódy dostanú **rovnaký rozpočet 1 000 vyhodnotení** ako náhodné hľadanie.

**7.1 Iteratívne vylepšovanie s náhodnými reštartmi a premenlivým okolím.** Z
aktuálneho kandidáta sa vygeneruje vzorka 10 – 20 susedov cez náhodne striedané
operátory. Metóda sa presunie k najlepšiemu susedovi, ak je aspoň taký dobrý podľa g.
*Prečo:* reprezentácia má prirodzené okolie a lokálne zmeny sú účinné, napr.
`odober_prestup` zlepší g v 97,6 % prípadov, keď je použiteľný. *Úpravy:*

- akceptácia rovnako dobrých susedov kvôli plošinám (veľa trás vedie na ten istý
  spoj),
- reštart po približne 100 vyhodnoteniach bez zlepšenia kvôli skokom vo funkcii
  (zmeškaný spoj znamená čakanie celý interval),
- štart z greedy riešenia, ďalšie reštarty z `nahodny_kandidat` s náhradou
  nedekódovateľných, lebo ich susedia sú tiež zväčša nedekódovateľní.

**7.2 Genetický algoritmus s reprezentáciou premenlivej dĺžky.** *Prečo:* plocha g je
multimodálna, lebo dobré trasy vedú rôznymi koridormi mesta. Populácia ich pokryje
naraz a zníži závislosť od počiatočného bodu: náhodné hľadanie má pri D σ = 19 min a
greedy tam v 39 % inštancií zlyhá. *Úpravy:*

- populácia 40 z `nahodny_kandidat` a jeden greedy jedinec, bez nedekódovateľných a
  doplnená o kratšie trasy,
- turnajová selekcia podľa g, robustná voči ∞,
- kríženie v prestupnom bode: úseky rodiča 1 po výstup, ku ktorému existuje nástup
  rodiča 2 do 400 m, a zvyšok rodiča 2; zachová O2 aj O5,
- oprava potomka s viac ako 4 úsekmi cez `odober_prestup`, inak penalizácia cez g,
- mutácia operátorom okolia (p_m ≈ 0,2 – 0,3),
- elitizmus 1 – 2 jedinci a nahrádzanie duplicitných genotypov proti predčasnej
  konvergencii.

Pri rozpočte 1 000 vyhodnotení to je približne 25 generácií.

## 8 Rozdelenie práce

| člen | práca |
|---|---|
| A – [meno] | kostra repozitára a kontrakt, testovacia sieť, načítanie GTFS a indexy, `geo.py` a priestorový index (prevzaté od B), dekóder a `ohodnot`, unit testy modelu, kapitola 2 |
| B – [meno] | generátor 60 inštancií, náhodná a greedy baseline, behy na inštanciách a súhrnné tabuľky, README, kapitoly 3, 5, 6 |
| C – [meno] | operátory okolia a ich testy, overené príklady na reálnych dátach, meranie modelu a operátorov, kapitoly 1, 4, 7 a 8, zloženie správy |

## Literatúra

1. MAGYAR, J. Moderné prístupy v optimalizácii: Úvod do optimalizácie [prednáška 1].
   Košice: TUKE, 2026.
2. DOPRAVNÝ PODNIK BRATISLAVA, a. s. Cestovný poriadok MHD v Bratislave (GTFS) [online].
   2026 [cit. 2026-10-31]. Dostupné na:
   https://data.bratislava.sk/datasets/aba12fd2cbac4843bc7406151bc66106/about
3. DELLING, D., PAJOR, T., WERNECK, R. F. Round-Based Public Transit Routing.
   Transportation Science. 2015, 49(3), 591–604.
4. TALBI, E.-G. Metaheuristics: From Design to Implementation. Hoboken: Wiley, 2009.
