"""Náhodná baseline: konštruktívne náhodné generovanie kandidátov, najlepší z N.

Implementuje osoba B.

nahodny_kandidat skladá trasu tak, aby vždy spĺňala O2 (výstup leží za
nástupom v smere jazdy linky, ktorá v daný deň premáva). O1 a O5 sú tiež
splnené konštrukciou (nástup do d_max od štartu, prestup do d_prestup), O1 pri
cieli a O6 (príchod do t0 + H) porušené byť môžu; O3 (žiadny spoj v časovom
okne) spôsobí nedekódovateľnosť – to odhalí až dekóder.
nahodne_hladanie generuje a hodnotí kandidátov cez Hodnotitel.ohodnot, kým
neminie rozpočet, a vráti najlepšieho podľa g.
"""

import random
import time
from collections import Counter
from dataclasses import dataclass, field

from mhd import geo
from mhd.evaluate import Hodnotitel
from mhd.gtfs import CestovnyPoriadok
from mhd.model import Hodnotenie, Kandidat, Poziadavka, Usek
from mhd.params import Parametre

MAX_USEKOV = 4
P_IBA_PESO = 0.05         # pravdepodobnosť trasy iba pešo
P_KONIEC_PRI_CIELI = 0.5  # pravdepodobnosť skončiť, ak je výstup do d_max od cieľa


class Pamat:
    """Pamäť odpovedí cestovného poriadku pre jednu požiadavku (zrýchlenie).

    Nemení výsledok – iba nepočíta znova to isté okolie, linky a zastávky za.
    Platí len pre jeden dátum (p.datum).
    """

    def __init__(self, cp: CestovnyPoriadok, p: Poziadavka):
        self.cp, self.p = cp, p
        self._okolie: dict[tuple, list[str]] = {}
        self._moznosti: dict[str, list[tuple[str, list[str]]]] = {}

    def okolie(self, bod: tuple[float, float], max_m: float) -> list[str]:
        """stop_id do pešej vzdialenosti max_m od bodu (od najbližšej)."""
        kluc = (bod, max_m)
        if kluc not in self._okolie:
            self._okolie[kluc] = [z for z, _ in self.cp.zastavky_v_okoli(bod, max_m)]
        return self._okolie[kluc]

    def moznosti(self, zastavka: str) -> list[tuple[str, list[str]]]:
        """[(linka, zastávky za nástupom)] – iba linky s neprázdnym zoznamom za."""
        if zastavka not in self._moznosti:
            d = self.p.datum
            self._moznosti[zastavka] = [
                (l, za) for l in self.cp.linky_na_zastavke(zastavka, d)
                if (za := self.cp.zastavky_za(l, zastavka, d))
            ]
        return self._moznosti[zastavka]


def nahodny_kandidat(
    cp: CestovnyPoriadok,
    p: Poziadavka,
    par: Parametre,
    rng: random.Random,
    pamat: Pamat | None = None,
) -> Kandidat:
    """Náhodný kandidát, ktorý vždy spĺňa O2 a má najviac 4 úseky.

    Postup: s pravdepodobnosťou 0,05 trasa iba pešo. Inak náhodná zastávka do
    d_max od štartu (z tých, kde v deň p.datum stojí linka so zastávkami za
    nástupom) → náhodná taká linka → náhodná zastávka za nástupom. Ak je výstup
    do d_max od cieľa, s pravdepodobnosťou 0,5 skončí (po 4. úseku vždy); inak
    prestúpi na náhodnú zastávku do d_prestup od výstupu a pokračuje. Ak sa
    z aktuálnej polohy nedá pokračovať, skončí s doterajšími úsekmi (bez úsekov
    vráti trasu iba pešo).

    Args:
        cp: cestovný poriadok.
        p: požiadavka (štart, cieľ, dátum).
        par: parametre (d_max, d_prestup).
        rng: generátor náhodných čísel (determinizmus cez seed).
        pamat: voliteľná Pamat pre opakované volania s tou istou požiadavkou.

    Returns:
        Kandidat s 0 až 4 úsekmi.
    """
    if pamat is None:
        pamat = Pamat(cp, p)
    if rng.random() < P_IBA_PESO:
        return Kandidat([])

    useky: list[Usek] = []
    bod, polomer = p.start, par.d_max
    while len(useky) < MAX_USEKOV:
        zastavky = [z for z in pamat.okolie(bod, polomer) if pamat.moznosti(z)]
        if not zastavky:
            break
        nastup = rng.choice(zastavky)
        linka, za = rng.choice(pamat.moznosti(nastup))
        vystup = rng.choice(za)
        useky.append(Usek(linka, nastup, vystup))

        bod = cp.suradnice(vystup)
        pri_cieli = geo.pesia_vzdialenost_m(bod, p.ciel, par) <= par.d_max
        if pri_cieli and rng.random() < P_KONIEC_PRI_CIELI:
            break
        polomer = par.d_prestup
    return Kandidat(useky)


