"""Spustí obe baseline na všetkých inštanciách a uloží výsledky.

Greedy raz a náhodné hľadanie so seedmi 0–9 a rozpočtom 1 000 vyhodnotení na
každej inštancii z data/instances.json (spolu ~600 000 vyhodnotení, ~2–3 min).

Vytvorí:
    results/baselines.csv         – riadok za každý beh
    results/baselines_summary.md  – súhrnné tabuľky
    results/baselines_box.png     – boxplot f (iba ak je nainštalovaný matplotlib)

Spustenie (z koreňa repozitára):
    python scripts/run_baselines.py                 # celé behy
    python scripts/run_baselines.py --seedy 2 --rozpocet 200   # rýchla skúška
    python scripts/run_baselines.py --iba-suhrn     # iba prepočíta súhrn z CSV
"""

import argparse
import csv
import math
import sys
import time
from pathlib import Path

import pandas as pd

from mhd.baselines.greedy import greedy
from mhd.baselines.random_search import VysledokHladania, nahodne_hladanie
from mhd.evaluate import Hodnotitel
from mhd.gtfs import CestovnyPoriadok
from mhd.instances import kod_casu, nacitaj_instancie, skupina
from mhd.model import Poziadavka
from mhd.params import Parametre

KOREN = Path(__file__).resolve().parent.parent
STLPCE = [
    "instancia", "skupina", "cas", "metoda", "seed", "f", "g", "pripustny", "prestupy",
    "chodza_m", "celkovy_cas_min", "pocet_vyhodnoteni", "podiel_pripustnych_kandidatov",
    "podiel_nedekodovatelnych", "cas_behu_s",
    # doplnkové stĺpce
    "porusenia", "pocet_usekov", "iba_pesho", "podiel_nepripustnych_kandidatov",
    "porusenia_kandidatov", "volani_najblizsi_odchod",
]
SKUPINY = ["K", "S", "D"]
CASY = ["ut0730", "ut1300", "so2200"]
METODY = ["greedy", "nahodne"]


def riadok(p: Poziadavka, metoda: str, seed, v: VysledokHladania, volani="") -> dict:
    h = v.hodnotenie
    n = v.pocet_vyhodnoteni
    podiel = (lambda x: round(x / n, 4)) if metoda == "nahodne" else (lambda x: "")
    return {
        "instancia": p.id, "skupina": skupina(p.id), "cas": kod_casu(p.id),
        "metoda": metoda, "seed": seed,
        "f": round(h.f, 3), "g": round(h.g, 3), "pripustny": int(h.pripustny),
        "prestupy": h.prestupy, "chodza_m": round(h.chodza_m, 1),
        "celkovy_cas_min": round(h.celkovy_cas_s / 60, 3) if h.dekodovatelny else math.inf,
        "pocet_vyhodnoteni": n,
        "podiel_pripustnych_kandidatov": podiel(v.pocet_pripustnych),
        "podiel_nedekodovatelnych": podiel(v.pocet_nedekodovatelnych),
        "cas_behu_s": round(v.cas_behu_s, 4),
        "porusenia": ";".join(h.porusenia),
        "pocet_usekov": len(v.kandidat.useky),
        "iba_pesho": int(not v.kandidat.useky),
        "podiel_nepripustnych_kandidatov": podiel(v.pocet_nepripustnych),
        "porusenia_kandidatov": ";".join(f"{k}:{c}" for k, c in sorted(v.porusenia.items()))
        if metoda == "nahodne" else "",
        "volani_najblizsi_odchod": volani,
    }


def spusti(gtfs: str, instancie_json: str, csv_cesta: Path, seedy: int, rozpocet: int) -> None:
    t = time.perf_counter()
    cp = CestovnyPoriadok.nacitaj(gtfs)
    par = Parametre()
    hod = Hodnotitel(cp, par)
    instancie = nacitaj_instancie(instancie_json)
    print(f"GTFS načítané za {time.perf_counter() - t:.1f} s; {len(instancie)} inštancií, "
          f"seedy 0–{seedy - 1}, rozpočet {rozpocet}")

    csv_cesta.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_cesta, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=STLPCE)
        w.writeheader()
        for i, p in enumerate(instancie, 1):
            v, volani = greedy(hod, cp, p, par)
            w.writerow(riadok(p, "greedy", "", v, volani))
            for seed in range(seedy):
                v = nahodne_hladanie(hod, cp, p, par, rozpocet=rozpocet, seed=seed)
                w.writerow(riadok(p, "nahodne", seed, v))
            f.flush()
            print(f"  [{i:2d}/{len(instancie)}] {p.id}", flush=True)
    print(f"Hotovo za {time.perf_counter() - t:.0f} s, vyhodnotení spolu: {hod.pocet_vyhodnoteni}")
    print(f"Uložené: {csv_cesta}")


