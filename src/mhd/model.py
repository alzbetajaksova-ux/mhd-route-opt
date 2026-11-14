"""Dátové triedy modelu – spoločný kontrakt tímu.

Mená, typy a jednotky sa nemenia bez dohody všetkých troch členov.
Časy sú v sekundách od polnoci prevádzkového dňa (môžu byť > 86 400 pri
spojoch po polnoci), vzdialenosti v metroch, f a g v minútach.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Literal


@dataclass(frozen=True)
class Usek:
    """Gén kandidáta – jeden úsek jazdy.

    Atribúty:
        linka: route_id z GTFS.
        nastup: stop_id nástupnej zastávky.
        vystup: stop_id výstupnej zastávky.
    """

    linka: str
    nastup: str
    vystup: str


@dataclass
class Kandidat:
    """Genotyp – zoznam 0 až 4 úsekov; [] = trasa iba pešo.

    Počet prestupov P = max(0, len(useky) - 1). Pešie presuny, čakanie ani
    konkrétne spoje nie sú súčasťou kandidáta – dopočíta ich dekóder.
    """

    useky: list[Usek]


@dataclass(frozen=True)
class Poziadavka:
    """Inštancia úlohy (požiadavka cestujúceho).

    Atribúty:
        id: identifikátor inštancie.
        start: poloha štartu o ako (lat, lon) v stupňoch WGS84.
        ciel: poloha cieľa d ako (lat, lon) v stupňoch WGS84.
        datum: dátum cesty (prevádzkový deň).
        cas_odchodu: čas odchodu t0 [s od polnoci].
    """

    id: str
    start: tuple[float, float]
    ciel: tuple[float, float]
    datum: date
    cas_odchodu: int


@dataclass
class CastTrasy:
    """Jedna časť itinerára (fenotyp).

    Atribúty:
        typ: 'chodza', 'cakanie' alebo 'jazda'.
        od: stop_id alebo 'start'.
        do: stop_id alebo 'ciel'.
        cas_od: začiatok časti [s od polnoci].
        cas_do: koniec časti [s od polnoci].
        linka: route_id (iba pri jazde).
        trip_id: trip_id spoja (iba pri jazde).
        vzdialenost_m: pešia vzdialenosť [m] (iba pri chôdzi).
    """

    typ: Literal["chodza", "cakanie", "jazda"]
    od: str
    do: str
    cas_od: int
    cas_do: int
    linka: str | None = None
    trip_id: str | None = None
    vzdialenost_m: float = 0.0


@dataclass
class Hodnotenie:
    """Výsledok vyhodnotenia kandidáta.

    Atribúty:
        itinerar: dekódovaný itinerár (chôdza, čakanie, jazda).
        celkovy_cas_s: príchod − t0 [s].
        prestupy: počet prestupov P [-].
        chodza_m: celková pešia vzdialenosť [m].
        f: cieľová funkcia [min]; inf, ak je kandidát nedekódovateľný.
        g: ohodnocovacia funkcia f + λ·V [min]; inf, ak je nedekódovateľný.
        pripustny: True, ak kandidát spĺňa O1 – O6.
        dekodovatelny: False, ak pre niektorý úsek neexistuje spoj (O2 – O4).
        porusenia: porušené obmedzenia, napr. ['O1', 'O5'].
    """

    itinerar: list[CastTrasy]
    celkovy_cas_s: int
    prestupy: int
    chodza_m: float
    f: float
    g: float
    pripustny: bool
    dekodovatelny: bool
    porusenia: list[str] = field(default_factory=list)
