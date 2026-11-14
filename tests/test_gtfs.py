"""Testy načítania GTFS na toy sieti (očakávané hodnoty v toy_gtfs/README.md)."""

from datetime import date

import pandas as pd

from mhd.gtfs import cas_na_sekundy

PO, SVIATOK, SO, NE = date(2026, 11, 16), date(2026, 11, 17), date(2026, 11, 21), date(2026, 11, 22)


def test_casy_po_polnoci():
    assert cas_na_sekundy(pd.Series(["07:00:00", "25:10:00"])).tolist() == [25200, 90600]


def test_nacitanie(cp):
    assert cp.pocty() == (4, 9, 61)
    assert "01" in cp.zastavky()  # ID ostalo str s úvodnou nulou
    assert cp.nazov("02") == "Račianske mýto"


def test_aktivne_sluzby(cp):
    assert cp.aktivne_sluzby(PO) == {"PD"}
    assert cp.aktivne_sluzby(SVIATOK) == {"SO"}  # výnimka typ 2 aj typ 1
    assert cp.aktivne_sluzby(SO) == {"SO"}
    assert cp.aktivne_sluzby(NE) == set()


def test_linky_a_zastavky_za(cp):
    assert cp.linky_na_zastavke("02", PO) == ["1", "2"]
    assert cp.linky_na_zastavke("03", SO) == ["4"]
    assert set(cp.zastavky_za("1", "02", PO)) == {"01", "03"}  # oba smery
    assert cp.zastavky_za("2", "08", PO) == []
    assert cp.zastavky_za("4", "03", PO) == []


def test_najblizsi_odchod(cp):
    assert cp.najblizsi_odchod("1", "01", "03", 25200, PO) == ("1_0_0700", 25200, 25620)
    assert cp.najblizsi_odchod("1", "01", "03", 25201, PO) == ("1_0_0710", 25800, 26220)
    assert cp.najblizsi_odchod("1", "03", "01", 25200, PO)[0] == "1_1_0705"
    assert cp.najblizsi_odchod("2", "08", "02", 0, PO) is None  # opačný smer
    assert cp.najblizsi_odchod("1", "01", "03", 25200, SVIATOK) is None
    assert cp.najblizsi_odchod("3", "06", "01", 80000, PO) == ("3_0_2405", 86700, 87060)


def test_zastavky_v_okoli(cp):
    okolie = cp.zastavky_v_okoli(cp.suradnice("07"), 400)
    assert [s for s, _ in okolie] == ["07", "06"]
    assert abs(okolie[1][1] - 221.54) < 0.01
