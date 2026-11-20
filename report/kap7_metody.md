# 7 Navrhované metódy

**Skúsenosti z implementácie modelu** (`results/bench.md`, `results/baselines_summary.md`):

- **Vyhodnotenie je lacné.** Jedno `ohodnot` trvá v priemere 36 µs (10 000 náhodných
  kandidátov). Rozpočet 1 000 vyhodnotení teda trvá približne 0,04 s. Drahšie je
  vytvorenie kandidáta: `nahodny_kandidat` potrebuje 323 µs, operátor okolia
  0,03 – 0,5 ms. Väčšinu času zaberie hľadanie zastávok v okolí a liniek, ktoré cez ne
  idú, preto sa oplatí odpovede cestovného poriadku kešovať (ako `Pamat` od B).
- **Obmedzenia sa ťažko dodržia náhodne.** Iba 7,2 % náhodných kandidátov je
  prípustných (pri dlhých trasách 2,0 %) a 66,5 % je nedekódovateľných. Najčastejšie sa
  porušuje O3 (66,5 %): linka v daný deň premáva, ale v časovom okne nemá spoj. Ďalej
  nasledujú O1 (25,3 %) a O6 (15,7 %). Cielená zmena dobrého kandidáta je preto
  výhodnejšia ako generovanie od nuly.
- **Reprezentácia má prirodzené okolie.** Šesť operátorov okolia (`neighborhood.py`)
  mení kandidáta v malom kroku a nikdy neporuší O2 (overené na 12 000 volaniach).
  Z dekódovateľného kandidáta vznikne v 90,3 % prípadov opäť dekódovateľný sused a
  v 33,0 % sused s menším g. Operátory však často nie sú použiteľné: v 33,2 % volaní
  vrátia None. Najčastejšie ide o `pridaj_prestup` pri kandidátovi so 4 úsekmi a
  o `vymen_linku`, keď z tej istej zastávky na ten istý výstup nejde iná linka.
- **Účelová funkcia má plošiny a skoky.** Veľa kandidátov vedie na ten istý spoj
  (rovnaké f). Malá zmena, napr. o 1 min neskorší príchod na zastávku, naopak znamená
  čakanie na ďalší spoj.
- **Baseline.** Greedy je rýchly, ale krátkozraký: pri dlhých trasách (D) je prípustný
  iba v 61 % inštancií. Náhodné hľadanie je pri D prípustné v 56 % behov a jeho
  výsledok silno závisí od seedu (σ f = 19,0 min).

Obe metódy budú používať rovnaký model, operátory okolia a **rovnaký rozpočet 1 000
vyhodnotení** `ohodnot` na inštanciu ako náhodné hľadanie. Porovnanie s baseline tak
bude férové.

## 7.1 Iteratívne vylepšovanie s náhodnými reštartmi a premenlivým okolím

**Princíp.** Z aktuálneho kandidáta sa vygeneruje vzorka susedov cez operátory okolia.
Ak je najlepší sused aspoň taký dobrý ako aktuálny kandidát (podľa g), metóda sa
presunie k nemu. Ak dlhšie nenastane zlepšenie, metóda začne odznova z nového
kandidáta. Uchováva sa najlepší kandidát zo všetkých behov.

**Prečo je vhodná.** Vyhodnotenie je lacné (36 µs) a reprezentácia má prirodzené
okolie. Z dekódovateľného kandidáta sa lokálnymi zmenami ľahko dostane k lepšiemu
riešeniu: napr. `odober_prestup` zlepší g v 97,6 % prípadov, keď je použiteľný.
Neprípustné kandidáty netreba zahadzovať, lebo g ich prirodzene usporiada.

**Potrebné úpravy pre našu úlohu.**

- *Vzorkované okolie.* Úplné okolie je veľké (stovky zastávok a liniek v dosahu),
  preto sa použije `susedia(k, …, limit = 10 – 20)`. Operátory sa striedajú náhodne,
  čo zodpovedá premenlivému okoliu.
