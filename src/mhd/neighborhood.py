"""Operátory okolia kandidáta pre metódy 3. fázy.

Implementuje osoba C.

Každý operátor má tvar op(k, p, cp, par, rng) -> Kandidat | None. Vráti nového
kandidáta, ktorý sa od k líši v malom kroku, spĺňa O2 (výstup každého úseku
leží za nástupom v smere jazdy linky, ktorá v deň p.datum premáva) a má
najviac 4 úseky. Ak zmena nie je možná, vráti None. Pôvodného kandidáta
nemení (Usek je nemenný, zoznam úsekov sa vždy kopíruje).

O3 (spoj v časovom okne), O1, O5 a O6 operátory nezaručujú – to posúdi
dekóder cez g. Kde je to lacné, operátory uprednostnia zmeny, ktoré O1 a O5
zachovajú (nástup do d_max od štartu, prestup do d_prestup).

Determinizmus: všetky zoznamy z cestovného poriadku sú zoradené a náhoda ide
iba cez rng, takže rovnaký seed dá rovnakých susedov.
"""

import random
from collections.abc import Callable

from mhd import geo
from mhd.gtfs import CestovnyPoriadok
from mhd.model import Kandidat, Poziadavka, Usek
from mhd.params import Parametre

MAX_USEKOV = 4
MAX_POKUSOV = 10      # nahodny_sused: počet pokusov pri None
SUSEDNE_ZASTAVKY = 2  # posun_prestupu: koľko najbližších zastávok linky sa skúša

Operator = Callable[
    [Kandidat, Poziadavka, CestovnyPoriadok, Parametre, random.Random], Kandidat | None
]


# ------------------------------------------------------------ pomocné funkcie
def splna_o2(k: Kandidat, p: Poziadavka, cp: CestovnyPoriadok) -> bool:
    """True, ak každý úsek kandidáta spĺňa O2 v deň p.datum."""
    return all(
        cp.je_zastavka(u.nastup) and u.vystup in cp.zastavky_za(u.linka, u.nastup, p.datum)
        for u in k.useky
    )


def _za(cp: CestovnyPoriadok, linka: str, zastavka: str, p: Poziadavka) -> set[str]:
    return set(cp.zastavky_za(linka, zastavka, p.datum))


def _linky_do(cp: CestovnyPoriadok, nastup: str, vystup: str, p: Poziadavka) -> list[str]:
    """Linky, ktoré v deň p.datum idú zo zastávky nastup na vystup (O2), zoradené."""
    return [
        l for l in cp.linky_na_zastavke(nastup, p.datum)
        if vystup in _za(cp, l, nastup, p)
    ]


def _nahrad(k: Kandidat, i: int, nove: list[Usek], pocet: int = 1) -> Kandidat:
    """Nový kandidát: úseky k.useky[i : i + pocet] nahradené zoznamom nove."""
    return Kandidat(k.useky[:i] + nove + k.useky[i + pocet:])


def _dist(cp: CestovnyPoriadok, a: str, b: str, par: Parametre) -> float:
    return geo.pesia_vzdialenost_m(cp.suradnice(a), cp.suradnice(b), par)