# ---------------------------------------------------------------- súhrn

def _fmt(x, des=1) -> str:
    if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
        return "–"
    return f"{x:.{des}f}".replace(".", ",")


def _tabulka(hlavicka: list[str], riadky: list[list[str]]) -> str:
    out = ["| " + " | ".join(hlavicka) + " |", "|" + "---|" * len(hlavicka)]
    out += ["| " + " | ".join(r) + " |" for r in riadky]
    return "\n".join(out)


def _std_cez_seedy(df: pd.DataFrame) -> float:
    """Priemer (cez inštancie) smerodajnej odchýlky f prípustných riešení cez seedy."""
    pr = df[(df.metoda == "nahodne") & (df.pripustny == 1)]
    s = pr.groupby("instancia").f.std(ddof=0)
    return s.mean() if len(s) else math.nan


def _blok(df: pd.DataFrame) -> list[str]:
    pr = df[df.pripustny == 1]
    return [
        str(len(df)),
        _fmt(100 * df.pripustny.mean(), 0) + " %",
        _fmt(pr.f.mean()),
        _fmt(_std_cez_seedy(df)) if (df.metoda == "nahodne").all() else "–",
        _fmt(pr.prestupy.mean(), 2),
        _fmt(100 * df.iba_pesho.mean(), 0) + " %",
        _fmt(df.cas_behu_s.mean(), 3),
    ]


HLAVICKA_BLOK = ["behov", "prípustné", "priem. f [min]", "σ f cez seedy",
                 "priem. prestupy", "iba pešo", "čas behu [s]"]


