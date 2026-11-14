"""Dekóder a vyhodnotenie kandidáta (funkcie f a g, obmedzenia O1 – O6).

f(x) = (príchod − t0) / 60 + α · P            [min]
g(x) = f(x) + λ · V(x),  V = počet porušených z {O1, O5, O6}
Nedekódovateľný kandidát (O2 – O4): f = g = inf.
"""

import math

from mhd import geo
from mhd.gtfs import CestovnyPoriadok
from mhd.model import CastTrasy, Hodnotenie, Kandidat, Poziadavka
from mhd.params import Parametre

INF = math.inf


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

    def _chodza(self, a: tuple[float, float], b: tuple[float, float]) -> tuple[float, int]:
        """(pešia vzdialenosť [m], čas chôdze [s])."""
        d = geo.pesia_vzdialenost_m(a, b, self.par)
        return d, geo.cas_chodze_s(d, self.par)

    def ohodnot(self, k: Kandidat, p: Poziadavka) -> Hodnotenie:
        """Dekóduje kandidáta na itinerár a vypočíta f, g a porušenia.

        Postup: chôdza štart → b1 (O1); pre každý úsek i > 0 chôdza
        a(i−1) → b(i) (0 m pri tej istej zastávke, O5) + min_prestup [s];
        najbližší odchod od aktuálneho času; čakanie a jazda; chôdza a(k) → cieľ
        (O1); O6 (počet prestupov, príchod do t0 + H). Časti itinerára s nulovou
        dĺžkou (čakanie, chôdza na tej istej zastávke) sa vynechajú;
        min_prestup je súčasťou čakania.

        Zvýši pocet_vyhodnoteni pri každom volaní (aj pri nedekódovateľnom).

        Args:
            k: kandidát (0 až 4 úseky; [] = iba pešo).
            p: požiadavka (štart, cieľ, dátum, t0 v s).

        Returns:
            Hodnotenie s itinerárom, f a g v minútach a zoznamom porušení.
        """
        self.pocet_vyhodnoteni += 1
        par, cp = self.par, self.cp
        t0 = p.cas_odchodu
        limit = t0 + par.horizont
        useky = k.useky
        itinerar: list[CastTrasy] = []
        porusenia: list[str] = []

        # trasa iba pešo
        if not useky:
            d, s = self._chodza(p.start, p.ciel)
            itinerar.append(CastTrasy("chodza", "start", "ciel", t0, t0 + s, vzdialenost_m=d))
            if t0 + s > limit:
                porusenia.append("O6")
            return self._vysledok(itinerar, t0, t0 + s, 0, d, porusenia)

        prestupy = len(useky) - 1
        t = t0
        chodza_m = 0.0
        predosla: str | None = None  # posledná výstupná zastávka

        for i, u in enumerate(useky):
            # chôdza na nástupnú zastávku
            if predosla is None:
                d, s = self._chodza(p.start, cp.suradnice(u.nastup))
                if d > par.d_max:
                    porusenia.append("O1")
                od = "start"
            else:
                if predosla == u.nastup:
                    d, s = 0.0, 0
                else:
                    d, s = self._chodza(cp.suradnice(predosla), cp.suradnice(u.nastup))
                if d > par.d_prestup and "O5" not in porusenia:
                    porusenia.append("O5")
                od = predosla
            if s > 0 or od == "start":
                itinerar.append(CastTrasy("chodza", od, u.nastup, t, t + s, vzdialenost_m=d))
            chodza_m += d
            t += s
            pripraveny = t + (par.min_prestup if i > 0 else 0)

            # najbližší spoj (O2 – O4)
            spoj = cp.najblizsi_odchod(u.linka, u.nastup, u.vystup, pripraveny, p.datum)
            if spoj is None or spoj[1] > limit:
                existuje = spoj is not None or cp.najblizsi_odchod(
                    u.linka, u.nastup, u.vystup, 0, p.datum) is not None
                porusenia.append("O3" if existuje else "O2")
                return Hodnotenie(itinerar, t - t0, prestupy, chodza_m, INF, INF,
                                  False, False, porusenia)
            trip_id, odchod, prichod = spoj
            if odchod > t:
                itinerar.append(CastTrasy("cakanie", u.nastup, u.nastup, t, odchod))
            itinerar.append(CastTrasy("jazda", u.nastup, u.vystup, odchod, prichod,
                                      linka=u.linka, trip_id=trip_id))
            t = prichod
            predosla = u.vystup

        # chôdza do cieľa
        d, s = self._chodza(cp.suradnice(predosla), p.ciel)
        if d > par.d_max and "O1" not in porusenia:
            porusenia.append("O1")
        itinerar.append(CastTrasy("chodza", predosla, "ciel", t, t + s, vzdialenost_m=d))
        chodza_m += d
        t += s

        if prestupy > par.max_prestupov or t > limit:
            porusenia.append("O6")
        return self._vysledok(itinerar, t0, t, prestupy, chodza_m, porusenia)

    def _vysledok(self, itinerar, t0, prichod, prestupy, chodza_m, porusenia) -> Hodnotenie:
        f = (prichod - t0) / 60 + self.par.penalizacia_prestupu * prestupy
        g = f + self.par.penalizacia_porusenia * len(porusenia)
        return Hodnotenie(itinerar, prichod - t0, prestupy, chodza_m, f, g,
                          not porusenia, True, sorted(porusenia))
