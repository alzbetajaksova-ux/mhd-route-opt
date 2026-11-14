"""Geometria: pešia vzdialenosť a čas chôdze.

Implementuje osoba A (po dohode prevzaté od osoby B).
Pešia vzdialenosť = haversinova vzdialenosť (R = 6 371 000 m) · zachadzka.
"""

import math

from mhd.params import Parametre

POLOMER_ZEME_M = 6_371_000.0


def haversine_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Vzdušná (haversinova) vzdialenosť bodov a, b [m].

    Args:
        a: bod (lat, lon) v stupňoch.
        b: bod (lat, lon) v stupňoch.
    """
    f1, f2 = math.radians(a[0]), math.radians(b[0])
    df = f2 - f1
    dl = math.radians(b[1] - a[1])
    x = math.sin(df / 2) ** 2 + math.cos(f1) * math.cos(f2) * math.sin(dl / 2) ** 2
    return 2 * POLOMER_ZEME_M * math.asin(math.sqrt(min(1.0, x)))


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
    return haversine_m(a, b) * par.zachadzka


def cas_chodze_s(vzdialenost_m: float, par: Parametre) -> int:
    """Čas chôdze [s] pre pešiu vzdialenosť [m], zaokrúhlený nahor.

    Args:
        vzdialenost_m: pešia vzdialenosť v metroch.
        par: parametre modelu (rychlost_chodze v m/s).

    Returns:
        ceil(vzdialenost_m / par.rychlost_chodze) v sekundách.
    """
    return math.ceil(vzdialenost_m / par.rychlost_chodze)
