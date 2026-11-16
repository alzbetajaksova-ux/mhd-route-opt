# 5 Baseline

Obe metódy hodnotia kandidátov výhradne cez `Hodnotitel.ohodnot`, takže rozpočet
(počet vyhodnotení) je férovo merateľný aj pre metódy v 3. fáze. Kandidátov
porovnávajú podľa g: prípustný kandidát má g < 200 a neprípustný g > 200, preto
prípustný vždy vyhrá.

**Náhodné hľadanie** (`baselines/random_search.py`). Funkcia `nahodny_kandidat`
skladá trasu konštruktívne:

1. S pravdepodobnosťou 0,05 vráti trasu iba pešo.
2. Inak vyberie náhodnú zastávku do 800 m od štartu, náhodnú linku, ktorá na nej
   v daný deň zastavuje, a náhodnú zastávku za nástupom v smere jazdy
   (`zastavky_za`).
3. Ak je výstup do 800 m od cieľa, s pravdepodobnosťou 0,5 skončí. Inak prestúpi
   na náhodnú zastávku do 400 m a pokračuje, najviac do 4 úsekov.

Konštrukcia tak zaručí O2, O5 a O1 pri štarte. Porušené môžu ostať O1 pri cieli
(po 4 úsekoch je kandidát stále ďaleko) a O6. Kandidát môže byť aj
nedekódovateľný (O3): linka v daný deň premáva, ale v okne [príchod cestujúceho,
t₀ + 3 h] nemá spoj. Typicky ide o nočné linky (N…) cez deň a o zriedkavé linky.

`nahodne_hladanie` generuje kandidátov, kým neminie rozpočet 1 000 vyhodnotení,
a vráti najlepšieho podľa g:

- **Neprípustní kandidáti** sa nezahadzujú. Ak sa nenájde žiadny prípustný,
  vráti sa najmenej porušujúci s príznakom `pripustny = False`.
- **Nedekódovateľní kandidáti** (g = ∞) sa iba započítajú.

Okrem riešenia metóda vráti počty prípustných, neprípustných a nedekódovateľných
kandidátov a početnosť porušení. Na reálnych dátach je nedekódovateľných 57 – 77 %
kandidátov a prípustných iba 2 – 24 % podľa skupiny. Väčšinu rozpočtu teda
spotrebujú kandidáti, ktorí nikdy nemôžu vyhrať. Toto je hlavný argument pre
metódy v 3. fáze, ktoré budú meniť už dobrého kandidáta namiesto generovania od
nuly.

**Greedy** (`baselines/greedy.py`) postupuje po úsekoch z aktuálnej polohy a
času:

1. Preskúša všetky zastávky v dosahu (800 m zo štartu, 400 m pri prestupe),
   všetky ich linky (okrem práve použitej) a všetky zastávky za nástupom.
2. Pre každú trojicu nájde najbližší spoj rovnako ako dekóder, vrátane 60 s na
   prestup.
3. Vyberie trojicu s najmenším odhadom príchodu do cieľa, pričom odhad je príchod
   na výstup plus chôdza z výstupu do cieľa.

Skončí, keď je výstup do 800 m od cieľa, po 4 úsekoch alebo keď už nejde žiadny
spoj. Výsledok ohodnotí a porovná s trasou iba pešo; vráti lepšiu podľa g.
Greedy je deterministický a jeho kandidát je vždy dekódovateľný, lebo spoje hľadá
rovnako ako dekóder. Neprípustný však byť môže: odhad je krátkozraký a cestujúci
môže skončiť na zastávke, odkiaľ ďalej vedú iba nočné linky, ďaleko od cieľa (O1)
alebo s príchodom po t₀ + 3 h (O6). Vtedy vyhrá trasa iba pešo, ak je prípustná,
inak sa vráti greedy trasa s príznakom. Takto skončilo 7 zo 60 inštancií, všetky
v skupine D. Na jednu inštanciu spotrebuje 2 vyhodnotenia a rádovo stovky až
tisíce volaní `najblizsi_odchod`, čo trvá asi 5 ms.
