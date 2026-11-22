# 2 Implementácia modelu

**Načítanie GTFS a indexy.** Trieda `CestovnyPoriadok` (`src/mhd/gtfs.py`) načíta zo
zafixovaného GTFS DPB (feed 6. 11. 2026, platnosť od 16. 11. 2026; 90 liniek, 1 375
zastávok, 35 932 spojov, 712 583 záznamov `stop_times`) súbory `stops`, `routes`,
`trips`, `stop_times`, `calendar` a `calendar_dates` cez pandas; identifikátory sa
čítajú ako reťazce (inak by sa z ID „01“ stalo 1). Časy HH:MM:SS sa prevedú na
sekundy od polnoci prevádzkového dňa, hodnoty nad 24:00:00 sa ponechajú. Aktívne
služby pre dátum sa určia z dňa v týždni a rozsahu platnosti v `calendar.txt` a
výnimiek z `calendar_dates.txt` (1 = pridaná, 2 = zrušená) a kešujú sa podľa dátumu.
Analýza z 1. fázy počítala so staršou verziou feedu (36 354 spojov), model používa
novšiu verziu s 35 932 spojmi.
Pri načítaní sa vytvoria indexy: pre dvojicu (linka, zastávka) zoradený zoznam
odchodov (čas, spoj, poradie zastávky), pre spoj slovník zastávka → (poradie,
príchod) a pre (linka, zastávka) a službu množina zastávok za ňou v smere jazdy.
Hotové indexy sa uložia do `data/cache/` (pickle). Zastávky v okolí bodu (do d_max
od štartu a cieľa) hľadá priestorový index `PriestorovyIndex` (BallTree s
haversinovou metrikou zo scikit-learn).

**Dekóder.** Kandidát je zoznam úsekov (linka, nástup, výstup). `Hodnotitel.ohodnot`
(`src/mhd/evaluate.py`) postupne pripočíta chôdzu zo štartu na prvú nástupnú zastávku,
pre každý úsek nájde najbližší odchod a pripočíta čakanie a jazdu, pri prestupe
chôdzu medzi zastávkami (0 m na tej istej zastávke) a min. čas na prestup τ = 60 s a
nakoniec chôdzu do cieľa. Najbližší odchod hľadá binárne vyhľadávanie prvého odchodu
≥ čas príchodu cestujúceho; od neho sa prechádzajú ďalšie odchody, kým sa nenájde
spoj aktívny v daný deň, ktorý neskôr (vyššie poradie) zastavuje na výstupnej
zastávke. Pešia vzdialenosť je haversinova vzdialenosť × 1,3, čas chôdze je
vzdialenosť / 1,3 m/s zaokrúhlená nahor na sekundy. Výsledkom je itinerár z častí
chôdza / čakanie / jazda s časmi, linkou a `trip_id`.

**Výpočet f a g a kontrola obmedzení.** f(x) = (príchod − t₀)/60 + 5 · P [min],
g(x) = f(x) + 200 · V(x), kde V je počet porušených obmedzení spomedzi O1, O5, O6
(každé sa ráta najviac raz). O1 sa kontroluje na prvej a poslednej chôdzi (≤ 800 m),
O5 pri každom prestupe (≤ 400 m), O6 na počte prestupov (≤ 3) a príchode
(≤ t₀ + 3 h). O2 – O4 rieši dekóder: ak pre úsek neexistuje spoj s odchodom do
t₀ + H, kandidát je nedekódovateľný, f = g = ∞ a porušenie je `O2` (linka v ten deň
nespojí zastávky v tomto smere – aj keď vôbec nepremáva, O4) alebo `O3` (spoj
existuje, ale nie v časovom okne). Trasa iba pešo má f = čas chôdze a kontroluje sa
na nej iba O6. Každé volanie zvýši počítadlo `pocet_vyhodnoteni`.

**Zjednodušenia.** Spoje predchádzajúceho prevádzkového dňa s časmi po polnoci sa
neuvažujú. Pešia vzdialenosť sa neodvodzuje z uličnej siete, ale z koeficientu
zachádzky. Ak spoj zastavuje na tej istej zastávke viackrát (okružné linky), použije
sa jej posledný výskyt.

**Overenie a rýchlosť.** Model je overený 34 unit testami na ručne navrhnutej sieti
(9 zastávok, 4 linky) s ručne vypočítanými hodnotami f a g pre 16 scenárov (priama
trasa, prestup bez chôdze aj s chôdzou, iba pešo, porušenia O1 – O6, výnimka v
kalendári, spoj po polnoci). Na reálnych dátach (Python 3.15, pandas 3.1,
notebook s procesorom Intel 11. generácie) trvá načítanie z CSV 3,7 – 4,4 s (prvé spustenie 7,7 s), z cache 0,3 s; jedno
vyhodnotenie kandidáta s dvoma úsekmi trvá v priemere 12 µs (10 000 opakovaní),
jedno vyhľadanie najbližšieho odchodu približne 5 µs a hľadanie zastávok do 800 m
od bodu približne 140 µs.
