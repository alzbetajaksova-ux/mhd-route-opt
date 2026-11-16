"""Testy baseline metód na toy sieti (tests/data/toy_gtfs)."""

import random
from datetime import date

import pytest

from mhd import geo
from mhd.baselines.greedy import greedy
from mhd.baselines.random_search import nahodne_hladanie, nahodny_kandidat
from mhd.evaluate import Hodnotitel
from mhd.model import Poziadavka
from mhd.params import Parametre

PO, NE = date(2026, 11, 16), date(2026, 11, 22)
PAR = Parametre()


def poz(cp, start: str, ciel: str, datum: date = PO, t0: int = 25200) -> Poziadavka:
    return Poziadavka(f"{start}-{ciel}", cp.suradnice(start), cp.suradnice(ciel), datum, t0)


@pytest.fixture
def hod(cp):
    return Hodnotitel(cp, PAR)


@pytest.mark.parametrize("start,ciel", [("01", "03"), ("01", "08"), ("02", "01"), ("08", "06")])
def test_nahodny_kandidat_spina_o2_a_dlzku(cp, start, ciel):
    p = poz(cp, start, ciel)
    rng = random.Random(1)
    for _ in range(300):
        k = nahodny_kandidat(cp, p, PAR, rng)
        assert len(k.useky) <= 4
        for i, u in enumerate(k.useky):
            assert u.vystup in cp.zastavky_za(u.linka, u.nastup, p.datum)  # O2
            if i == 0:
                assert geo.pesia_vzdialenost_m(p.start, cp.suradnice(u.nastup), PAR) <= PAR.d_max
            else:
                predosla = cp.suradnice(k.useky[i - 1].vystup)
                assert geo.pesia_vzdialenost_m(predosla, cp.suradnice(u.nastup), PAR) <= PAR.d_prestup


def test_nahodny_kandidat_deterministicky(cp):
    p = poz(cp, "01", "08")
    a = [nahodny_kandidat(cp, p, PAR, random.Random(5)) for _ in range(3)]
    b = [nahodny_kandidat(cp, p, PAR, random.Random(5)) for _ in range(3)]
    assert a == b


def test_nahodny_kandidat_bez_spojov_je_pesho(cp):
    # v nedeľu 22. 11. nepremáva nič
    k = nahodny_kandidat(cp, poz(cp, "01", "03", NE), PAR, random.Random(0))
    assert k.useky == []


def test_nahodne_hladanie_rozpocet(cp, hod):
    hod.pocet_vyhodnoteni = 17
    r = nahodne_hladanie(hod, cp, poz(cp, "01", "08"), PAR, rozpocet=250, seed=3)
    assert r.pocet_vyhodnoteni == 250
    assert hod.pocet_vyhodnoteni == 17 + 250
    assert r.pocet_pripustnych + r.pocet_nepripustnych + r.pocet_nedekodovatelnych == 250


def test_nahodne_hladanie_rovnaky_seed(cp, hod):
    p = poz(cp, "02", "01")
    a = nahodne_hladanie(hod, cp, p, PAR, rozpocet=200, seed=11)
    b = nahodne_hladanie(hod, cp, p, PAR, rozpocet=200, seed=11)
    assert a.kandidat == b.kandidat
    assert (a.hodnotenie.g, a.pocet_pripustnych, a.pocet_nedekodovatelnych) == \
           (b.hodnotenie.g, b.pocet_pripustnych, b.pocet_nedekodovatelnych)


def test_nahodne_hladanie_najde_optimum_priamej_trasy(cp, hod):
    # scenár 1 z toy README: linka 1 01 → 03 o 7:00, f = 7,0 (nič lepšie neexistuje)
    r = nahodne_hladanie(hod, cp, poz(cp, "01", "03"), PAR, rozpocet=300, seed=0)
    assert r.pripustny
    assert r.hodnotenie.g == pytest.approx(7.0)


def test_nahodne_hladanie_vrati_najlepsie_g(cp, hod):
    p = poz(cp, "01", "08")
    r = nahodne_hladanie(hod, cp, p, PAR, rozpocet=100, seed=2)
    rng = random.Random(2)
    from mhd.baselines.random_search import Pamat
    pamat = Pamat(cp, p)
    vsetky = [Hodnotitel(cp, PAR).ohodnot(nahodny_kandidat(cp, p, PAR, rng, pamat), p).g
              for _ in range(100)]
    assert r.hodnotenie.g == min(vsetky)


def test_nahodne_hladanie_neplatny_rozpocet(cp, hod):
    with pytest.raises(ValueError):
        nahodne_hladanie(hod, cp, poz(cp, "01", "03"), PAR, rozpocet=0)


def test_greedy_deterministicky(cp, hod):
    p = poz(cp, "02", "01")
    a, na = greedy(hod, cp, p, PAR)
    b, nb = greedy(hod, cp, p, PAR)
    assert a.kandidat == b.kandidat and a.hodnotenie.g == b.hodnotenie.g and na == nb


def test_greedy_priama_trasa(cp, hod):
    r, volani = greedy(hod, cp, poz(cp, "01", "03"), PAR)
    assert r.pripustny and r.hodnotenie.f == pytest.approx(7.0)
    assert volani > 0


@pytest.mark.parametrize("start,ciel", [("01", "08"), ("02", "01"), ("03", "07"), ("08", "06")])
def test_greedy_spina_o2_a_nie_je_horsi_ako_pesho(cp, hod, start, ciel):
    p = poz(cp, start, ciel)
    r, _ = greedy(hod, cp, p, PAR)
    assert len(r.kandidat.useky) <= 4
    assert r.hodnotenie.dekodovatelny
    for u in r.kandidat.useky:
        assert u.vystup in cp.zastavky_za(u.linka, u.nastup, p.datum)
    for a, b in zip(r.kandidat.useky, r.kandidat.useky[1:]):
        assert a.linka != b.linka  # nezopakuje linku dvakrát po sebe
    pesho = Hodnotitel(cp, PAR).ohodnot(type(r.kandidat)([]), p)
    assert r.hodnotenie.g <= pesho.g


def test_greedy_pouzije_dve_vyhodnotenia(cp, hod):
    r, _ = greedy(hod, cp, poz(cp, "01", "08"), PAR)
    assert r.pocet_vyhodnoteni == 2 == hod.pocet_vyhodnoteni


def test_greedy_bez_spojov_vrati_pesho(cp, hod):
    r, _ = greedy(hod, cp, poz(cp, "01", "03", NE), PAR)
    assert r.kandidat.useky == [] and r.hodnotenie.dekodovatelny
