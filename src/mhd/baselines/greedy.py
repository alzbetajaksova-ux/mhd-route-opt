"""Greedy baseline: po úsekoch vždy nastúpi na spoj s najlepším odhadom príchodu do cieľa.

Implementuje osoba B.

Z aktuálnej polohy a času preskúša všetky zastávky v dosahu (d_max zo štartu,
d_prestup pri prestupe), všetky ich linky a všetky zastávky za nástupom. Pre
každú trojicu (nástup, linka, výstup) nájde najbližší spoj (rovnako ako
dekóder: chôdza + min_prestup pri prestupe) a odhadne príchod do cieľa =
príchod na výstup + čas chôdze z výstupu do cieľa. Vyberie trojicu s
najmenším odhadom.

Koniec: výstup do d_max od cieľa, 4 úseky alebo z aktuálnej polohy už nejde
žiadny spoj v časovom okne. Úsek sa vyberie aj vtedy, keď odhad zhorší (napr.
dlhé čakanie) – greedy sa nevracia. Výsledok sa ohodnotí cez
Hodnotitel.ohodnot a porovná s trasou iba pešo.

(Vyskúšaný variant „skonči, ak ďalší úsek nezlepší odhad oproti chôdzi
z aktuálnej polohy" bol na 60 inštanciách mierne horší: priemerné f
prípustných 51,7 vs. 48,8 min.)
"""

import math
import time

from mhd import geo
from mhd.baselines.random_search import MAX_USEKOV, VysledokHladania
from mhd.evaluate import Hodnotitel
from mhd.gtfs import CestovnyPoriadok
from mhd.model import Kandidat, Poziadavka, Usek
from mhd.params import Parametre


def greedy(
    hodnotitel: Hodnotitel,
    cp: CestovnyPoriadok,
    p: Poziadavka,
    par: Parametre,
) -> tuple[VysledokHladania, int]:
    """Deterministická greedy trasa pre požiadavku p.

    Tú istú linku nepoužije dvakrát po sebe. Pri rovnakom odhade rozhoduje
    lexikografické poradie (nástup, linka, výstup), takže výsledok je vždy
    rovnaký. Kandidát je vždy dekódovateľný (spoje hľadá rovnako ako dekóder),
    ale môže byť neprípustný – napr. posledná zastávka ostane ďalej ako d_max od
    cieľa (O1) alebo príchod po t0 + H (O6); vráti sa aj tak, s pripustny = False.

    Args:
        hodnotitel: Hodnotitel (použijú sa 2 vyhodnotenia: greedy trasa a iba pešo).
        cp: cestovný poriadok.
        p: požiadavka.
        par: parametre.

    Returns:
        (VysledokHladania s lepšou z dvojice greedy / iba pešo podľa g,
         počet volaní cp.najblizsi_odchod).
    """
    t_start = time.perf_counter()
    zaciatok = hodnotitel.pocet_vyhodnoteni
    limit = p.cas_odchodu + par.horizont
    volani = 0

    useky: list[Usek] = []
    bod, cas, polomer = p.start, p.cas_odchodu, par.d_max
    predosla_linka: str | None = None

    while len(useky) < MAX_USEKOV:
        najlepsi_odhad, najlepsi = math.inf, None

        for nastup, d in cp.zastavky_v_okoli(bod, polomer):
            pripraveny = cas + geo.cas_chodze_s(d, par) + (par.min_prestup if useky else 0)
            for linka in cp.linky_na_zastavke(nastup, p.datum):
                if linka == predosla_linka:
                    continue
                for vystup in cp.zastavky_za(linka, nastup, p.datum):
                    volani += 1
                    spoj = cp.najblizsi_odchod(linka, nastup, vystup, pripraveny, p.datum)
                    if spoj is None or spoj[1] > limit:
                        continue
                    _, s = _chodza(cp.suradnice(vystup), p.ciel, par)
                    odhad = spoj[2] + s
                    kluc = (odhad, nastup, linka, vystup)
                    if odhad < najlepsi_odhad or (najlepsi and odhad == najlepsi_odhad
                                                  and kluc < najlepsi[0]):
                        najlepsi_odhad, najlepsi = odhad, (kluc, spoj[2])

        if najlepsi is None:
            break  # z aktuálnej polohy už nejde žiadny spoj v časovom okne
        (_, nastup, linka, vystup), prichod = najlepsi
        useky.append(Usek(linka, nastup, vystup))
        bod, cas, polomer = cp.suradnice(vystup), prichod, par.d_prestup
        predosla_linka = linka
        if geo.pesia_vzdialenost_m(bod, p.ciel, par) <= par.d_max:
            break

    k_greedy = Kandidat(useky)
    h_greedy = hodnotitel.ohodnot(k_greedy, p)
    k_peso = Kandidat([])
    h_peso = hodnotitel.ohodnot(k_peso, p)
    k, h = (k_greedy, h_greedy) if h_greedy.g <= h_peso.g else (k_peso, h_peso)

    vysledok = VysledokHladania(
        kandidat=k,
        hodnotenie=h,
        pocet_vyhodnoteni=hodnotitel.pocet_vyhodnoteni - zaciatok,
        pocet_pripustnych=h_greedy.pripustny + h_peso.pripustny,
        pocet_nepripustnych=(h_greedy.dekodovatelny and not h_greedy.pripustny)
        + (h_peso.dekodovatelny and not h_peso.pripustny),
        pocet_nedekodovatelnych=(not h_greedy.dekodovatelny) + (not h_peso.dekodovatelny),
        cas_behu_s=time.perf_counter() - t_start,
    )
    vysledok.porusenia.update(h_greedy.porusenia)
    vysledok.porusenia.update(h_peso.porusenia)
    return vysledok, volani


def _chodza(a: tuple[float, float], b: tuple[float, float], par: Parametre) -> tuple[float, int]:
    d = geo.pesia_vzdialenost_m(a, b, par)
    return d, geo.cas_chodze_s(d, par)
