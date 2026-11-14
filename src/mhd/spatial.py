"""Priestorový index zastávok (hľadanie zastávok v okolí bodu).

Implementuje osoba B. V kostre sú iba hlavičky.
"""

from mhd.params import Parametre


class PriestorovyIndex:
    """Index zastávok na rýchle hľadanie zastávok do zadanej pešej vzdialenosti."""

    def __init__(self, suradnice: dict[str, tuple[float, float]], par: Parametre):
        """Vytvorí index.

        Args:
            suradnice: stop_id -> (lat, lon) v stupňoch.
            par: parametre modelu (zachadzka pre pešiu vzdialenosť).
        """
        raise NotImplementedError

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
        raise NotImplementedError