def suhrn(csv_cesta: Path, md_cesta: Path, png_cesta: Path) -> None:
    df = pd.read_csv(csv_cesta, dtype={"seed": "Int64"})
    for c in ("f", "g", "celkovy_cas_min"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    n_inst = df.instancia.nunique()
    seedy = df[df.metoda == "nahodne"].seed.nunique()
    rozpocet = int(df[df.metoda == "nahodne"].pocet_vyhodnoteni.max()) if seedy else 0

    md = [
        "# Výsledky baseline",
        "",
        f"{n_inst} inštancií; greedy 1 beh na inštanciu, náhodné hľadanie {seedy} seedov "
        f"× rozpočet {rozpocet} vyhodnotení. Priemerné f a prestupy sú iba z prípustných "
        "riešení; σ f = priemer cez inštancie zo smerodajnej odchýlky f (prípustných "
        "riešení) cez seedy. Vygenerované skriptom `scripts/run_baselines.py`.",
        "",
        "## Podľa metódy a skupiny (všetky časy spolu)",
        "",
    ]
    riadky = [[m, s] + _blok(df[(df.metoda == m) & (df.skupina == s)])
              for m in METODY for s in SKUPINY]
    riadky += [[m, "spolu"] + _blok(df[df.metoda == m]) for m in METODY]
    md += [_tabulka(["metóda", "skupina"] + HLAVICKA_BLOK, riadky), ""]

    md += ["## Podľa metódy, skupiny a času odchodu", ""]
    riadky = [[m, s, c] + _blok(x)
              for m in METODY for s in SKUPINY for c in CASY
              if len(x := df[(df.metoda == m) & (df.skupina == s) & (df.cas == c)])]
    md += [_tabulka(["metóda", "skupina", "čas"] + HLAVICKA_BLOK, riadky), ""]

    # greedy vs. náhodné – na úrovni inštancií (medián g cez seedy)
    gr = df[df.metoda == "greedy"].set_index("instancia").g
    nh = df[df.metoda == "nahodne"].groupby("instancia").g.median()
    porov = pd.DataFrame({"greedy": gr, "nahodne": nh}).dropna(how="all")
    porov["skupina"] = [skupina(i) for i in porov.index]
    porov["cas"] = [kod_casu(i) for i in porov.index]
    md += ["## Greedy vs. náhodné hľadanie (počet inštancií)",
           "",
           "Porovnáva sa g greedy s mediánom g náhodného hľadania cez seedy "
           "(rozdiel do 0,05 min = rovnaké).",
           ""]
    riadky = []
    for s in SKUPINY + ["spolu"]:
        for c in CASY + ["spolu"]:
            x = porov
            if s != "spolu":
                x = x[x.skupina == s]
            if c != "spolu":
                x = x[x.cas == c]
            if not len(x):
                continue
            rozdiel = x.greedy - x.nahodne
            lepsi = int((rozdiel < -0.05).sum())
            horsi = int((rozdiel > 0.05).sum())
            riadky.append([s, c, str(lepsi), str(len(x) - lepsi - horsi), str(horsi)])
    md += [_tabulka(["skupina", "čas", "greedy lepší", "rovnaké", "greedy horší"], riadky), ""]

    # kandidáti náhodného hľadania
    nhd = df[df.metoda == "nahodne"].copy()
    md += ["## Kandidáti náhodného hľadania",
           "",
           "Podiel zo všetkých vygenerovaných (a vyhodnotených) kandidátov.",
           ""]
    riadky = []
    for s in SKUPINY + ["spolu"]:
        for c in CASY:
            x = nhd if s == "spolu" else nhd[nhd.skupina == s]
            x = x[x.cas == c]
            if not len(x):
                continue
            riadky.append([s, c,
                           _fmt(100 * x.podiel_pripustnych_kandidatov.astype(float).mean()) + " %",
                           _fmt(100 * x.podiel_nepripustnych_kandidatov.astype(float).mean()) + " %",
                           _fmt(100 * x.podiel_nedekodovatelnych.astype(float).mean()) + " %"])
    md += [_tabulka(["skupina", "čas", "prípustní", "neprípustní", "nedekódovateľní"], riadky), ""]

    spolu: dict[str, int] = {}
    for zaznam in nhd.porusenia_kandidatov.fillna(""):
        for kus in str(zaznam).split(";"):
            if kus:
                k, c = kus.split(":")
                spolu[k] = spolu.get(k, 0) + int(c)
    vsetkych = int(nhd.pocet_vyhodnoteni.sum())
    if vsetkych:
        md += ["Porušenia cez všetkých kandidátov (kandidát môže mať viac porušení): "
               + ", ".join(f"{k} {_fmt(100 * v / vsetkych)} %" for k, v in
                           sorted(spolu.items(), key=lambda t: -t[1])) + ".", ""]

    md_cesta.write_text("\n".join(md), encoding="utf-8")
    print(f"Uložené: {md_cesta}")
    _boxplot(df, png_cesta)


def _boxplot(df: pd.DataFrame, cesta: Path) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib nie je nainštalovaný – boxplot sa preskočí")
        return
    pr = df[df.pripustny == 1]
    data, popisy = [], []
    for s in SKUPINY:
        for m in METODY:
            data.append(pr[(pr.skupina == s) & (pr.metoda == m)].f.to_numpy())
            popisy.append(f"{s}\n{m}")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.boxplot(data, tick_labels=popisy)
    ax.set_ylabel("f prípustných riešení [min]")
    ax.set_title("Baseline: f podľa skupiny inštancií a metódy")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(cesta, dpi=150)
    plt.close(fig)
    print(f"Uložené: {cesta}")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seedy", type=int, default=10, help="počet seedov náhodného hľadania (0..n-1)")
    ap.add_argument("--rozpocet", type=int, default=1000)
    ap.add_argument("--gtfs", default=str(KOREN / "data" / "gtfs"))
    ap.add_argument("--instancie", default=str(KOREN / "data" / "instances.json"))
    ap.add_argument("--vystup", default=str(KOREN / "results"))
    ap.add_argument("--iba-suhrn", action="store_true", help="iba prepočíta súhrn z existujúceho CSV")
    a = ap.parse_args()

    vystup = Path(a.vystup)
    csv_cesta = vystup / "baselines.csv"
    if not a.iba_suhrn:
        spusti(a.gtfs, a.instancie, csv_cesta, a.seedy, a.rozpocet)
    suhrn(csv_cesta, vystup / "baselines_summary.md", vystup / "baselines_box.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
