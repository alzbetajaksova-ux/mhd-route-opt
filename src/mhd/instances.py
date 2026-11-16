"""Generovanie a načítanie inštancií (požiadaviek cestujúcich).

Implementuje osoba B.

Inštancia = dvojica štart–cieľ v jednom z troch časov odchodu. Dvojice sa delia
do skupín podľa vzdušnej (haversinovej) vzdialenosti štart–cieľ:
K (krátke, 1–3 km), S (stredné, 3–7 km), D (dlhé, nad 7 km).
Bod štartu/cieľa = súradnice náhodnej zastávky posunuté o 100–600 m náhodným
smerom; prijme sa, iba ak má aspoň jednu zastávku do d_max pešej vzdialenosti.

id inštancie: '{skupina}{poradie:02d}-{cas}', napr. 'S03-ut0730'.
"""

import json
import math
import random
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from mhd import geo
from mhd.gtfs import CestovnyPoriadok
from mhd.model import Poziadavka
from mhd.params import Parametre


@dataclass(frozen=True)
class Pasmo:
    """Skupina inštancií podľa vzdušnej vzdialenosti štart–cieľ.

    Atribúty:
        prefix: písmeno skupiny ('K', 'S', 'D').
        pocet: počet dvojíc štart–cieľ v skupine.
        od_m: dolná hranica vzdušnej vzdialenosti [m] (vrátane).
        do_m: horná hranica vzdušnej vzdialenosti [m] (bez nej; inf = bez limitu).
    """

    prefix: str
    pocet: int
    od_m: float
    do_m: float


@dataclass(frozen=True)
class CasOdchodu:
    """Čas odchodu, v ktorom sa použije každá dvojica.

    Atribúty:
        kod: krátky kód do id inštancie, napr. 'ut0730'.
        datum: dátum cesty.
        cas_s: čas odchodu t0 [s od polnoci].
    """

    kod: str
    datum: date
    cas_s: int


PASMA: tuple[Pasmo, ...] = (
    Pasmo("K", 6, 1_000.0, 3_000.0),
    Pasmo("S", 8, 3_000.0, 7_000.0),
    Pasmo("D", 6, 7_000.0, math.inf),
)

CASY: tuple[CasOdchodu, ...] = (
    CasOdchodu("ut0730", date(2026, 11, 24), 7 * 3600 + 30 * 60),  # utorok, špička
    CasOdchodu("ut1300", date(2026, 11, 24), 13 * 3600),           # utorok, mimo špičky
    CasOdchodu("so2200", date(2026, 11, 28), 22 * 3600),           # sobota večer, riedke spoje
)

POSUN_M = (100.0, 600.0)  # posun bodu od zastávky [m]
_MAX_POKUSOV = 100_000    # poistka proti nekonečnému cyklu pri nesplniteľných pásmach
_DES_MIEST = 6            # zaokrúhlenie súradníc (≈ 0,1 m), aby JSON vrátil to isté


def skupina(id_instancie: str) -> str:
    """Skupina inštancie ('K', 'S', 'D') z jej id."""
    return id_instancie[0]


def kod_casu(id_instancie: str) -> str:
    """Kód času odchodu (napr. 'ut0730') z id inštancie."""
    return id_instancie.split("-", 1)[1]


def posun_bod(bod: tuple[float, float], vzdialenost_m: float, azimut_rad: float) -> tuple[float, float]:
    """Bod vo vzdušnej vzdialenosti vzdialenost_m [m] od bodu v smere azimutu.

    Priama úloha na guli s polomerom geo.POLOMER_ZEME_M.

    Args:
        bod: (lat, lon) v stupňoch.
        vzdialenost_m: vzdušná vzdialenosť [m].
        azimut_rad: smer v radiánoch (0 = sever, π/2 = východ).
    """
    f1, l1 = math.radians(bod[0]), math.radians(bod[1])
    u = vzdialenost_m / geo.POLOMER_ZEME_M
    f2 = math.asin(math.sin(f1) * math.cos(u) + math.cos(f1) * math.sin(u) * math.cos(azimut_rad))
    l2 = l1 + math.atan2(math.sin(azimut_rad) * math.sin(u) * math.cos(f1),
                         math.cos(u) - math.sin(f1) * math.sin(f2))
    return math.degrees(f2), math.degrees(l2)


def _nahodny_bod(cp: CestovnyPoriadok, zastavky: list[str], par: Parametre,
                 rng: random.Random) -> tuple[float, float]:
    """Náhodná zastávka posunutá o POSUN_M; opakuje, kým bod nemá zastávku do d_max."""
    for _ in range(_MAX_POKUSOV):
        z = rng.choice(zastavky)
        bod = posun_bod(cp.suradnice(z), rng.uniform(*POSUN_M), rng.uniform(0.0, 2 * math.pi))
        bod = (round(bod[0], _DES_MIEST), round(bod[1], _DES_MIEST))
        if cp.zastavky_v_okoli(bod, par.d_max):
            return bod
    raise RuntimeError("nepodarilo sa nájsť bod so zastávkou do d_max")


def obsluhovane_zastavky(cp: CestovnyPoriadok, casy: tuple[CasOdchodu, ...] = CASY) -> list[str]:
    """Zastávky, na ktorých zastavuje aspoň jedna linka v niektorý z dátumov `casy`.

    Zoradené podľa stop_id (determinizmus). Vylúči zastávky bez spojov.
    """
    datumy = sorted({c.datum for c in casy})
    return sorted(z for z in cp.zastavky()
                  if any(cp.linky_na_zastavke(z, d) for d in datumy))


