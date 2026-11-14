"""Overenie, že kontrakt (mená, polia, predvolené hodnoty) platí presne."""

import dataclasses
import inspect
from datetime import date
from pathlib import Path

import pytest

from mhd.evaluate import Hodnotitel
from mhd.geo import cas_chodze_s, pesia_vzdialenost_m
from mhd.gtfs import CestovnyPoriadok
from mhd.model import CastTrasy, Hodnotenie, Kandidat, Poziadavka, Usek
from mhd.params import Parametre
from mhd.spatial import PriestorovyIndex

TOY = Path(__file__).parent / "data" / "toy_gtfs"


def polia(trieda) -> list[str]:
    return [f.name for f in dataclasses.fields(trieda)]


def test_parametre_predvolene():
    p = Parametre()
    assert (p.rychlost_chodze, p.zachadzka) == (1.3, 1.3)
    assert (p.d_max, p.d_prestup) == (800.0, 400.0)
    assert (p.min_prestup, p.max_prestupov, p.horizont) == (60, 3, 10800)
    assert (p.penalizacia_prestupu, p.penalizacia_porusenia) == (5.0, 200.0)


def test_polia_tried():
    assert polia(Usek) == ["linka", "nastup", "vystup"]
    assert polia(Kandidat) == ["useky"]
    assert polia(Poziadavka) == ["id", "start", "ciel", "datum", "cas_odchodu"]
    assert polia(CastTrasy) == [
        "typ", "od", "do", "cas_od", "cas_do", "linka", "trip_id", "vzdialenost_m"
    ]
    assert polia(Hodnotenie) == [
        "itinerar", "celkovy_cas_s", "prestupy", "chodza_m",
        "f", "g", "pripustny", "dekodovatelny", "porusenia",
    ]


def test_frozen_a_hashovatelnost():
    u = Usek("1", "01", "03")
    with pytest.raises(dataclasses.FrozenInstanceError):
        u.linka = "2"  # type: ignore[misc]
    assert len({u, Usek("1", "01", "03")}) == 1
    p = Poziadavka("x", (48.15, 17.1), (48.16, 17.12), date(2026, 11, 16), 25200)
    with pytest.raises(dataclasses.FrozenInstanceError):
        p.cas_odchodu = 0  # type: ignore[misc]


def test_predvolene_hodnoty_poli():
    c = CastTrasy("chodza", "start", "01", 0, 10)
    assert (c.linka, c.trip_id, c.vzdialenost_m) == (None, None, 0.0)
    h1 = Hodnotenie([], 0, 0, 0.0, 0.0, 0.0, True, True)
    h2 = Hodnotenie([], 0, 0, 0.0, 0.0, 0.0, True, True)
    h1.porusenia.append("O1")
    assert h2.porusenia == []  # žiadny zdieľaný mutable default


def test_hlavicky_funkcii():
    assert list(inspect.signature(CestovnyPoriadok.nacitaj).parameters) == ["cesta"]
    assert list(inspect.signature(CestovnyPoriadok.najblizsi_odchod).parameters) == [
        "self", "linka", "nastup", "vystup", "od_casu", "datum"
    ]
    assert list(inspect.signature(pesia_vzdialenost_m).parameters) == ["a", "b", "par"]
    assert list(inspect.signature(cas_chodze_s).parameters) == ["vzdialenost_m", "par"]
    assert list(inspect.signature(PriestorovyIndex.v_okoli).parameters) == [
        "self", "bod", "max_m"
    ]
    assert list(inspect.signature(Hodnotitel.ohodnot).parameters) == ["self", "k", "p"]


def test_toy_gtfs_existuje():
    for subor in ["stops.txt", "routes.txt", "trips.txt", "stop_times.txt",
                  "calendar.txt", "calendar_dates.txt", "README.md"]:
        assert (TOY / subor).is_file(), subor
