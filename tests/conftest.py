"""Spoločné fixtures pre testy.

DOČASNÉ: kým osoba B neimplementuje geo.py a spatial.py, testy použijú
jednoduchú náhradu (haversine R = 6 371 000 m · zachadzka, lineárne hľadanie).
Keď B dodá vlastnú implementáciu, náhrada sa automaticky prestane používať.
"""

import math
from pathlib import Path

import pytest

from mhd import geo, spatial
from mhd.gtfs import CestovnyPoriadok
from mhd.params import Parametre

TOY = Path(__file__).parent / "data" / "toy_gtfs"


def _pesia_vzdialenost_m(a, b, par):
    f1, f2 = math.radians(a[0]), math.radians(b[0])
    dl = math.radians(b[1] - a[1])
    x = math.sin((f2 - f1) / 2) ** 2 + math.cos(f1) * math.cos(f2) * math.sin(dl / 2) ** 2
    return 2 * 6_371_000.0 * math.asin(math.sqrt(x)) * par.zachadzka


def _cas_chodze_s(vzdialenost_m, par):
    return math.ceil(vzdialenost_m / par.rychlost_chodze)


class _PriestorovyIndex:
    def __init__(self, suradnice, par):
        self.suradnice, self.par = suradnice, par

    def v_okoli(self, bod, max_m):
        vysledok = []
        for s, xy in self.suradnice.items():
            d = _pesia_vzdialenost_m(bod, xy, self.par)
            if d <= max_m:
                vysledok.append((s, d))
        return sorted(vysledok, key=lambda t: t[1])


def _je_hotove(funkcia) -> bool:
    try:
        funkcia()
        return True
    except NotImplementedError:
        return False


@pytest.fixture(autouse=True, scope="session")
def docasne_geo():
    par = Parametre()
    mp = pytest.MonkeyPatch()
    if not _je_hotove(lambda: geo.pesia_vzdialenost_m((48.0, 17.0), (48.0, 17.0), par)):
        mp.setattr(geo, "pesia_vzdialenost_m", _pesia_vzdialenost_m)
        mp.setattr(geo, "cas_chodze_s", _cas_chodze_s)
    if not _je_hotove(lambda: spatial.PriestorovyIndex({}, par)):
        mp.setattr(spatial, "PriestorovyIndex", _PriestorovyIndex)
    yield
    mp.undo()


@pytest.fixture(scope="session")
def cp() -> CestovnyPoriadok:
    return CestovnyPoriadok.nacitaj(str(TOY))
