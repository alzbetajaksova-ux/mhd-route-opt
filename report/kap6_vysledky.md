# 6 Výsledky baseline

Greedy bežal na každej zo 60 inštancií raz. Náhodné hľadanie bežalo so seedmi 0 –
9 a rozpočtom 1 000 vyhodnotení, spolu 600 120 volaní `ohodnot` za 125 s.
Priemerné f a prestupy sú iba z prípustných riešení. σ je priemerná smerodajná
odchýlka f cez seedy. Úplné tabuľky (aj podľa času odchodu) sú v
`results/baselines_summary.md`, boxplot je v `results/baselines_box.png`.

| metóda | skupina | prípustné riešenia | priem. f [min] | σ f cez seedy | priem. prestupy | iba pešo | čas behu [s] |
|---|---|---|---|---|---|---|---|
| greedy | K | 100 % | 24,0 | – | 0,06 | 50 % | 0,003 |
| greedy | S | 100 % | 52,0 | – | 0,42 | 33 % | 0,005 |
| greedy | D | 61 % | 82,4 | – | 1,55 | 28 % | 0,005 |
| náhodné | K | 100 % | 24,9 | 0,9 | 0,04 | 53 % | 0,21 |
| náhodné | S | 100 % | 60,7 | 9,7 | 0,37 | 50 % | 0,22 |
| náhodné | D | 56 % | 97,7 | 19,0 | 1,58 | 23 % | 0,19 |

Podiel prípustných **kandidátov** pri náhodnom hľadaní: K 8,7 – 24,2 %,
S 5,3 – 6,4 %, D 1,8 – 1,9 %. Nedekódovateľných kandidátov je 57 – 77 %.

**Interpretácia.**

- **Greedy vs. náhodné.** Greedy je v porovnaní s mediánom náhodného hľadania
  lepší na 28 inštanciách, rovnaký na 26 a horší na 6. Pritom je približne
  50-krát rýchlejší a spotrebuje iba 2 vyhodnotenia namiesto 1 000.
- **Kde greedy zlyháva.** Na dlhých trasách (D) skončil neprípustne v 7 z 18
  prípadov a 5-krát bol horší než náhodné hľadanie. Krátkozraký výber úseku ho
  zavedie na zastávky, odkiaľ sa nedá rozumne pokračovať.
- **Náhodné hľadanie.** Vždy nájde prípustné riešenie pri K a S, pri D iba v 56 %
  behov. Výsledky pri D silno kolíšu medzi seedmi (σ = 19 min).
- **Iba pešo.** Na krátkych trasách vyhrá trasa iba pešo približne v polovici
  prípadov u oboch metód.
- **Časy odchodu.** V sobotu o 22:00 klesá podiel prípustných riešení náhodného
  hľadania pri D na 47 % a stúpa podiel nedekódovateľných kandidátov na 77 %
  (riedke spoje). Pri K je naopak podiel prípustných kandidátov najvyšší, lebo
  časť náhodných trás je iba pešo.
- **Opatrnosť pri porovnaní f.** Nižšie priemerné f pri D v sobotu (84,7 min
  oproti 97 – 108 min cez týždeň) je skreslené tým, že sa priemerujú iba
  prípustné, teda ľahšie inštancie.
