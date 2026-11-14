"""Kontrola modelu na reálnych dátach.

Načíta data/gtfs/, vypíše počty liniek, zastávok a spojov, čas načítania,
ohodnotí jednu ručne zadanú trasu a zmeria čas jedného vyhodnotenia.

Spustenie:  python scripts/check_model.py
"""

import math
import sys
import time
from datetime import date
from pathlib import Path

from mhd import geo
from mhd.evaluate import Hodnotitel
from mhd.gtfs import CestovnyPoriadok
from mhd.model import Kandidat, Poziadavka, Usek
from mhd.params import Parametre

GTFS = Path(__file__).resolve().parent.parent / "data" / "gtfs"


def _docasne_geo() -> None:
    """Ak geo.py (osoba B) ešte nie je hotové, použije dočasnú náhradu."""
    try:
        geo.pesia_vzdialenost_m((48.0, 17.0), (48.0, 17.0), Parametre())
        return
    except NotImplementedError:
        pass

    def pesia(a, b, par):
        f1, f2 = math.radians(a[0]), math.radians(b[0])
        dl = math.radians(b[1] - a[1])
        x = math.sin((f2 - f1) / 2) ** 2 + math.cos(f1) * math.cos(f2) * math.sin(dl / 2) ** 2
        return 2 * 6_371_000.0 * math.asin(math.sqrt(x)) * par.zachadzka

    geo.pesia_vzdialenost_m = pesia
    geo.cas_chodze_s = lambda d, par: math.ceil(d / par.rychlost_chodze)
    print("POZOR: geo.py ešte nie je implementované – použitá dočasná náhrada.\n")


def hhmmss(s: int) -> str:
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


def main() -> int:
    _docasne_geo()

    t = time.perf_counter()
    cp = CestovnyPoriadok.nacitaj(str(GTFS))
    cas_nacitania = time.perf_counter() - t
    linky, zastavky, spoje = cp.pocty()
    print(f"Linky: {linky}, zastávky: {zastavky}, spoje: {spoje}")
    print(f"Čas načítania: {cas_nacitania:.2f} s (s cache v data/cache/ je rýchlejšie)\n")

    # Ručná trasa: pri Hlavnej stanici -> električka 1 na Poštovú ->
    # prestup na električku 9 -> Kútiky; streda 18. 11. 2026 o 8:00.
    k = Kandidat([
        Usek("1014", "000000009300001", "000000030200001"),  # 1: Hlavná stanica -> Poštová
        Usek("9015", "000000030200001", "000000014300002"),  # 9: Poštová -> Kútiky
    ])
    p = Poziadavka(
        id="rucna",
        start=(48.1590, 17.1060),   # pri Hlavnej stanici
        ciel=(48.1665, 17.0480),    # pri zastávke Kútiky (Karlova Ves)
        datum=date(2026, 11, 18),
        cas_odchodu=8 * 3600,
    )
    hod = Hodnotitel(cp, Parametre())
    h = hod.ohodnot(k, p)

    print(f"Trasa '{p.id}', {p.datum}, odchod {hhmmss(p.cas_odchodu)}")
    for c in h.itinerar:
        od = c.od if c.od in ("start", "ciel") else cp.nazov(c.od)
        do = c.do if c.do in ("start", "ciel") else cp.nazov(c.do)
        extra = f" linka {c.linka} ({c.trip_id})" if c.typ == "jazda" else ""
        if c.typ == "chodza":
            extra = f" {c.vzdialenost_m:.0f} m"
        print(f"  {hhmmss(c.cas_od)}–{hhmmss(c.cas_do)}  {c.typ:8s} {od} -> {do}{extra}")
    print(f"  f = {h.f:.2f} min, g = {h.g:.2f} min, prestupy = {h.prestupy}, "
          f"chôdza = {h.chodza_m:.0f} m, prípustný = {h.pripustny}, porušenia = {h.porusenia}")

    n = 10_000
    t = time.perf_counter()
    for _ in range(n):
        hod.ohodnot(k, p)
    print(f"\nČas jedného vyhodnotenia: {(time.perf_counter() - t) / n * 1e6:.1f} µs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