# ------------------------------------------------------------ operátory
def zmen_nastup(k, p, cp, par, rng):
    """Iná nástupná zastávka prvého úseku do d_max od štartu.

    Z novej zastávky musí ísť linka prvého úseku alebo iná linka na pôvodný
    výstup. Ak taká zastávka nie je, skúsi inú linku na náhodný výstup; pri
    viacúsekovom kandidátovi iba na výstup do d_prestup od nástupu druhého
    úseku, aby prestup ostal pešo dosiahnuteľný.

    Returns:
        Nový kandidát alebo None (iba pešo / žiadna iná zastávka s vhodnou linkou).
    """
    if not k.useky:
        return None
    u = k.useky[0]
    okolie = [z for z, _ in cp.zastavky_v_okoli(p.start, par.d_max) if z != u.nastup]

    # 1) rovnaký výstup, prednostne rovnaká linka
    moznosti = []
    for z in okolie:
        linky = _linky_do(cp, z, u.vystup, p)
        if linky:
            moznosti.append(Usek(u.linka if u.linka in linky else rng.choice(linky), z, u.vystup))
    if moznosti:
        return _nahrad(k, 0, [rng.choice(moznosti)])

    # 2) náhodný výstup (pri prestupe do d_prestup od ďalšieho nástupu)
    dalsi = k.useky[1].nastup if len(k.useky) > 1 else None
    moznosti = []
    for z in okolie:
        for l in cp.linky_na_zastavke(z, p.datum):
            za = cp.zastavky_za(l, z, p.datum)
            if dalsi is not None:
                za = [v for v in za if _dist(cp, v, dalsi, par) <= par.d_prestup]
            moznosti.extend(Usek(l, z, v) for v in za)
    if not moznosti:
        return None
    return _nahrad(k, 0, [rng.choice(moznosti)])


def zmen_vystup(k, p, cp, par, rng):
    """Iná výstupná zastávka posledného úseku na tej istej linke.

    Prednostne zastávka do d_max od cieľa (zachová O1); ak taká nie je,
    ľubovoľná iná zastávka za nástupom.

    Returns:
        Nový kandidát alebo None (iba pešo / linka nemá iné zastávky za nástupom).
    """
    if not k.useky:
        return None
    i = len(k.useky) - 1
    u = k.useky[i]
    za = [v for v in cp.zastavky_za(u.linka, u.nastup, p.datum) if v != u.vystup]
    if not za:
        return None
    blizko = [v for v in za
              if geo.pesia_vzdialenost_m(cp.suradnice(v), p.ciel, par) <= par.d_max]
    v = rng.choice(blizko or za)
    return _nahrad(k, i, [Usek(u.linka, u.nastup, v)])


def posun_prestupu(k, p, cp, par, rng):
    """Posunie prestup medzi úsekmi i a i + 1 o zastávku skôr alebo neskôr.

    Nový výstup úseku i je jedna z SUSEDNE_ZASTAVKY zastávok linky i (za
    nástupom) najbližších k pôvodnému výstupu – v praxi predošlá alebo
    nasledujúca zastávka. K nemu sa vyberie nástup úseku i + 1 do d_prestup
    (aj tá istá zastávka), z ktorého linka i + 1 stále dosiahne svoj výstup.

    Returns:
        Nový kandidát alebo None (menej ako 2 úseky / linka i + 1 sa z okolia
        nového výstupu nedá chytiť).
    """
    if len(k.useky) < 2:
        return None
    poradie = list(range(len(k.useky) - 1))
    rng.shuffle(poradie)
    for i in poradie:
        a, b = k.useky[i], k.useky[i + 1]
        za = [v for v in cp.zastavky_za(a.linka, a.nastup, p.datum) if v != a.vystup]
        za.sort(key=lambda v: (_dist(cp, v, a.vystup, par), v))
        moznosti = []
        for v in za[:SUSEDNE_ZASTAVKY]:
            for z, _ in cp.zastavky_v_okoli(cp.suradnice(v), par.d_prestup):
                if b.vystup in _za(cp, b.linka, z, p):
                    moznosti.append((v, z))
        if moznosti:
            v, z = rng.choice(moznosti)
            return _nahrad(k, i, [Usek(a.linka, a.nastup, v), Usek(b.linka, z, b.vystup)], 2)
    return None


def vymen_linku(k, p, cp, par, rng):
    """Iná linka náhodného úseku z tej istej nástupnej na tú istú výstupnú zastávku.

    Returns:
        Nový kandidát alebo None (žiadny úsek nemá inú takú linku).
    """
    poradie = list(range(len(k.useky)))
    rng.shuffle(poradie)
    for i in poradie:
        u = k.useky[i]
        ine = [l for l in _linky_do(cp, u.nastup, u.vystup, p) if l != u.linka]
        if ine:
            return _nahrad(k, i, [Usek(rng.choice(ine), u.nastup, u.vystup)])
    return None


