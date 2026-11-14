"""Geometria: pešia vzdialenosť a čas chôdze.

Implementuje osoba B. V kostre sú iba hlavičky.
"""

from mhd.params import Parametre


def pesia_vzdialenost_m(
    a: tuple[float, float], b: tuple[float, float], par: Parametre
) -> float:
    """Pešia vzdialenosť po uliciach medzi bodmi a, b [m].

    Počíta sa ako haversinova (vzdušná) vzdialenosť · par.zachadzka.

    Args:
        a: bod (lat, lon) v stupňoch.
        b: bod (lat, lon) v stupňoch.
        par: parametre modelu.

    Returns:
        Vzdialenosť v metroch.
    """
    raise NotImplementedError


def cas_chodze_s(vzdialenost_m: float, par: Parametre) -> int:
    """Čas chôdze [s] pre pešiu vzdialenosť [m], zaokrúhlený nahor.

    Args:
        vzdialenost_m: pešia vzdialenosť v metroch.
        par: parametre modelu (rychlost_chodze v m/s).

    Returns:
        ceil(vzdialenost_m / par.rychlost_chodze) v sekundách.
    """
    raise NotImplementedError