@dataclass
class VysledokHladania:
    """Výsledok baseline metódy na jednej inštancii.

    Atribúty:
        kandidat: najlepší kandidát podľa g.
        hodnotenie: jeho Hodnotenie.
        pocet_vyhodnoteni: počet volaní Hodnotitel.ohodnot počas behu.
        pocet_pripustnych: koľko vyhodnotených kandidátov bolo prípustných.
        pocet_nepripustnych: dekódovateľných, ale s porušením O1/O5/O6.
        pocet_nedekodovatelnych: s g = inf (O2 – O4).
        porusenia: početnosť porušení cez všetkých kandidátov (napr. {'O3': 120}).
        cas_behu_s: čas behu [s].
    """

    kandidat: Kandidat
    hodnotenie: Hodnotenie
    pocet_vyhodnoteni: int
    pocet_pripustnych: int = 0
    pocet_nepripustnych: int = 0
    pocet_nedekodovatelnych: int = 0
    porusenia: Counter = field(default_factory=Counter)
    cas_behu_s: float = 0.0

    @property
    def pripustny(self) -> bool:
        """True, ak vrátené riešenie spĺňa všetky obmedzenia."""
        return self.hodnotenie.pripustny


def nahodne_hladanie(
    hodnotitel: Hodnotitel,
    cp: CestovnyPoriadok,
    p: Poziadavka,
    par: Parametre,
    rozpocet: int = 1000,
    seed: int = 0,
) -> VysledokHladania:
    """Generuje náhodných kandidátov, kým neminie rozpočet; vráti najlepšieho podľa g.

    Rozpočet = počet volaní hodnotitel.ohodnot. Neprípustní kandidáti sa
    nezahadzujú – porovnávajú sa podľa g, takže prípustný (g < λ) vždy vyhrá nad
    neprípustným; ak žiadny prípustný nie je, vráti sa najmenej porušujúci
    (hodnotenie.pripustny = False). Nedekódovateľní (g = inf) sa iba započítajú;
    ak sú nedekódovateľní všetci, vráti sa prvý z nich.

    Args:
        hodnotitel: Hodnotitel (jeho počítadlo sa zvýši presne o rozpocet).
        cp: cestovný poriadok.
        p: požiadavka.
        par: parametre.
        rozpocet: počet vyhodnotení (≥ 1).
        seed: seed generátora (rovnaký seed = rovnaký výsledok).
    """
    if rozpocet < 1:
        raise ValueError("rozpocet musí byť aspoň 1")
    t = time.perf_counter()
    rng = random.Random(seed)
    pamat = Pamat(cp, p)
    zaciatok = hodnotitel.pocet_vyhodnoteni

    najlepsi: Kandidat | None = None
    najlepsie_h: Hodnotenie | None = None
    pripustne = nepripustne = nedekodovatelne = 0
    porusenia: Counter = Counter()

    while hodnotitel.pocet_vyhodnoteni - zaciatok < rozpocet:
        k = nahodny_kandidat(cp, p, par, rng, pamat)
        h = hodnotitel.ohodnot(k, p)
        porusenia.update(h.porusenia)
        if not h.dekodovatelny:
            nedekodovatelne += 1
        elif h.pripustny:
            pripustne += 1
        else:
            nepripustne += 1
        if najlepsie_h is None or h.g < najlepsie_h.g:
            najlepsi, najlepsie_h = k, h

    return VysledokHladania(
        kandidat=najlepsi,
        hodnotenie=najlepsie_h,
        pocet_vyhodnoteni=hodnotitel.pocet_vyhodnoteni - zaciatok,
        pocet_pripustnych=pripustne,
        pocet_nepripustnych=nepripustne,
        pocet_nedekodovatelnych=nedekodovatelne,
        porusenia=porusenia,
        cas_behu_s=time.perf_counter() - t,
    )