def generuj_dvojice(
    cp: CestovnyPoriadok,
    par: Parametre | None = None,
    seed: int = 42,
    pasma: tuple[Pasmo, ...] = PASMA,
    casy: tuple[CasOdchodu, ...] = CASY,
) -> list[tuple[str, tuple[float, float], tuple[float, float]]]:
    """Vygeneruje dvojice štart–cieľ po skupinách.

    Returns:
        Zoznam (kód dvojice napr. 'S03', štart, cieľ).
    """
    par = par or Parametre()
    rng = random.Random(seed)
    zastavky = obsluhovane_zastavky(cp, casy)
    if not zastavky:
        raise ValueError("cestovný poriadok nemá žiadne obsluhované zastávky")
    dvojice = []
    for pasmo in pasma:
        for i in range(1, pasmo.pocet + 1):
            start = _nahodny_bod(cp, zastavky, par, rng)
            for _ in range(_MAX_POKUSOV):
                ciel = _nahodny_bod(cp, zastavky, par, rng)
                if pasmo.od_m <= geo.haversine_m(start, ciel) < pasmo.do_m:
                    break
            else:
                raise RuntimeError(f"pásmo {pasmo.prefix}: nenašiel sa cieľ v rozsahu vzdialeností")
            dvojice.append((f"{pasmo.prefix}{i:02d}", start, ciel))
    return dvojice


def generuj_instancie(
    cp: CestovnyPoriadok,
    par: Parametre | None = None,
    seed: int = 42,
    pasma: tuple[Pasmo, ...] = PASMA,
    casy: tuple[CasOdchodu, ...] = CASY,
) -> list[Poziadavka]:
    """Vygeneruje inštancie: každú dvojicu štart–cieľ v každom čase z `casy`.

    Pri predvolených hodnotách vznikne 20 dvojíc × 3 časy = 60 inštancií.
    Rovnaký seed (a rovnaký cestovný poriadok) dá vždy rovnaké inštancie.

    Args:
        cp: cestovný poriadok.
        par: parametre modelu (d_max); predvolene Parametre().
        seed: seed generátora náhodných čísel.
        pasma: skupiny podľa vzdušnej vzdialenosti štart–cieľ.
        casy: časy odchodu.

    Returns:
        Zoznam Poziadavka zoradený podľa skupiny, dvojice a času.
    """
    return [
        Poziadavka(f"{kod}-{c.kod}", start, ciel, c.datum, c.cas_s)
        for kod, start, ciel in generuj_dvojice(cp, par, seed, pasma, casy)
        for c in casy
    ]


def _hhmm(s: int) -> str:
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}"


def _najblizsia(cp: CestovnyPoriadok, bod: tuple[float, float], par: Parametre) -> dict:
    okolie = cp.zastavky_v_okoli(bod, par.d_max)
    if not okolie:
        return {"stop_id": None, "nazov": None, "pesia_vzdialenost_m": None}
    z, d = okolie[0]
    return {"stop_id": z, "nazov": cp.nazov(z), "pesia_vzdialenost_m": round(d, 1)}


def uloz_instancie(
    instancie: list[Poziadavka],
    cesta: str | Path,
    cp: CestovnyPoriadok,
    par: Parametre | None = None,
    seed: int | None = None,
) -> None:
    """Uloží inštancie do JSON (aj s doplňujúcimi údajmi kvôli čitateľnosti).

    Doplňujúce polia (skupina, vzdušná vzdialenosť, najbližšia zastávka, počet
    zastávok do d_max) nacitaj_instancie ignoruje.
    """
    par = par or Parametre()
    zaznamy = []
    for p in instancie:
        zaznamy.append({
            "id": p.id,
            "skupina": skupina(p.id),
            "cas": kod_casu(p.id),
            "datum": p.datum.isoformat(),
            "cas_odchodu": p.cas_odchodu,
            "cas_odchodu_hhmm": _hhmm(p.cas_odchodu),
            "start": list(p.start),
            "ciel": list(p.ciel),
            "vzdusna_vzdialenost_m": round(geo.haversine_m(p.start, p.ciel), 1),
            "start_najblizsia": _najblizsia(cp, p.start, par),
            "ciel_najblizsia": _najblizsia(cp, p.ciel, par),
            "start_zastavok_do_d_max": len(cp.zastavky_v_okoli(p.start, par.d_max)),
            "ciel_zastavok_do_d_max": len(cp.zastavky_v_okoli(p.ciel, par.d_max)),
        })
    obsah = {"seed": seed, "pocet": len(zaznamy), "instancie": zaznamy}
    cesta = Path(cesta)
    cesta.parent.mkdir(parents=True, exist_ok=True)
    cesta.write_text(json.dumps(obsah, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def nacitaj_instancie(cesta: str | Path) -> list[Poziadavka]:
    """Načíta inštancie z JSON vytvoreného uloz_instancie.

    Args:
        cesta: cesta k súboru (napr. data/instances.json).

    Returns:
        Zoznam Poziadavka v poradí zo súboru.
    """
    obsah = json.loads(Path(cesta).read_text(encoding="utf-8"))
    return [
        Poziadavka(
            id=z["id"],
            start=(float(z["start"][0]), float(z["start"][1])),
            ciel=(float(z["ciel"][0]), float(z["ciel"][1])),
            datum=date.fromisoformat(z["datum"]),
            cas_odchodu=int(z["cas_odchodu"]),
        )
        for z in obsah["instancie"]
    ]
