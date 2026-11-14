"""Testy geo.py a spatial.py (hodnoty z toy_gtfs/README.md)."""

import pytest

from mhd.geo import cas_chodze_s, pesia_vzdialenost_m
from mhd.params import Parametre
from mhd.spatial import PriestorovyIndex

PAR = Parametre()
POSTOVA = (48.1466407775879, 17.1085720062256)
HODZOVO = (48.1481628417969, 17.1083030700684)


def test_pesia_vzdialenost_a_cas():
    d = pesia_vzdialenost_m(POSTOVA, HODZOVO, PAR)
    assert d == pytest.approx(221.54, abs=0.01)
    assert pesia_vzdialenost_m(POSTOVA, POSTOVA, PAR) == 0.0
    assert cas_chodze_s(d, PAR) == 171
    assert cas_chodze_s(1.3, PAR) == 1  # presne delené – bez zaokrúhlenia nahor


def test_priestorovy_index():
    idx = PriestorovyIndex({"07": POSTOVA, "06": HODZOVO, "x": (48.2, 17.2)}, PAR)
    assert [s for s, _ in idx.v_okoli(POSTOVA, 400)] == ["07", "06"]
    assert [s for s, _ in idx.v_okoli(POSTOVA, 200)] == ["07"]
    assert PriestorovyIndex({}, PAR).v_okoli(POSTOVA, 400) == []
