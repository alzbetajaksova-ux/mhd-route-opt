"""Načítanie cestovného poriadku GTFS a indexy pre dekóder.

Časy sú v sekundách od polnoci prevádzkového dňa; hodnoty nad 24:00:00 sa
ponechávajú (napr. 25:10:00 = 90 600 s).

Zjednodušenie: spoje predchádzajúceho prevádzkového dňa s časmi po polnoci
sa neuvažujú (cesta po polnoci vidí iba spoje dňa `datum`).
"""

import hashlib
import io
import pickle
import zipfile
from bisect import bisect_left
from collections import defaultdict
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from mhd import spatial
from mhd.params import Parametre

_ID_STLPCE = {
    "route_id": str, "stop_id": str, "trip_id": str, "service_id": str,
    "agency_id": str, "date": str, "start_date": str, "end_date": str,
}
_DNI = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
_CACHE_VERZIA = "1"  # zvýš pri zmene indexov, aby sa stará cache nepoužila
_CACHE_MIN_BAJTOV = 1_000_000  # malé feedy (toy GTFS) sa nekešujú


def _cache_subor(cesta: Path) -> Path | None:
    """Cesta k pickle cache v <rodič>/cache/ alebo None (malý feed).

    Kľúč = veľkosť a čas zmeny zdrojových súborov, takže zmena dát cache zneplatní.
    """
    subory = [cesta] if cesta.is_file() else sorted(cesta.glob("*.txt"))
    if sum(s.stat().st_size for s in subory) < _CACHE_MIN_BAJTOV:
        return None
    h = hashlib.sha1(_CACHE_VERZIA.encode())
    for s in subory:
        st = s.stat()
        h.update(f"{s.name}:{st.st_size}:{st.st_mtime_ns}".encode())
    return cesta.parent / "cache" / f"gtfs_{h.hexdigest()[:12]}.pkl"


def cas_na_sekundy(hodnoty: pd.Series) -> np.ndarray:
    """Prevedie časy 'HH:MM:SS' (aj > 24:00:00) na sekundy od polnoci [s]."""
    casti = hodnoty.str.strip().str.split(":", expand=True).astype(np.int64)
    return (casti[0] * 3600 + casti[1] * 60 + casti[2]).to_numpy()


def _citaj(cesta: Path, nazov: str, stlpce: list[str] | None = None) -> pd.DataFrame:
    """Prečíta jeden súbor GTFS z priečinka alebo .zip; ID stĺpce ako str."""
    if cesta.suffix.lower() == ".zip":
        with zipfile.ZipFile(cesta) as z:
            zdroj = io.BytesIO(z.read(nazov))
    else:
        zdroj = cesta / nazov
    return pd.read_csv(zdroj, dtype=_ID_STLPCE, usecols=stlpce, encoding="utf-8-sig")


