"""Priestorový index zastávok (hľadanie zastávok v okolí bodu).

Implementuje osoba A (po dohode prevzaté od osoby B).
Používa BallTree z scikit-learn s haversinovou metrikou; vrátené vzdialenosti
sa prepočítajú cez geo.pesia_vzdialenost_m, aby presne sedeli s dekóderom.
"""

import numpy as np
from sklearn.neighbors import BallTree

from mhd import geo
from mhd.params import Parametre


class PriestorovyIndex:
    """Index zastávok na rýchle hľadanie zastávok do zadanej pešej vzdialenosti."""

    def __init__(self, suradnice: dict[str, tuple[float, float]], par: Parametre):
        """Vytvorí index.

        Args:
            suradnice: stop_id -> (lat, lon) v stupňoch.
            par: parametre modelu (zachadzka pre pešiu vzdialenosť).
        """
        self.par = par
        self.ids = list(suradnice)
        self.body = [suradnice[s] for s in self.ids]
        self._strom = (
            BallTree(np.radians(np.array(self.body, dtype=float)), metric="haversine")
            if self.body else None
        )

    def v_okoli(
        self, bod: tuple[float, float], max_m: float
    ) -> list[tuple[str, float]]:
        """Zastávky do pešej vzdialenosti max_m [m] od bodu.

        Args:
            bod: (lat, lon) v stupňoch.
            max_m: max. pešia vzdialenosť (po uliciach) v metroch.

        Returns:
            Zoznam (stop_id, pešia vzdialenosť v m) zoradený vzostupne.
        """
        if self._strom is None or max_m < 0:
            return []
        # polomer v radiánoch so zásobou; presný filter nižšie
        polomer = max_m / self.par.zachadzka / geo.POLOMER_ZEME_M * 1.000001 + 1e-12
        indexy = self._strom.query_radius(np.radians([bod]), r=polomer)[0]
        vysledok = []
        for i in indexy:
            d = geo.pesia_vzdialenost_m(bod, self.body[i], self.par)
            if d <= max_m:
                vysledok.append((self.ids[i], d))
        vysledok.sort(key=lambda t: (t[1], t[0]))
        return vysledok
