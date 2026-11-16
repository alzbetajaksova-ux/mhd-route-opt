"""Testy generátora inštancií (toy sieť + kontrola data/instances.json)."""

import re
from pathlib import Path

import pytest

from mhd import geo
from mhd.instances import (
    CASY, Pasmo, generuj_instancie, kod_casu, nacitaj_instancie, posun_bod,
    skupina, uloz_instancie,
)
from mhd.params import Parametre

# pásma prispôsobené malej toy sieti (zastávky do ~2 km)
TOY_PASMA = (Pasmo("K", 2, 300.0, 1_000.0), Pasmo("S", 3, 1_000.0, 2_500.0))
INSTANCES_JSON = Path(__file__).resolve().parent.parent / "data" / "instances.json"


@pytest.fixture(scope="module")
def instancie(cp):
    return generuj_instancie(cp, seed=42, pasma=TOY_PASMA)


def test_pocet_a_id(instancie):
    assert len(instancie) == (2 + 3) * len(CASY)
    assert len({p.id for p in instancie}) == len(instancie)
    for p in instancie:
        assert re.fullmatch(r"[KS]\d{2}-(ut0730|ut1300|so2200)", p.id)


def test_rovnaky_seed_rovnake_instancie(cp, instancie):
    assert generuj_instancie(cp, seed=42, pasma=TOY_PASMA) == instancie


def test_iny_seed_ine_instancie(cp, instancie):
    assert generuj_instancie(cp, seed=7, pasma=TOY_PASMA) != instancie


def test_vzdialenosti_v_pasmach(instancie):
    pasma = {p.prefix: p for p in TOY_PASMA}
    for p in instancie:
        ps = pasma[skupina(p.id)]
        assert ps.od_m <= geo.haversine_m(p.start, p.ciel) < ps.do_m


def test_kazdy_bod_ma_zastavku_do_d_max(cp, instancie):
    d_max = Parametre().d_max
    for p in instancie:
        assert cp.zastavky_v_okoli(p.start, d_max)
        assert cp.zastavky_v_okoli(p.ciel, d_max)


def test_casy_odchodu(instancie):
    for p in instancie:
        c = next(c for c in CASY if c.kod == kod_casu(p.id))
        assert (p.datum, p.cas_odchodu) == (c.datum, c.cas_s)


def test_dvojica_rovnaka_vo_vsetkych_casoch(instancie):
    for i in range(0, len(instancie), len(CASY)):
        trojica = instancie[i:i + len(CASY)]
        assert len({(p.start, p.ciel) for p in trojica}) == 1


def test_ulozenie_a_nacitanie(cp, instancie, tmp_path):
    cesta = tmp_path / "instances.json"
    uloz_instancie(instancie, cesta, cp, seed=42)
    assert nacitaj_instancie(cesta) == instancie


def test_posun_bod():
    bod = (48.1486, 17.1077)
    for azimut in (0.0, 1.0, 3.0, 5.5):
        assert geo.haversine_m(bod, posun_bod(bod, 450.0, azimut)) == pytest.approx(450.0, abs=0.01)


def test_nesplnitelne_pasmo(cp, monkeypatch):
    monkeypatch.setattr("mhd.instances._MAX_POKUSOV", 200)
    with pytest.raises(RuntimeError):
        generuj_instancie(cp, pasma=(Pasmo("D", 1, 50_000.0, 60_000.0),))


@pytest.mark.skipif(not INSTANCES_JSON.is_file(), reason="data/instances.json ešte nie je vygenerovaný")
def test_ulozene_realne_instancie():
    inst = nacitaj_instancie(INSTANCES_JSON)
    assert len(inst) == 60
    skupiny = [skupina(p.id) for p in inst]
    assert (skupiny.count("K"), skupiny.count("S"), skupiny.count("D")) == (18, 24, 18)
    for p in inst:
        d = geo.haversine_m(p.start, p.ciel)
        assert {"K": 1_000 <= d < 3_000, "S": 3_000 <= d < 7_000, "D": d >= 7_000}[skupina(p.id)]
