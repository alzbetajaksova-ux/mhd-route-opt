"""Overené príklady: 5 ručne zostavených trás na reálnych dátach DPB.

Implementuje osoba C. Utorok 24. 11. 2026, odchod 7:30. Pre každú trasu vypíše
itinerár (časy, zastávky, linky, chôdza v m), f, g a porušenia a na konci
tabuľku „očakávané z cestovného poriadku vs. vypočítané“ na ručné overenie
(dpb.sk / imhd.sk). Výstup sa uloží aj do results/demo_examples.md.

Trasy:
  (a) priama trasa:      Hlavná stanica -> Jiráskova (Petržalka), linka 93
  (b) 1 prestup:         Hlavná stanica -> Lanfranconi (Mlynská dolina),
                         93 po Zochovu, prestup na 31 na tom istom nástupišti
  (c) iba pešo:          Hodžovo nám. -> Zochova
  (d) neprípustná (O1):  štart pri Hlavnej stanici, nástup na 93 až na Hodžovom nám.
  (e) nedekódovateľná:   linka 93 z Jiráskovej „späť“ na Hlavnú stanicu, ale
                         z nástupišťa v smere do Petržalky (O2)

Spustenie:  python scripts/demo_examples.py [--gtfs data/gtfs] [--vystup results]
"""

import argparse
import sys
from datetime import date
from pathlib import Path

import pandas as pd

from mhd.evaluate import Hodnotitel
from mhd.gtfs import CestovnyPoriadok
from mhd.model import Hodnotenie, Kandidat, Poziadavka, Usek
from mhd.params import Parametre

KOREN = Path(__file__).resolve().parents[1]
DATUM = date(2026, 11, 24)  # utorok
T0 = 7 * 3600 + 30 * 60     # 7:30

# stop_id zo zafixovaného GTFS DPB (feed 6. 11. 2026)
HLAVNA_STANICA_93 = "000000009300007"   # nástupište liniek 71/93 smer centrum
HODZOVO_93 = "000000009500004"          # Hodžovo nám., smer Zochova
ZOCHOVA_2 = "000000050000002"           # Zochova, smer Most SNP / Karlova Ves
# Jiráskova a Lanfranconi sa hľadajú podľa názvu medzi zastávkami za nástupom (O2)


def hhmmss(s: int) -> str:
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


def zastavka_podla_nazvu(cp: CestovnyPoriadok, nazov: str, linka: str, za: str) -> str:
    """stop_id zastávky s daným názvom, ktorú linka dosiahne zo zastávky za (O2)."""
    for z in cp.zastavky_za(linka, za, DATUM):
        if cp.nazov(z) == nazov:
            return z
    raise SystemExit(f"Zastávka '{nazov}' nie je za {cp.nazov(za)} na linke {linka}")


def priklady(cp: CestovnyPoriadok, linka_id: dict[str, str]) -> list[tuple[str, str, Kandidat, Poziadavka]]:
    """[(kľúč, popis, kandidát, požiadavka)] – päť overovaných trás."""
    l93, l31 = linka_id["93"], linka_id["31"]
    jiraskova = zastavka_podla_nazvu(cp, "Jiráskova", l93, HLAVNA_STANICA_93)
    lanfranconi = zastavka_podla_nazvu(cp, "Lanfranconi", l31, ZOCHOVA_2)
    s = cp.suradnice
    hl_st = s(HLAVNA_STANICA_93)

    def poz(i, a, b):
        return Poziadavka(i, a, b, DATUM, T0)

    return [
        ("a", "priama trasa: Hlavná stanica -> Jiráskova (Petržalka)",
         Kandidat([Usek(l93, HLAVNA_STANICA_93, jiraskova)]),
         poz("a", hl_st, s(jiraskova))),
        ("b", "1 prestup: Hlavná stanica -> Lanfranconi (Mlynská dolina)",
         Kandidat([Usek(l93, HLAVNA_STANICA_93, ZOCHOVA_2), Usek(l31, ZOCHOVA_2, lanfranconi)]),
         poz("b", hl_st, s(lanfranconi))),
        ("c", "iba pešo: Hodžovo nám. -> Zochova",
         Kandidat([]),
         poz("c", s(HODZOVO_93), s(ZOCHOVA_2))),
        ("d", "neprípustná (O1): nástup na Hodžovom nám., štart pri Hlavnej stanici",
         Kandidat([Usek(l93, HODZOVO_93, jiraskova)]),
         poz("d", hl_st, s(jiraskova))),
        ("e", "nedekódovateľná (O2): linka 93 z Jiráskovej v opačnom smere",
         Kandidat([Usek(l93, jiraskova, HLAVNA_STANICA_93)]),
         poz("e", s(jiraskova), hl_st)),
    ]