def pridaj_prestup(k, p, cp, par, rng):
    """Rozdelí náhodný úsek v medzizastávke m na dva: linka po m, iná linka z m.

    Medzizastávka m leží za nástupom a výstup leží za m (na tej istej linke);
    druhá časť ide z m na pôvodný výstup inou linkou (prestup bez chôdze).

    Returns:
        Nový kandidát alebo None (už 4 úseky / iba pešo / žiadna iná linka).
    """
    if not k.useky or len(k.useky) >= MAX_USEKOV:
        return None
    poradie = list(range(len(k.useky)))
    rng.shuffle(poradie)
    for i in poradie:
        u = k.useky[i]
        medzi = [m for m in cp.zastavky_za(u.linka, u.nastup, p.datum)
                 if m != u.vystup and u.vystup in _za(cp, u.linka, m, p)]
        rng.shuffle(medzi)
        for m in medzi:
            ine = [l for l in _linky_do(cp, m, u.vystup, p) if l != u.linka]
            if ine:
                return _nahrad(k, i, [Usek(u.linka, u.nastup, m),
                                      Usek(rng.choice(ine), m, u.vystup)])
    return None


def odober_prestup(k, p, cp, par, rng):
    """Zlúči susedné úseky i, i + 1 do jedného, ak jedna linka spojí nástup i
    s výstupom i + 1. Prednostne sa použije linka jedného z oboch úsekov.

    Returns:
        Nový kandidát alebo None (menej ako 2 úseky / žiadna taká linka).
    """
    if len(k.useky) < 2:
        return None
    poradie = list(range(len(k.useky) - 1))
    rng.shuffle(poradie)
    for i in poradie:
        a, b = k.useky[i], k.useky[i + 1]
        linky = _linky_do(cp, a.nastup, b.vystup, p)
        if linky:
            vlastne = [l for l in linky if l in (a.linka, b.linka)]
            l = rng.choice(vlastne or linky)
            return _nahrad(k, i, [Usek(l, a.nastup, b.vystup)], 2)
    return None


OPERATORY: dict[str, Operator] = {
    "zmen_nastup": zmen_nastup,
    "zmen_vystup": zmen_vystup,
    "posun_prestupu": posun_prestupu,
    "vymen_linku": vymen_linku,
    "pridaj_prestup": pridaj_prestup,
    "odober_prestup": odober_prestup,
}


# ------------------------------------------------------------ vzorkovanie
def nahodny_sused(
    k: Kandidat,
    p: Poziadavka,
    cp: CestovnyPoriadok,
    par: Parametre,
    rng: random.Random,
) -> Kandidat | None:
    """Sused z náhodného operátora; pri None skúsi ďalší (najviac MAX_POKUSOV).

    Returns:
        Nový kandidát alebo None, ak žiadny pokus neuspel (napr. trasa iba pešo).
    """
    nazvy = list(OPERATORY)
    for _ in range(MAX_POKUSOV):
        sused = OPERATORY[rng.choice(nazvy)](k, p, cp, par, rng)
        if sused is not None:
            return sused
    return None


def susedia(
    k: Kandidat,
    p: Poziadavka,
    cp: CestovnyPoriadok,
    par: Parametre,
    rng: random.Random,
    limit: int = 20,
) -> list[Kandidat]:
    """Vzorka najviac `limit` rôznych susedov (bez k), v poradí vzniku.

    Volá nahodny_sused najviac 2 · limit-krát; duplicitní susedia sa vynechajú.
    """
    vysledok: list[Kandidat] = []
    videne = {tuple(k.useky)}
    for _ in range(2 * limit):
        if len(vysledok) >= limit:
            break
        s = nahodny_sused(k, p, cp, par, rng)
        if s is None:
            break  # ani 10 pokusov neuspelo – okolie je prázdne
        kluc = tuple(s.useky)
        if kluc not in videne:
            videne.add(kluc)
            vysledok.append(s)
    return vysledok
