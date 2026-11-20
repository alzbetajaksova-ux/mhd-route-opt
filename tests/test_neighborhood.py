"""Testy operátorov okolia (src/mhd/neighborhood.py) na toy sieti."""

import copy
import random
from datetime import date

import pytest

from mhd import neighborhood as nb
from mhd.baselines.random_search import nahodny_kandidat
from mhd.model import Kandidat, Poziadavka, Usek
from mhd.params import Parametre

PO = date(2026, 11, 16)
PAR = Parametre()

# (štart, cieľ, úseky) – všetky spĺňajú O2 v pondelok 16. 11.
KANDIDATI = {
    "priama":            ("01", "03", [("1", "01", "03")]),
    "prestup bez chodze": ("01", "08", [("1", "01", "02"), ("2", "02", "08")]),
    "prestup s chodzou": ("02", "01", [("2", "02", "07"), ("3", "06", "01")]),
    "styri useky":       ("01", "08", [("1", "01", "02"), ("2", "02", "04"),
                                       ("2", "04", "05"), ("2", "05", "08")]),
    "iba pesho":         ("07", "06", []),
}


def poziadavka(cp, start, ciel, datum=PO, t0=25200):
    return Poziadavka("test", cp.suradnice(start), cp.suradnice(ciel), datum, t0)


def kandidat(useky):
    return Kandidat([Usek(*u) for u in useky])


def vsetky_vstupy(cp):
    for nazov, (start, ciel, useky) in KANDIDATI.items():
        yield nazov, kandidat(useky), poziadavka(cp, start, ciel)


def over_suseda(s, p, cp):
    assert isinstance(s, Kandidat)
    assert len(s.useky) <= nb.MAX_USEKOV
    assert nb.splna_o2(s, p, cp)


# ------------------------------------------------------------ O2 a dĺžka
@pytest.mark.parametrize("op", nb.OPERATORY)
@pytest.mark.parametrize("nazov", KANDIDATI)
def test_operator_splna_o2_a_dlzku(cp, op, nazov):
    start, ciel, useky = KANDIDATI[nazov]
    k, p = kandidat(useky), poziadavka(cp, start, ciel)
    assert nb.splna_o2(k, p, cp)
    for seed in range(20):
        s = nb.OPERATORY[op](k, p, cp, PAR, random.Random(seed))
        if s is not None:
            over_suseda(s, p, cp)
            assert s.useky != k.useky


def test_nahodne_kandidati_a_ich_susedia(cp):
    """Susedia náhodných kandidátov od B (rôzne štarty a ciele) spĺňajú O2."""
    zastavky = ["01", "02", "03", "04", "05", "06", "07", "08"]
    rng = random.Random(1)
    pocet = 0
    for _ in range(100):
        p = poziadavka(cp, rng.choice(zastavky), rng.choice(zastavky))
        k = nahodny_kandidat(cp, p, PAR, rng)
        for s in nb.susedia(k, p, cp, PAR, rng, limit=5):
            over_suseda(s, p, cp)
            pocet += 1
    assert pocet > 50


# ------------------------------------------------------------ konkrétne zmeny
def test_odober_prestup_zluci_rovnaku_linku(cp):
    k = kandidat([("1", "01", "02"), ("2", "02", "04"), ("2", "04", "05")])
    s = nb.odober_prestup(k, poziadavka(cp, "01", "05"), cp, PAR, random.Random(0))
    assert s.useky == [Usek("1", "01", "02"), Usek("2", "02", "05")]


def test_odober_prestup_none(cp):
    # z 01 nejde žiadna linka do 08
    k = kandidat([("1", "01", "02"), ("2", "02", "08")])
    assert nb.odober_prestup(k, poziadavka(cp, "01", "08"), cp, PAR, random.Random(0)) is None


def test_pridaj_prestup_none_pri_4_usekoch(cp):
    _, _, useky = KANDIDATI["styri useky"]
    p = poziadavka(cp, "01", "08")
    assert nb.pridaj_prestup(kandidat(useky), p, cp, PAR, random.Random(0)) is None


def test_zmen_vystup_ostane_na_linke(cp):
    k = kandidat([("2", "02", "07")])
    for seed in range(10):
        s = nb.zmen_vystup(k, poziadavka(cp, "02", "08"), cp, PAR, random.Random(seed))
        assert s.useky[0].linka == "2" and s.useky[0].nastup == "02"
        assert s.useky[0].vystup in {"04", "05", "08"}


