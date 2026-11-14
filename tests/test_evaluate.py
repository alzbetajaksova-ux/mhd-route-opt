"""Testy Hodnotitel.ohodnot na toy sieti (scenáre z toy_gtfs/README.md)."""

import math
import time
from datetime import date

import pytest

from mhd.evaluate import Hodnotitel
from mhd.model import Kandidat, Poziadavka, Usek
from mhd.params import Parametre

PO, SVIATOK, SO, UT = date(2026, 11, 16), date(2026, 11, 17), date(2026, 11, 21), date(2026, 11, 24)
PATRONKA = (48.1684112548828, 17.0767230987549)
INF = math.inf

# (štart, cieľ, úseky [(linka, nástup, výstup)], dátum, t0, f, g, porušenia)
SCENARE = {
    "1 priama":             ("01", "03", [("1", "01", "03")], PO, 25200, 7.0, 7.0, []),
    "2 prestup bez chodze": ("01", "08", [("1", "01", "02"), ("2", "02", "08")], PO, 25200, 23.0, 23.0, []),
    "3 prestup s chodzou":  ("02", "01", [("2", "02", "07"), ("3", "06", "01")], PO, 25200, 36.0, 36.0, []),
    "4 iba pesho":          ("07", "06", [], PO, 25200, 2.85, 2.85, []),
    "5 O1":                 (PATRONKA, "03", [("1", "01", "03")], PO, 25200, 57.0, 257.0, ["O1"]),
    "6 O5":                 ("02", "01", [("2", "02", "08"), ("3", "06", "01")], PO, 25200, 46.0, 246.0, ["O5"]),
    "7 O6 prestupy":        ("01", "08", [("1", "01", "02"), ("2", "02", "04"), ("2", "04", "05"),
                                          ("2", "05", "07"), ("2", "07", "08")], PO, 25200, 68.0, 268.0, ["O6"]),
    "8 O6 horizont":        ("06", "01", [("3", "06", "01")], PO, 76200, 181.0, 381.0, ["O6"]),
    "9 po polnoci":         ("06", "01", [("3", "06", "01")], PO, 85800, 21.0, 21.0, []),
    "10 obojsmerna":        ("03", "01", [("1", "03", "01")], PO, 25200, 12.0, 12.0, []),
    "11 O2 opacny smer":    ("08", "02", [("2", "08", "02")], PO, 25200, INF, INF, ["O2"]),
    "12 O4 sobota v utorok": ("03", "05", [("4", "03", "05")], UT, 25200, INF, INF, ["O2"]),
    "13 sobota":            ("03", "05", [("4", "03", "05")], SO, 25200, 5.0, 5.0, []),
    "14 sviatok PD":        ("01", "03", [("1", "01", "03")], SVIATOK, 25200, INF, INF, ["O2"]),
    "15 sviatok SO":        ("03", "05", [("4", "03", "05")], SVIATOK, 25200, 5.0, 5.0, []),
    "16 O3 mimo okna":      ("01", "03", [("1", "01", "03")], PO, 32400, INF, INF, ["O3"]),
}


@pytest.fixture
def hod(cp):
    return Hodnotitel(cp, Parametre())


def poziadavka(cp, start, ciel, datum, t0):
    bod = lambda x: cp.suradnice(x) if isinstance(x, str) else x  # noqa: E731
    return Poziadavka("test", bod(start), bod(ciel), datum, t0)


@pytest.mark.parametrize("nazov", SCENARE)
def test_scenare(cp, hod, nazov):
    start, ciel, useky, datum, t0, f, g, porusenia = SCENARE[nazov]
    h = hod.ohodnot(Kandidat([Usek(*u) for u in useky]), poziadavka(cp, start, ciel, datum, t0))
    assert h.f == pytest.approx(f, abs=1e-9)
    assert h.g == pytest.approx(g, abs=1e-9)
    assert h.porusenia == porusenia
    assert h.dekodovatelny == (f != INF)
    assert h.pripustny == (not porusenia)


def test_itinerar_prestupu(cp, hod):
    k = Kandidat([Usek("2", "02", "07"), Usek("3", "06", "01")])
    h = hod.ohodnot(k, poziadavka(cp, "02", "01", PO, 25200))
    assert [c.typ for c in h.itinerar] == [
        "chodza", "cakanie", "jazda", "chodza", "cakanie", "jazda", "chodza"
    ]
    assert h.itinerar[2].trip_id == "2_0_0705" and h.itinerar[5].trip_id == "3_0_0725"
    assert h.prestupy == 1 and h.celkovy_cas_s == 1860
    assert h.chodza_m == pytest.approx(221.54, abs=0.01)
    # časti nadväzujú
    assert all(a.cas_do == b.cas_od for a, b in zip(h.itinerar, h.itinerar[1:]))


def test_pocitadlo_a_rychlost(cp, hod):
    p = poziadavka(cp, "01", "08", PO, 25200)
    k = Kandidat([Usek("1", "01", "02"), Usek("2", "02", "08")])
    hod.ohodnot(Kandidat([Usek("2", "08", "02")]), p)  # aj nedekódovateľný sa ráta
    n = 2000
    zaciatok = time.perf_counter()
    for _ in range(n):
        hod.ohodnot(k, p)
    assert hod.pocet_vyhodnoteni == n + 1
    assert (time.perf_counter() - zaciatok) / n < 1e-3  # pod 1 ms
