"""Dekóder a vyhodnotenie kandidáta (funkcie f a g, obmedzenia O1 – O6).

f(x) = (príchod − t0) / 60 + α · P            [min]
g(x) = f(x) + λ · V(x),  V = počet porušených z {O1, O5, O6}
Nedekódovateľný kandidát (O2 – O4): f = g = inf.
"""

from mhd.gtfs import CestovnyPoriadok
from mhd.model import Hodnotenie, Kandidat, Poziadavka
from mhd.params import Parametre


class Hodnotitel:
    """Ohodnocuje kandidátov voči cestovnému poriadku.

    Atribúty:
        cp: cestovný poriadok.
        par: parametre modelu.
        pocet_vyhodnoteni: počet volaní ohodnot (férový rozpočet metód).
    """

    def __init__(self, cp: CestovnyPoriadok, par: Parametre):
        self.cp = cp
        self.par = par
        self.pocet_vyhodnoteni: int = 0

    def ohodnot(self, k: Kandidat, p: Poziadavka) -> Hodnotenie:
        """Dekóduje kandidáta na itinerár a vypočíta f, g a porušenia.

        Zvýši pocet_vyhodnoteni pri každom volaní (aj pri nedekódovateľnom).

        Args:
            k: kandidát (0 až 4 úseky; [] = iba pešo).
            p: požiadavka (štart, cieľ, dátum, t0 v s).

        Returns:
            Hodnotenie s itinerárom, f a g v minútach a zoznamom porušení.
        """
        raise NotImplementedError
