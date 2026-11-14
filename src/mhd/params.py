"""Parametre modelu (spoločné pre všetky inštancie).

Hodnoty zodpovedajú opravenej analýze (odovzdávka 1 + pripomienky cvičiaceho).
Jednotky sú uvedené pri každom parametri.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Parametre:
    """Parametre modelu.

    Atribúty:
        rychlost_chodze: rýchlosť chôdze v [m/s].
        zachadzka: koeficient zachádzky c [-]; pešia vzdialenosť =
            haversine · c (vzdialenosť po uliciach).
        d_max: max. pešia vzdialenosť štart → prvá nástupná a posledná
            výstupná → cieľ [m] (obmedzenie O1).
        d_prestup: max. pešia vzdialenosť pri prestupe d_tr [m] (O5).
        min_prestup: min. čas na prestup τ [s]; pripočíta sa ku každému
            prestupu, aj na tej istej zastávke (O3).
        max_prestupov: max. počet prestupov K_max [-] (O6).
        horizont: časový horizont H [s]; príchod najneskôr t0 + H (O6) a
            odchod každého spoja najneskôr t0 + H (dekóder).
        penalizacia_prestupu: penalizácia prestupu α [min] v f(x).
        penalizacia_porusenia: penalizácia porušenia λ [min] v g(x).
    """

    rychlost_chodze: float = 1.3
    zachadzka: float = 1.3
    d_max: float = 800.0
    d_prestup: float = 400.0
    min_prestup: int = 60
    max_prestupov: int = 3
    horizont: int = 10800
    penalizacia_prestupu: float = 5.0
    penalizacia_porusenia: float = 200.0