class CestovnyPoriadok:
    """Cestovný poriadok MHD načítaný z GTFS (priečinok alebo .zip).

    Indexy (vytvorené v `nacitaj`):
        odchody[(route_id, stop_id)] = (časy [s], trip_id, stop_sequence),
            tri zoznamy zoradené podľa času odchodu (binárne vyhľadávanie);
        trip_zastavky[trip_id] = {stop_id: (stop_sequence, príchod [s])};
            ak spoj zastavuje na zastávke viackrát, ostane posledný výskyt;
        za[(route_id, stop_id)] = {service_id: množina zastávok za ňou};
        linky_sluzby[stop_id] = {service_id: množina route_id}.
    """

    def __init__(self) -> None:
        self._suradnice: dict[str, tuple[float, float]] = {}
        self._nazvy: dict[str, str] = {}
        self.trip_linka: dict[str, str] = {}
        self.trip_sluzba: dict[str, str] = {}
        self.odchody: dict[tuple[str, str], tuple[list[int], list[str], list[int]]] = {}
        self.trip_zastavky: dict[str, dict[str, tuple[int, int]]] = {}
        self.za: dict[tuple[str, str], dict[str, set[str]]] = {}
        self.linky_sluzby: dict[str, dict[str, set[str]]] = {}
        self._kalendar: pd.DataFrame | None = None
        self._vynimky: dict[str, list[tuple[str, int]]] = {}
        self._aktivne_cache: dict[date, frozenset[str]] = {}
        self._index: spatial.PriestorovyIndex | None = None
        self.pocet_liniek = 0

    # ------------------------------------------------------------ načítanie
    @classmethod
    def nacitaj(cls, cesta: str) -> "CestovnyPoriadok":
        """Načíta GTFS z priečinka alebo .zip a vytvorí indexy.

        Priestorový index používa predvolené Parametre() (zachadzka).
        Hotové indexy veľkého feedu sa uložia do <rodič cesty>/cache/*.pkl
        (napr. data/cache/) a pri ďalšom načítaní sa použijú.

        Args:
            cesta: cesta k priečinku alebo .zip so súbormi GTFS.
        """
        cesta = Path(cesta)
        cache = _cache_subor(cesta)
        if cache is not None and cache.is_file():
            # pickle je bezpečný: súbor vytvára iba tento kód lokálne a je v .gitignore
            try:
                with open(cache, "rb") as f:
                    return pickle.load(f)
            except Exception:
                pass  # poškodená cache – načítame znova
        cp = cls._nacitaj_csv(cesta)
        if cache is not None:
            try:
                cache.parent.mkdir(parents=True, exist_ok=True)
                with open(cache, "wb") as f:
                    pickle.dump(cp, f, protocol=pickle.HIGHEST_PROTOCOL)
            except OSError:
                pass
        return cp

    @classmethod
    def _nacitaj_csv(cls, cesta: Path) -> "CestovnyPoriadok":
        cp = cls()

        stops = _citaj(cesta, "stops.txt", ["stop_id", "stop_name", "stop_lat", "stop_lon"])
        cp._suradnice = {
            s: (float(la), float(lo))
            for s, la, lo in zip(stops.stop_id, stops.stop_lat, stops.stop_lon)
        }
        cp._nazvy = dict(zip(stops.stop_id, stops.stop_name.fillna("")))

        cp.pocet_liniek = len(_citaj(cesta, "routes.txt", ["route_id"]))
        trips = _citaj(cesta, "trips.txt", ["route_id", "service_id", "trip_id"])
        cp.trip_linka = dict(zip(trips.trip_id, trips.route_id))
        cp.trip_sluzba = dict(zip(trips.trip_id, trips.service_id))

        cp._nacitaj_kalendar(cesta)
        cp._vytvor_indexy(
            _citaj(cesta, "stop_times.txt",
                   ["trip_id", "arrival_time", "departure_time", "stop_id", "stop_sequence"])
        )
        return cp

    def _nacitaj_kalendar(self, cesta: Path) -> None:
        try:
            kal = _citaj(cesta, "calendar.txt")
            kal["od"] = kal.start_date.astype(int)
            kal["do"] = kal.end_date.astype(int)
            self._kalendar = kal
        except (FileNotFoundError, KeyError):
            self._kalendar = None
        try:
            vyn = _citaj(cesta, "calendar_dates.txt")
            for s, d, t in zip(vyn.service_id, vyn.date, vyn.exception_type):
                self._vynimky.setdefault(d, []).append((s, int(t)))
        except (FileNotFoundError, KeyError):
            pass

    def _vytvor_indexy(self, st: pd.DataFrame) -> None:
        st = st.dropna(subset=["arrival_time", "departure_time"])
        prichod = cas_na_sekundy(st.arrival_time)
        odchod = cas_na_sekundy(st.departure_time)
        st = st.assign(prichod=prichod, odchod=odchod)
        st = st.assign(route_id=st.trip_id.map(self.trip_linka))
        st = st.sort_values(["trip_id", "stop_sequence"], kind="stable")

        trip_ids = st.trip_id.to_numpy()
        stop_ids = st.stop_id.to_numpy()
        seqs = st.stop_sequence.to_numpy(dtype=np.int64).tolist()
        prichody = st.prichod.to_numpy().tolist()
        odchody = st.odchod.to_numpy().tolist()

        surove: dict[tuple[str, str], list[tuple[int, str, int]]] = defaultdict(list)
        vzory: set[tuple[str, str, tuple[str, ...]]] = set()

        hranice = np.flatnonzero(trip_ids[1:] != trip_ids[:-1]) + 1
        zaciatky = [0, *hranice.tolist()]
        konce = [*hranice.tolist(), len(trip_ids)]
        for i0, i1 in zip(zaciatky, konce):
            trip = trip_ids[i0]
            linka = self.trip_linka[trip]
            zast = stop_ids[i0:i1]
            self.trip_zastavky[trip] = {
                s: (q, p) for s, q, p in zip(zast, seqs[i0:i1], prichody[i0:i1])
            }
            for s, q, o in zip(zast, seqs[i0:i1], odchody[i0:i1]):
                surove[(linka, s)].append((o, trip, q))
            vzory.add((linka, self.trip_sluzba[trip], tuple(zast)))

        for kluc, zoznam in surove.items():
            zoznam.sort()
            self.odchody[kluc] = (
                [z[0] for z in zoznam], [z[1] for z in zoznam], [z[2] for z in zoznam]
            )

        # zastávky za danou zastávkou a linky na zastávke – podľa služby
        for linka, sluzba, zast in vzory:
            for i, s in enumerate(zast):
                self.za.setdefault((linka, s), {}).setdefault(sluzba, set()).update(zast[i + 1:])
                self.linky_sluzby.setdefault(s, {}).setdefault(sluzba, set()).add(linka)

    # ------------------------------------------------------------ kalendár
    def aktivne_sluzby(self, datum: date) -> frozenset[str]:
        """Množina service_id aktívnych v deň `datum` (výsledok sa kešuje).

        calendar.txt (deň v týždni + start_date – end_date), potom výnimky
        z calendar_dates.txt (1 = pridaná, 2 = zrušená).
        """
        if datum in self._aktivne_cache:
            return self._aktivne_cache[datum]
        aktivne: set[str] = set()
        cislo = int(datum.strftime("%Y%m%d"))
        if self._kalendar is not None:
            k = self._kalendar
            maska = (k[_DNI[datum.weekday()]].astype(int) == 1) & (k.od <= cislo) & (k["do"] >= cislo)
            aktivne.update(k.service_id[maska])
        for sluzba, typ in self._vynimky.get(str(cislo), []):
            if typ == 1:
                aktivne.add(sluzba)
            elif typ == 2:
                aktivne.discard(sluzba)
        vysledok = frozenset(aktivne)
        self._aktivne_cache[datum] = vysledok
        return vysledok

    # ------------------------------------------------------------ zastávky
    def zastavky(self) -> list[str]:
        """Zoznam všetkých stop_id."""
        return list(self._suradnice)

    def je_zastavka(self, stop_id: str) -> bool:
        """True, ak stop_id existuje v stops.txt."""
        return stop_id in self._suradnice

    def suradnice(self, stop_id: str) -> tuple[float, float]:
        """Súradnice zastávky (lat, lon) v stupňoch."""
        return self._suradnice[stop_id]

    def nazov(self, stop_id: str) -> str:
        """Názov zastávky (stop_name)."""
        return self._nazvy[stop_id]

    def zastavky_v_okoli(
        self, bod: tuple[float, float], max_m: float
    ) -> list[tuple[str, float]]:
        """Zastávky do pešej vzdialenosti max_m [m] od bodu.

        Deleguje na PriestorovyIndex (spatial.py, osoba B); index sa vytvorí
        pri prvom volaní.

        Returns:
            Zoznam (stop_id, pešia vzdialenosť po uliciach v m) zoradený od
            najbližšej.
        """
        if self._index is None:
            self._index = spatial.PriestorovyIndex(self._suradnice, Parametre())
        return self._index.v_okoli(bod, max_m)

    # ------------------------------------------------------------ linky
    def linky_na_zastavke(self, stop_id: str, datum: date) -> list[str]:
        """Linky (route_id), ktorých aspoň jeden spoj v deň `datum` zastavuje na stop_id."""
        aktivne = self.aktivne_sluzby(datum)
        linky: set[str] = set()
        for sluzba, mnozina in self.linky_sluzby.get(stop_id, {}).items():
            if sluzba in aktivne:
                linky |= mnozina
        return sorted(linky)

    def _za(self, linka: str, stop_id: str, aktivne: frozenset[str]) -> set[str]:
        vysledok: set[str] = set()
        for sluzba, mnozina in self.za.get((linka, stop_id), {}).items():
            if sluzba in aktivne:
                vysledok |= mnozina
        return vysledok

    def zastavky_za(self, linka: str, stop_id: str, datum: date) -> list[str]:
        """Zastávky dosiahnuteľné linkou zo stop_id v smere jazdy (O2).

        Uvažujú sa iba spoje aktívne v deň `datum`; zoznam je zoradený podľa stop_id.
        """
        za = self._za(linka, stop_id, self.aktivne_sluzby(datum))
        za.discard(stop_id)
        return sorted(za)

    def najblizsi_odchod(
        self, linka: str, nastup: str, vystup: str, od_casu: int, datum: date
    ) -> tuple[str, int, int] | None:
        """Prvý spoj linky aktívny v deň `datum`, ktorý odchádza z nástupnej
        zastávky najskôr v čase od_casu [s] a neskôr (vyššia stop_sequence)
        zastavuje na výstupnej.

        Binárne vyhľadá prvý odchod >= od_casu a prechádza ďalšie odchody.

        Args:
            linka: route_id.
            nastup: stop_id nástupnej zastávky.
            vystup: stop_id výstupnej zastávky.
            od_casu: najskorší čas odchodu [s od polnoci].
            datum: prevádzkový deň.

        Returns:
            (trip_id, odchod z nástupu [s], príchod na výstup [s]) alebo None.
        """
        aktivne = self.aktivne_sluzby(datum)
        if vystup not in self._za(linka, nastup, aktivne):
            return None  # linka v tento deň nespojí zastávky v tomto smere
        index = self.odchody.get((linka, nastup))
        if index is None:
            return None
        casy, tripy, seqy = index
        sluzba = self.trip_sluzba
        trip_zast = self.trip_zastavky
        for i in range(bisect_left(casy, od_casu), len(casy)):
            trip = tripy[i]
            if sluzba[trip] not in aktivne:
                continue
            ciel = trip_zast[trip].get(vystup)
            if ciel is not None and ciel[0] > seqy[i]:
                return trip, casy[i], ciel[1]
        return None

    # ------------------------------------------------------------ súhrn
    def pocty(self) -> tuple[int, int, int]:
        """(počet liniek, zastávok, spojov)."""
        return self.pocet_liniek, len(self._suradnice), len(self.trip_linka)
