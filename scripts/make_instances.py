"""Vygeneruje 60 inštancií z data/gtfs/ a uloží ich do data/instances.json.

Spustenie (z koreňa repozitára):  python scripts/make_instances.py [--seed 42]
"""

import argparse
import sys
from collections import Counter
from pathlib import Path

from mhd.gtfs import CestovnyPoriadok
from mhd.instances import generuj_instancie, kod_casu, skupina, uloz_instancie
from mhd.params import Parametre

KOREN = Path(__file__).resolve().parent.parent


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")  # diakritika aj vo Windows konzole / pri presmerovaní
    ap =argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--gtfs", default=str(KOREN / "data" / "gtfs"))
    ap.add_argument("--vystup", default=str(KOREN / "data" / "instances.json"))
    a = ap.parse_args()

    cp = CestovnyPoriadok.nacitaj(a.gtfs)
    par = Parametre()
    instancie = generuj_instancie(cp, par, seed=a.seed)
    uloz_instancie(instancie, a.vystup, cp, par, seed=a.seed)

    print(f"Uložených {len(instancie)} inštancií do {a.vystup} (seed {a.seed})")
    print("  skupiny:", dict(Counter(skupina(p.id) for p in instancie)))
    print("  časy:   ", dict(Counter(kod_casu(p.id) for p in instancie)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
