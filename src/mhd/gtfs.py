"""Načítanie cestovného poriadku GTFS a indexy pre dekóder.

Časy sú v sekundách od polnoci prevádzkového dňa; hodnoty nad 24:00:00 sa
ponechávajú (napr. 25:10:00 = 90 600 s).

Zjednodušenie: spoje predchádzajúceho prevádzkového dňa s časmi po polnoci
sa neuvažujú (cesta po polnoci vidí iba spoje dňa `datum`).
"""

from datetime import date

from mhd.params import Parametre


class CestovnyPoriadok:
    """Cestovný poriadok MHD načítaný z GTFS (priečinok alebo .zip)."""

    @classmethod
    def nacitaj(cls, cesta: str) -> "CestovnyPoriadok":
        """Načíta GTFS z priečinka alebo .zip a vytvorí indexy.

        Priestorový index používa predvolené Parametre() (zachadzka).

        Args:
            cesta: cesta k priečinku alebo .zip so súbormi GTFS.

        Returns:
            Načítaný cestovný poriadok.
        """
        raise NotImplementedError

    def zastavky(self) -> list[str]:
        """Zoznam všetkých stop_id."""
        raise NotImplementedError

    def suradnice(self, stop_id: str) -> tuple[float, float]:
        """Súradnice zastávky (lat, lon) v stupňoch."""
        raise NotImplementedError

    def nazov(self, stop_id: str) -> str:
        """Názov zastávky (stop_name)."""
        raise NotImplementedError

    def zastavky_v_okoli(
        self, bod: tuple[float, float], max_m: float
    ) -> list[tuple[str, float]]:
        """Zastávky do pešej vzdialenosti max_m [m] od bodu.

        Deleguje na PriestorovyIndex (spatial.py).

        Returns:
            Zoznam (stop_id, pešia vzdialenosť po uliciach v m) zoradený od
            najbližšej.
        """
        raise NotImplementedError

    def linky_na_zastavke(self, stop_id: str, datum: date) -> list[str]:
        """Linky (route_id), ktorých aspoň jeden spoj v deň `datum` zastavuje na stop_id."""
        raise NotImplementedError

    def zastavky_za(self, linka: str, stop_id: str, datum: date) -> list[str]:
        """Zastávky dosiahnuteľné linkou zo stop_id v smere jazdy (O2).

        Uvažujú sa iba spoje aktívne v deň `datum`.
        """
        raise NotImplementedError

    def najblizsi_odchod(
        self, linka: str, nastup: str, vystup: str, od_casu: int, datum: date
    ) -> tuple[str, int, int] | None:
        """Prvý spoj linky aktívny v deň `datum`, ktorý odchádza z nástupnej
        zastávky najskôr v čase od_casu [s] a neskôr zastavuje na výstupnej.

        Args:
            linka: route_id.
            nastup: stop_id nástupnej zastávky.
            vystup: stop_id výstupnej zastávky.
            od_casu: najskorší čas odchodu [s od polnoci].
            datum: prevádzkový deň.

        Returns:
            (trip_id, odchod z nástupu [s], príchod na výstup [s]) alebo None.
        """
        raise NotImplementedError
