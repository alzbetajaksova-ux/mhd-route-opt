# Overené príklady (scripts/demo_examples.py)

Utorok 24. 11. 2026, t₀ = 07:30:00. Vygenerované skriptom; stĺpce „z poriadku“ vypĺňa človek podľa dpb.sk / imhd.sk.

## (a) priama trasa: Hlavná stanica -> Jiráskova (Petržalka)

```
    07:30:00 – 07:30:00  chôdza     start -> Hlavná stanica  0 m
    07:30:00 – 07:43:00  linka  93  Hlavná stanica -> Jiráskova  (spoj 93009_02_107_32368)
    07:43:00 – 07:43:00  chôdza     Jiráskova -> ciel  0 m
f = 13,00 min, g = 13,00 min, prestupy = 0, chôdza = 0 m, porušenia = –, prípustný = True, dekódovateľný = True
```

## (b) 1 prestup: Hlavná stanica -> Lanfranconi (Mlynská dolina)

```
    07:30:00 – 07:30:00  chôdza     start -> Hlavná stanica  0 m
    07:30:00 – 07:35:00  linka  93  Hlavná stanica -> Zochova  (spoj 93009_02_107_32368)
    07:35:00 – 07:38:45  čakanie    Zochova  3.8 min
    07:38:45 – 07:44:00  linka  31  Zochova -> Lanfranconi  (spoj 31008_09_28_17789)
    07:44:00 – 07:44:00  chôdza     Lanfranconi -> ciel  0 m
f = 19,00 min, g = 19,00 min, prestupy = 1, chôdza = 0 m, porušenia = –, prípustný = True, dekódovateľný = True
```

## (c) iba pešo: Hodžovo nám. -> Zochova

```
    07:30:00 – 07:35:55  chôdza     start -> ciel  461 m
f = 5,92 min, g = 5,92 min, prestupy = 0, chôdza = 461 m, porušenia = –, prípustný = True, dekódovateľný = True
```

## (d) neprípustná (O1): nástup na Hodžovom nám., štart pri Hlavnej stanici

```
    07:30:00 – 07:48:01  chôdza     start -> Hodžovo nám.  1404 m
    07:48:01 – 07:50:00  čakanie    Hodžovo nám.  2.0 min
    07:50:00 – 07:59:00  linka  93  Hodžovo nám. -> Jiráskova  (spoj 93009_07_123_32372)
    07:59:00 – 07:59:00  chôdza     Jiráskova -> ciel  0 m
f = 29,00 min, g = 229,00 min, prestupy = 0, chôdza = 1404 m, porušenia = ['O1'], prípustný = False, dekódovateľný = True
```

## (e) nedekódovateľná (O2): linka 93 z Jiráskovej v opačnom smere

```
    07:30:00 – 07:30:00  chôdza     start -> Jiráskova  0 m
    linka 93 Jiráskova -> Hlavná stanica: v tomto smere nejde – nedekódovateľný
f = ∞ min, g = ∞ min, prestupy = 0, chôdza = 0 m, porušenia = ['O2'], prípustný = False, dekódovateľný = False
```

## Očakávané z cestovného poriadku vs. vypočítané

| trasa | úsek | odchod vypočítaný | odchod z poriadku | príchod vypočítaný | príchod z poriadku | chôdza vypočítaná [m] | chôdza z mapy [m] | f / g [min] | porušenia |
|---|---|---|---|---|---|---|---|---|---|
| (a) | 93 Hlavná stanica → Jiráskova | 07:30:00 | | 07:43:00 | | 0 | | 13,00 / 13,00 | – |
| (b) | 93 Hlavná stanica → Zochova | 07:30:00 | | 07:35:00 | | 0 | | 19,00 / 19,00 | – |
| (b) | 31 Zochova → Lanfranconi | 07:38:45 | | 07:44:00 | | 0 | | 19,00 / 19,00 | – |
| (c) | iba pešo | – | | – | | 461 | | 5,92 / 5,92 | – |
| (d) | 93 Hodžovo nám. → Jiráskova | 07:50:00 | | 07:59:00 | | 1404 | | 29,00 / 229,00 | O1 |
| (e) | spoj neexistuje | – | | – | | – | | ∞ / ∞ | O2 |