def test_zmen_vystup_prednostne_pri_cieli(cp):
    # cieľ = 08; do 800 m od cieľa je z výstupov 04, 05, 08 iba 08 (07 je pôvodný)
    k = kandidat([("2", "02", "07")])
    p = poziadavka(cp, "02", "08")
    blizko = {v for v in ["04", "05", "08"]
              if nb.geo.pesia_vzdialenost_m(cp.suradnice(v), p.ciel, PAR) <= PAR.d_max}
    for seed in range(10):
        s = nb.zmen_vystup(k, p, cp, PAR, random.Random(seed))
        assert s.useky[0].vystup in blizko


def test_zmen_vystup_none_na_konecnej(cp):
    # z 07 ide linka 2 už iba na 08 – iný výstup neexistuje
    k = kandidat([("2", "07", "08")])
    assert nb.zmen_vystup(k, poziadavka(cp, "07", "08"), cp, PAR, random.Random(0)) is None


def test_posun_prestupu_none(cp):
    # susedné zastávky linky 2 okolo 07 sú 05 a 08; z nich je linka 3 (06) ďalej ako 400 m
    k = kandidat([("2", "02", "07"), ("3", "06", "01")])
    p = poziadavka(cp, "02", "01")
    for seed in range(5):
        assert nb.posun_prestupu(k, p, cp, PAR, random.Random(seed)) is None


def test_posun_prestupu_zachova_linky(cp):
    """Úmyselne zvýšené d_prestup: prestup sa dá posunúť na 05 alebo 08."""
    par = Parametre(d_prestup=1300.0)
    k = kandidat([("2", "02", "07"), ("3", "06", "01")])
    p = poziadavka(cp, "02", "01")
    s = nb.posun_prestupu(k, p, cp, par, random.Random(0))
    assert s is not None
    over_suseda(s, p, cp)
    assert [u.linka for u in s.useky] == ["2", "3"]
    assert s.useky[0].vystup in {"05", "08"}
    a, b = s.useky[0].vystup, s.useky[1].nastup
    assert nb.geo.pesia_vzdialenost_m(cp.suradnice(a), cp.suradnice(b), par) <= par.d_prestup


def test_vymen_linku_none(cp):
    # z 01 na 03 ide iba linka 1
    k = kandidat([("1", "01", "03")])
    assert nb.vymen_linku(k, poziadavka(cp, "01", "03"), cp, PAR, random.Random(0)) is None


def test_iba_pesho_nema_susedov(cp):
    p = poziadavka(cp, "07", "06")
    k = Kandidat([])
    for op in nb.OPERATORY.values():
        assert op(k, p, cp, PAR, random.Random(0)) is None
    assert nb.nahodny_sused(k, p, cp, PAR, random.Random(0)) is None
    assert nb.susedia(k, p, cp, PAR, random.Random(0)) == []


def test_sobotna_linka_v_pondelok(cp):
    """Kandidát nedekódovateľný v daný deň (O4) – operátory ho neopravia na neplatný."""
    k = kandidat([("1", "01", "03")])
    p = poziadavka(cp, "01", "03", datum=date(2026, 11, 21))  # sobota: linka 1 nejde
    for op in nb.OPERATORY.values():
        s = op(k, p, cp, PAR, random.Random(0))
        if s is not None:
            over_suseda(s, p, cp)


# ------------------------------------------------------------ determinizmus a nemennosť
@pytest.mark.parametrize("op", nb.OPERATORY)
def test_determinizmus_operatorov(cp, op):
    for _, k, p in vsetky_vstupy(cp):
        for seed in range(5):
            a = nb.OPERATORY[op](k, p, cp, PAR, random.Random(seed))
            b = nb.OPERATORY[op](k, p, cp, PAR, random.Random(seed))
            assert a == b


def test_determinizmus_susedia(cp):
    for _, k, p in vsetky_vstupy(cp):
        a = nb.susedia(k, p, cp, PAR, random.Random(7), limit=10)
        b = nb.susedia(k, p, cp, PAR, random.Random(7), limit=10)
        assert a == b


def test_povodny_kandidat_sa_nezmeni(cp):
    for _, k, p in vsetky_vstupy(cp):
        povodny = copy.deepcopy(k)
        zoznam = k.useky
        for seed in range(10):
            for op in nb.OPERATORY.values():
                op(k, p, cp, PAR, random.Random(seed))
            nb.nahodny_sused(k, p, cp, PAR, random.Random(seed))
            nb.susedia(k, p, cp, PAR, random.Random(seed), limit=5)
        assert k == povodny
        assert k.useky is zoznam


def test_susedia_limit_a_unikatnost(cp):
    _, _, useky = KANDIDATI["prestup s chodzou"]
    k, p = kandidat(useky), poziadavka(cp, "02", "01")
    s = nb.susedia(k, p, cp, PAR, random.Random(0), limit=3)
    assert len(s) <= 3
    kluce = [tuple(x.useky) for x in s]
    assert len(set(kluce)) == len(kluce)
    assert tuple(k.useky) not in kluce
