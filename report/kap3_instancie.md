# 3 Inštancie

Inštancia je požiadavka cestujúceho: štart, cieľ, dátum a čas odchodu t₀. Sadu 60
inštancií vytvára `generuj_instancie` (`src/mhd/instances.py`, skript
`scripts/make_instances.py`) s pevným seedom 42 a ukladá ju do `data/instances.json`.
Okrem vstupných údajov súbor obsahuje vzdušnú vzdialenosť štart–cieľ, najbližšiu
zastávku a počet zastávok do 800 m pri štarte aj cieli.

**Body.** Bod štartu alebo cieľa vznikne zo súradníc náhodnej zastávky, ktorú
obsluhuje aspoň jedna linka v dňoch inštancií. Bod sa posunie o 100 – 600 m
náhodným smerom, aby neležal presne na zastávke. Prijme sa iba vtedy, ak má aspoň
jednu zastávku do d_max = 800 m pešej vzdialenosti, takže obmedzenie O1 je pri
každej inštancii splniteľné.

**Skupiny.** Dvojice štart–cieľ sa delia podľa vzdušnej vzdialenosti:

- 6 krátkych (K, 1 – 3 km),
- 8 stredných (S, 3 – 7 km),
- 6 dlhých (D, nad 7 km).

Pri každej dvojici sa cieľ losuje opakovane, kým vzdialenosť nepadne do pásma.
V sade vyšli vzdialenosti 1,3 – 2,6 km (K), 3,3 – 6,8 km (S) a 7,7 – 17,3 km (D).

**Časy odchodu.** Každá z 20 dvojíc sa použije v troch časoch:

- utorok 24. 11. 2026 o 7:30 (špička),
- utorok 24. 11. 2026 o 13:00 (mimo špičky),
- sobota 28. 11. 2026 o 22:00 (riedke a nočné spoje).

Spolu vznikne 60 inštancií s id v tvare `S03-ut0730`. Dátumy ležia v platnosti
GTFS (od 16. 11. 2026).

**Reprodukovateľnosť.** Rovnaký seed a rovnaký GTFS dajú vždy rovnaké inštancie.
Testy (`tests/test_instances.py`) to overujú na malej testovacej sieti s
prispôsobenými pásmami. Kontrolujú aj počet inštancií, vzdialenosti v pásmach,
zastávku do d_max pri každom bode a zhodu po uložení a načítaní JSON.
