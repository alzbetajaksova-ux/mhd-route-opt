"""Meranie modelu a operátorov okolia na reálnych dátach.

Implementuje osoba C. Meria:
  1. čas načítania GTFS (z CSV a z cache v data/cache/),
  2. priemerný čas jedného Hodnotitel.ohodnot na N náhodných kandidátoch
     (nahodny_kandidat od B, inštancie z data/instances.json striedavo),
  3. podiel prípustných, neprípustných a nedekódovateľných kandidátov
     a početnosť porušených obmedzení,
  4. operátory okolia: podiel volaní, ktoré vrátia None, čas volania,
     kontrola O2 a dĺžky každého suseda, podiel dekódovateľných, prípustných
     a zlepšujúcich susedov.

Výsledky uloží do results/bench.md. Seed je pevný; namerané časy závisia od počítača.

Spustenie:  python scripts/bench_eval.py [--pocet 10000] [--pocet-op 2000] [--seed 0]
"""

import argparse
import platform
import random
import statistics
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

from mhd import neighborhood as nb
from mhd.baselines.random_search import Pamat, nahodny_kandidat
from mhd.evaluate import Hodnotitel
from mhd.gtfs import CestovnyPoriadok
from mhd.instances import nacitaj_instancie, skupina
from mhd.params import Parametre

KOREN = Path(__file__).resolve().parents[1]
OPAKOVANI = 3  # koľkokrát sa zopakuje vyhodnotenie celej vzorky (časy kolíšu)


def pct(a: int, n: int) -> str:
    return f"{100 * a / n:.1f} %".replace(".", ",") if n else "–"


def num(x: float, d: int = 1) -> str:
    return f"{x:.{d}f}".replace(".", ",")