def vypis(cp: CestovnyPoriadok, nazov_linky: dict[str, str], h: Hodnotenie) -> list[str]:
    """Riadky itinerára: čas od – do, typ, odkiaľ – kam, linka, chôdza."""
    def miesto(x: str) -> str:
        return x if x in ("start", "ciel") else cp.nazov(x)

    riadky = []
    for c in h.itinerar:
        cas = f"{hhmmss(c.cas_od)} – {hhmmss(c.cas_do)}"
        if c.typ == "jazda":
            detail = f"linka {nazov_linky[c.linka]:>3}  {miesto(c.od)} -> {miesto(c.do)}  (spoj {c.trip_id})"
        elif c.typ == "chodza":
            detail = f"chôdza     {miesto(c.od)} -> {miesto(c.do)}  {c.vzdialenost_m:.0f} m"
        else:
            detail = f"čakanie    {miesto(c.od)}  {(c.cas_do - c.cas_od) / 60:.1f} min"
        riadky.append(f"    {cas}  {detail}")
    return riadky


def cislo(x: float) -> str:
    return "∞" if x == float("inf") else f"{x:.2f}".replace(".", ",")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--gtfs", default=str(KOREN / "data" / "gtfs"))
    ap.add_argument("--vystup", default=str(KOREN / "results"))
    args = ap.parse_args()

    cp = CestovnyPoriadok.nacitaj(args.gtfs)
    routes = pd.read_csv(Path(args.gtfs) / "routes.txt", dtype=str, encoding="utf-8-sig")
    nazov_linky = dict(zip(routes.route_id, routes.route_short_name))
    linka_id = {v: k for k, v in nazov_linky.items()}
    par = Parametre()
    hod = Hodnotitel(cp, par)

    md = [
        "# Overené príklady (scripts/demo_examples.py)",
        "",
        f"Utorok {DATUM:%d. %m. %Y}, t₀ = {hhmmss(T0)}. Vygenerované skriptom; "
        "stĺpce „z poriadku“ vypĺňa človek podľa dpb.sk / imhd.sk.",
        "",
    ]
    tabulka = []
    for kluc, popis, k, p in priklady(cp, linka_id):
        h = hod.ohodnot(k, p)
        hlavicka = f"({kluc}) {popis}"
        print(hlavicka)
        riadky = vypis(cp, nazov_linky, h)
        if not h.dekodovatelny:
            u = k.useky[len([c for c in h.itinerar if c.typ == "jazda"])]
            riadky.append(f"    linka {nazov_linky[u.linka]} {cp.nazov(u.nastup)} -> "
                          f"{cp.nazov(u.vystup)}: v tomto smere nejde – nedekódovateľný")
        print("\n".join(riadky))
        sumar = (f"    f = {cislo(h.f)} min, g = {cislo(h.g)} min, prestupy = {h.prestupy}, "
                 f"chôdza = {h.chodza_m:.0f} m, porušenia = {h.porusenia or '–'}, "
                 f"prípustný = {h.pripustny}, dekódovateľný = {h.dekodovatelny}")
        print(sumar, "\n")
        md += [f"## {hlavicka}", "", "```", *riadky, sumar.strip(), "```", ""]

        jazdy = [c for c in h.itinerar if c.typ == "jazda"]
        chodza = " + ".join(f"{c.vzdialenost_m:.0f}" for c in h.itinerar
                            if c.typ == "chodza" and c.vzdialenost_m > 0) or "0"
        if jazdy:
            for c in jazdy:
                tabulka.append(f"| ({kluc}) | {nazov_linky[c.linka]} {cp.nazov(c.od)} → "
                               f"{cp.nazov(c.do)} | {hhmmss(c.cas_od)} | | "
                               f"{hhmmss(c.cas_do)} | | {chodza} | | "
                               f"{cislo(h.f)} / {cislo(h.g)} | {', '.join(h.porusenia) or '–'} |")
        else:
            tabulka.append(f"| ({kluc}) | {'iba pešo' if h.dekodovatelny else 'spoj neexistuje'} | – | | – | | "
                           f"{chodza if h.dekodovatelny else '–'} | | {cislo(h.f)} / {cislo(h.g)} | "
                           f"{', '.join(h.porusenia) or '–'} |")

    hlav = ("| trasa | úsek | odchod vypočítaný | odchod z poriadku | príchod vypočítaný | "
            "príchod z poriadku | chôdza vypočítaná [m] | chôdza z mapy [m] | f / g [min] | porušenia |")
    tab = [hlav, "|" + "---|" * 10, *tabulka]
    print("Očakávané z cestovného poriadku vs. vypočítané (prázdne stĺpce vyplniť ručne):")
    print("\n".join(tab))
    md += ["## Očakávané z cestovného poriadku vs. vypočítané", "", *tab, ""]

    out = Path(args.vystup)
    out.mkdir(parents=True, exist_ok=True)
    (out / "demo_examples.md").write_text("\n".join(md) + "\n", encoding="utf-8", newline="\n")
    print(f"\nUložené: {out / 'demo_examples.md'}")


if __name__ == "__main__":
    main()