- *Akceptácia rovnako dobrých susedov* (g′ ≤ g), aby metóda prešla cez plošiny, kde
  veľa kandidátov vedie na ten istý spoj.
- *Reštart po N vyhodnoteniach bez zlepšenia* (N ≈ 100) kvôli skokom vo funkcii:
  zmeškaný spoj znamená čakanie celý interval a lokálna zmena to často nenapraví.
- *Štart.* Prvý beh začne z výsledku greedy (2 vyhodnotenia), ďalšie z
  `nahodny_kandidat`. Kandidát s g = ∞ sa nahradí ďalším, lebo susedia
  nedekódovateľného kandidáta sú zväčša tiež nedekódovateľní.
- *Rozpočet.* Každé volanie `ohodnot`, aj pri reštarte, sa ráta do rozpočtu 1 000.

**Parametre a ukončenie.** Veľkosť vzorky susedov, N pre reštart a pravdepodobnosti
operátorov sa nastavia na časti inštancií. Metóda skončí po minutí rozpočtu.

## 7.2 Genetický algoritmus s reprezentáciou premenlivej dĺžky

**Princíp.** Populácia kandidátov sa vyvíja selekciou, krížením a mutáciou.
Najlepší jedinci prechádzajú do ďalšej generácie (elitizmus).

**Prečo je vhodný.** Plocha g je multimodálna: medzi štartom a cieľom vedie viac
dobrých trás rôznymi časťami mesta (napr. električkou cez centrum alebo autobusom
po obchvate). Populácia ich pokryje naraz, čím sa zníži závislosť od jedného
počiatočného bodu. Náhodné hľadanie má pri D σ f = 19 min a greedy tam v 39 %
inštancií skončí neprípustne. Kríženie môže spojiť dobrý začiatok jednej trasy
s dobrým koncom inej.

**Potrebné úpravy pre našu úlohu.**

- *Inicializácia.* Populácia 30 – 50 jedincov z `nahodny_kandidat` a jeden greedy
  jedinec. Nedekódovateľní sa pri inicializácii nahradia (66,5 % náhodných kandidátov
  má g = ∞). Populácia sa doplní aj kratšími kandidátmi, lebo 91 % náhodných kandidátov
  má 4 úseky.
- *Selekcia.* Turnajová selekcia (veľkosť turnaja 2 – 3) podľa g. Je robustná voči
  hodnotám ∞ a voči veľkým rozdielom medzi prípustnými (g < 200) a neprípustnými
  (g > 200) jedincami.
- *Kríženie pre premenlivú dĺžku v prestupnom bode.* Potomok dostane úseky rodiča 1 po
  výstup a, ku ktorému existuje nástup b rodiča 2 do d_prestup = 400 m, a za ním zvyšok
  rodiča 2 od b. Takto zostane prestup pešo dosiahnuteľný (O5) a každý prevzatý úsek
  spĺňa O2.
- *Oprava potomka.* Ak má potomok viac ako 4 úseky, zlúčia sa úseky cez
  `odober_prestup`, prípadne sa skráti. Ak oprava neuspeje, potomok ostane
  neprípustný a penalizuje ho g.
- *Mutácia.* Operátor okolia (`nahodny_sused`) s pravdepodobnosťou p_m. Operátory
  zachovávajú O2, takže mutácia nikdy nevytvorí nekonzistentný gén.
- *Ochrana proti predčasnej konvergencii.* Duplicitné genotypy (rovnaký zoznam úsekov)
  sa v populácii nahradia novými náhodnými jedincami.

**Parametre a ukončenie.** Populácia 40, elitizmus 1 – 2 jedinci, p_m približne 0,2 až
0,3. Pri rozpočte 1 000 vyhodnotení to zodpovedá približne 25 generáciám. Rozpočet sa
počíta cez `pocet_vyhodnoteni`, rovnako ako pri baseline.