def tabulka_operatorov(stat: dict[str, Counter], cas_op: dict[str, float] | None = None) -> list[str]:
    """Markdown tabuľka štatistík operátorov (None, dekódovateľní, prípustní, zlepšujúci)."""
    hlav = "| operátor | volaní | vráti None |" + (" priem. čas [ms] |" if cas_op else "")
    hlav += " dekódovateľní | prípustní | zlepšujúci |"
    riadky = [hlav, "|" + "---|" * (hlav.count("|") - 1)]
    spolu: Counter = Counter()
    for nazov, c in stat.items():
        spolu.update(c)
        v = c["volani"] - c["none"]
        cas = f" {num(1e3 * cas_op[nazov] / c['volani'], 2)} |" if cas_op else ""
        riadky.append(f"| `{nazov}` | {c['volani']} | {pct(c['none'], c['volani'])} |{cas} "
                      f"{pct(c['dek'], v)} | {pct(c['prip'], v)} | {pct(c['lepsi'], v)} |")
    v = spolu["volani"] - spolu["none"]
    cas = f" {num(1e3 * sum(cas_op.values()) / spolu['volani'], 2)} |" if cas_op else ""
    riadky.append(f"| spolu | {spolu['volani']} | **{pct(spolu['none'], spolu['volani'])}** |{cas} "
                  f"{pct(spolu['dek'], v)} | {pct(spolu['prip'], v)} | {pct(spolu['lepsi'], v)} |")
    return riadky


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--gtfs", default=str(KOREN / "data" / "gtfs"))
    ap.add_argument("--instancie", default=str(KOREN / "data" / "instances.json"))
    ap.add_argument("--pocet", type=int, default=10_000, help="počet náhodných kandidátov")
    ap.add_argument("--pocet-op", type=int, default=2_000,
                    help="na koľkých z nich sa skúšajú všetky operátory okolia")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--vystup", default=str(KOREN / "results" / "bench.md"))
    args = ap.parse_args()

    # ---------------------------------------------------------------- 1. načítanie
    t = time.perf_counter()
    cp_csv = CestovnyPoriadok._nacitaj_csv(Path(args.gtfs))  # bez cache
    t_csv = time.perf_counter() - t
    del cp_csv
    CestovnyPoriadok.nacitaj(args.gtfs)  # vytvorí cache, ak ešte nie je
    t = time.perf_counter()
    cp = CestovnyPoriadok.nacitaj(args.gtfs)
    t_cache = time.perf_counter() - t
    linky, zastavky, spoje = cp.pocty()
    print(f"načítanie GTFS: CSV {t_csv:.2f} s, cache {t_cache:.2f} s "
          f"({linky} liniek, {zastavky} zastávok, {spoje} spojov)")

    par = Parametre()
    hod = Hodnotitel(cp, par)
    instancie = nacitaj_instancie(args.instancie)
    rng = random.Random(args.seed)
    pamate = {p.id: Pamat(cp, p) for p in instancie}

    # ---------------------------------------------------------------- 2. generovanie
    t = time.perf_counter()
    vzorka = []
    for i in range(args.pocet):
        p = instancie[i % len(instancie)]
        vzorka.append((nahodny_kandidat(cp, p, par, rng, pamate[p.id]), p))
    t_gen = time.perf_counter() - t

    # ---------------------------------------------------------------- 3. vyhodnotenie
    for k, p in vzorka[:200]:  # zahriatie (kalendár, kešované služby)
        hod.ohodnot(k, p)
    hod.pocet_vyhodnoteni = 0
    casy_podla_dlzky: dict[int, list[float]] = defaultdict(list)
    casy_podla_stavu: dict[str, list[float]] = defaultdict(list)
    hodnotenia = []
    for k, p in vzorka:
        t = time.perf_counter()
        h = hod.ohodnot(k, p)
        dt = time.perf_counter() - t
        casy_podla_dlzky[len(k.useky)].append(dt)
        stav = "prípustní" if h.pripustny else ("nedekódovateľní" if not h.dekodovatelny else "neprípustní")
        casy_podla_stavu[stav].append(dt)
        hodnotenia.append(h)
    n = len(vzorka)
    assert hod.pocet_vyhodnoteni == n
    # celkový čas bez réžie merania jednotlivých volaní: OPAKOVANI behov, najlepší a priemer
    behy = []
    for _ in range(OPAKOVANI):
        t = time.perf_counter()
        for k, p in vzorka:
            hod.ohodnot(k, p)
        behy.append(time.perf_counter() - t)
    t_eval, t_eval_priem = min(behy), statistics.fmean(behy)

    prip = sum(h.pripustny for h in hodnotenia)
    nedek = sum(not h.dekodovatelny for h in hodnotenia)
    neprip = n - prip - nedek
    porusenia = Counter(o for h in hodnotenia for o in h.porusenia)
    po_skup: dict[str, Counter] = defaultdict(Counter)
    for (_, p), h in zip(vzorka, hodnotenia):
        stav = "prip" if h.pripustny else ("nedek" if not h.dekodovatelny else "neprip")
        po_skup[skupina(p.id)][stav] += 1
    print(f"ohodnot: {1e6 * t_eval / n:.1f} µs priemerne na {n} kandidátoch; "
          f"prípustní {pct(prip, n)}, neprípustní {pct(neprip, n)}, nedekódovateľní {pct(nedek, n)}")

    # ---------------------------------------------------------------- 4. operátory
    stat = {op: Counter() for op in nb.OPERATORY}        # všetci kandidáti s úsekmi
    stat_dek = {op: Counter() for op in nb.OPERATORY}    # iba dekódovateľní kandidáti
    stat_kratsi = {op: Counter() for op in nb.OPERATORY}  # kandidáti s < 4 úsekmi
    cas_op: dict[str, float] = defaultdict(float)
    porusenia_o2 = 0
    s_usekmi = [(k, p, h) for (k, p), h in zip(vzorka, hodnotenia) if k.useky][: args.pocet_op]
    rng_op = random.Random(args.seed + 1)
    for k, p, h in s_usekmi:
        for nazov, op in nb.OPERATORY.items():
            t = time.perf_counter()
            s = op(k, p, cp, par, rng_op)
            cas_op[nazov] += time.perf_counter() - t
            skupiny_stat = [stat[nazov]] + ([stat_dek[nazov]] if h.dekodovatelny else [])
            if len(k.useky) < nb.MAX_USEKOV:
                skupiny_stat.append(stat_kratsi[nazov])
            for c in skupiny_stat:
                c["volani"] += 1
                c["none"] += s is None
            if s is None:
                continue
            if len(s.useky) > nb.MAX_USEKOV or not nb.splna_o2(s, p, cp):
                porusenia_o2 += 1
            hs = hod.ohodnot(s, p)
            for c in skupiny_stat:
                c["dek"] += hs.dekodovatelny
                c["prip"] += hs.pripustny
                c["lepsi"] += hs.g < h.g
    # nahodny_sused (s opakovaním pri None)
    ns = Counter()
    t = time.perf_counter()
    for k, p, _ in s_usekmi:
        ns["volani"] += 1
        ns["none"] += nb.nahodny_sused(k, p, cp, par, rng_op) is None
    cas_ns = time.perf_counter() - t
    spolu_op = sum(c["volani"] for c in stat.values())
    spolu_none = sum(c["none"] for c in stat.values())
    print(f"operátory: {spolu_op} volaní, None {pct(spolu_none, spolu_op)}, "
          f"susedov porušujúcich O2/dĺžku: {porusenia_o2}")

    # ---------------------------------------------------------------- výstup
    md = [
        "# Meranie modelu a operátorov okolia",
        "",
        f"Vygenerované skriptom `scripts/bench_eval.py` (seed {args.seed}). "
        f"Python {platform.python_version()}, {platform.system()} {platform.release()}, "
        f"procesor: {platform.processor() or 'neuvedený'}. Časy závisia od počítača.",
        "",
        "## Načítanie GTFS",
        "",
        f"- z CSV (bez cache): **{num(t_csv, 2)} s**",
        f"- z cache (`data/cache/*.pkl`): **{num(t_cache, 2)} s**",
        f"- {linky} liniek, {zastavky} zastávok, {spoje} spojov",
        "",
        f"## Vyhodnotenie kandidáta ({n} náhodných kandidátov)",
        "",
        f"Kandidáti z `nahodny_kandidat` (B) striedavo na {len(instancie)} inštanciách z "
        f"`data/instances.json` (≈ {n // len(instancie)} na inštanciu). Generovanie trvalo "
        f"{num(t_gen, 2)} s ({num(1e6 * t_gen / n, 0)} µs na kandidáta, vrátane hľadania "
        f"zastávok v okolí).",
        "",
        f"- priemerný čas jedného `ohodnot`: **{num(1e6 * t_eval / n)} µs** "
        f"(najlepší z {OPAKOVANI} behov celej vzorky; priemer behov {num(1e6 * t_eval_priem / n)} µs)",
        f"- vyhodnotenie všetkých {n} kandidátov: {num(t_eval, 3)} s",
        "",
        "Podľa počtu úsekov (čas meraný pri každom volaní, preto mierne vyšší):",
        "",
        "| počet úsekov | kandidátov | priem. čas `ohodnot` [µs] | medián [µs] |",
        "|---|---|---|---|",
    ]
    for d in sorted(casy_podla_dlzky):
        c = casy_podla_dlzky[d]
        md.append(f"| {d} | {len(c)} | {num(1e6 * statistics.fmean(c))} | "
                  f"{num(1e6 * statistics.median(c))} |")
    md += ["", "| stav kandidáta | kandidátov | priem. čas `ohodnot` [µs] | medián [µs] |",
           "|---|---|---|---|"]
    for stav in ["prípustní", "neprípustní", "nedekódovateľní"]:
        c = casy_podla_stavu[stav]
        md.append(f"| {stav} | {len(c)} | {num(1e6 * statistics.fmean(c))} | "
                  f"{num(1e6 * statistics.median(c))} |")
    md += [
        "",
        "## Prípustnosť náhodných kandidátov",
        "",
        "| skupina | kandidátov | prípustní | neprípustní | nedekódovateľní |",
        "|---|---|---|---|---|",
    ]
    for sk in ["K", "S", "D"]:
        c = po_skup[sk]
        m = sum(c.values())
        md.append(f"| {sk} | {m} | {pct(c['prip'], m)} | {pct(c['neprip'], m)} | {pct(c['nedek'], m)} |")
    md += [
        f"| spolu | {n} | **{pct(prip, n)}** | {pct(neprip, n)} | {pct(nedek, n)} |",
        "",
        "Porušené obmedzenia (podiel zo všetkých kandidátov; kandidát môže mať viac porušení):",
        "",
        "| obmedzenie | kandidátov | podiel |",
        "|---|---|---|",
        *[f"| {o} | {c} | {pct(c, n)} |" for o, c in porusenia.most_common()],
        "",
        f"Najčastejšie porušené: **{porusenia.most_common(1)[0][0]}**" if porusenia else "",
        "",
        f"## Operátory okolia ({len(s_usekmi)} kandidátov s aspoň jedným úsekom)",
        "",
        "Každý operátor sa zavolal raz na každého kandidáta. Podiely dekódovateľných, "
        "prípustných a zlepšujúcich (g suseda < g kandidáta) susedov sú z vrátených "
        "(nie None) susedov.",
        "",
        "### Všetci kandidáti s úsekmi",
        "",
        *tabulka_operatorov(stat, cas_op),
        "",
        f"### Iba dekódovateľní kandidáti ({stat_dek['zmen_vystup']['volani']})",
        "",
        "Pre metódy 3. fázy je dôležitejšia táto tabuľka: lokálne hľadanie aj GA budú "
        "meniť hlavne dekódovateľných kandidátov.",
        "",
        *tabulka_operatorov(stat_dek),
        "",
        f"### Kandidáti s menej ako {nb.MAX_USEKOV} úsekmi ({stat_kratsi['zmen_vystup']['volani']})",
        "",
        *tabulka_operatorov(stat_kratsi),
        "",
        f"- `nahodny_sused` (najviac {nb.MAX_POKUSOV} pokusov): None v "
        f"{pct(ns['none'], ns['volani'])} volaní, priemerne {num(1e3 * cas_ns / ns['volani'], 2)} ms",
        f"- susedov, ktorí porušujú O2 alebo majú viac ako {nb.MAX_USEKOV} úseky: **{porusenia_o2}**",
        "",
    ]
    out = Path(args.vystup)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(md), encoding="utf-8")
    print(f"Uložené: {out}")


if __name__ == "__main__":
    main()
