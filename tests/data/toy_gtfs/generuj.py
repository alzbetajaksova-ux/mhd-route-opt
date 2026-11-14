"""Generátor toy GTFS (malá testovacia sieť). Popis siete je v README.md.

Spustenie (prepíše CSV v tomto priečinku):
    python tests/data/toy_gtfs/generuj.py
"""

import csv
from pathlib import Path

PRIECINOK = Path(__file__).parent

# stop_id s úvodnou nulou zámerne – overuje čítanie ID ako str
ZASTAVKY = [
    # stop_id, názov, lat, lon (reálne súradnice z GTFS DPB)
    ("01", "Hlavná stanica", 48.157543182373, 17.1067714691162),
    ("02", "Račianske mýto", 48.1580009460449, 17.1205291748047),
    ("03", "Trnavské mýto", 48.1574859619141, 17.1269702911377),
    ("04", "Blumentál", 48.1533737182617, 17.1187610626221),
    ("05", "Americké nám.", 48.1508674621582, 17.1179046630859),
    ("06", "Hodžovo nám.", 48.1481628417969, 17.1083030700684),
    ("07", "Poštová", 48.1466407775879, 17.1085720062256),
    ("08", "Most SNP", 48.139762878418, 17.1056499481201),
    ("09", "Krížna", 48.1546783447266, 17.123685836792),
]

LINKY = [
    # route_id, short_name, long_name, route_type
    ("1", "1", "Hlavná stanica - Trnavské mýto", 0),
    ("2", "2", "Račianske mýto - Most SNP", 0),
    ("3", "3", "Hodžovo nám. - Hlavná stanica", 3),
    ("4", "4", "Trnavské mýto - Americké nám. (iba sobota)", 3),
]

# (route_id, service_id, direction_id, [(stop_id, posun od začiatku v s)], začiatky)
def hhmm(h: int, m: int) -> int:
    return h * 3600 + m * 60


def kazdych_10(h0: int, m0: int, pocet: int = 12) -> list[int]:
    return [hhmm(h0, m0) + 600 * i for i in range(pocet)]


VZORY = [
    ("1", "PD", 0, [("01", 0), ("02", 240), ("03", 420)], kazdych_10(7, 0)),
    ("1", "PD", 1, [("03", 0), ("02", 180), ("01", 420)], kazdych_10(7, 5)),
    ("2", "PD", 0, [("02", 0), ("04", 180), ("05", 300), ("07", 540), ("08", 780)],
     kazdych_10(7, 5)),
    ("3", "PD", 0, [("06", 0), ("01", 360)], kazdych_10(7, 5) + [hhmm(24, 5)]),
    ("4", "SO", 0, [("03", 0), ("09", 120), ("05", 300)], kazdych_10(7, 0)),
]


def cas(s: int) -> str:
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


def zapis(nazov: str, hlavicka: list[str], riadky: list[list]) -> None:
    with open(PRIECINOK / nazov, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(hlavicka)
        w.writerows(riadky)


def main() -> None:
    zapis("agency.txt",
          ["agency_id", "agency_name", "agency_url", "agency_timezone"],
          [["01", "Toy DPB", "https://dpb.sk", "Europe/Bratislava"]])
    zapis("stops.txt", ["stop_id", "stop_name", "stop_lat", "stop_lon"],
          [list(z) for z in ZASTAVKY])
    zapis("routes.txt",
          ["route_id", "agency_id", "route_short_name", "route_long_name", "route_type"],
          [[r, "01", s, n, t] for r, s, n, t in LINKY])
    zapis("calendar.txt",
          ["service_id", "monday", "tuesday", "wednesday", "thursday", "friday",
           "saturday", "sunday", "start_date", "end_date"],
          [["PD", 1, 1, 1, 1, 1, 0, 0, "20261116", "20261231"],
           ["SO", 0, 0, 0, 0, 0, 1, 0, "20261116", "20261231"]])
    # 17. 11. 2026 (utorok, štátny sviatok): pracovné dni zrušené, sobotná premávka pridaná
    zapis("calendar_dates.txt", ["service_id", "date", "exception_type"],
          [["PD", "20261117", 2], ["SO", "20261117", 1]])

    trips, stop_times = [], []
    for linka, sluzba, smer, zastavky, zaciatky in VZORY:
        for t0 in zaciatky:
            trip_id = f"{linka}_{smer}_{cas(t0)[:5].replace(':', '')}"
            trips.append([linka, sluzba, trip_id, smer])
            for seq, (stop_id, posun) in enumerate(zastavky, start=1):
                stop_times.append([trip_id, cas(t0 + posun), cas(t0 + posun), stop_id, seq])
    zapis("trips.txt", ["route_id", "service_id", "trip_id", "direction_id"], trips)
    zapis("stop_times.txt",
          ["trip_id", "arrival_time", "departure_time", "stop_id", "stop_sequence"],
          stop_times)
    zapis("transfers.txt", ["from_stop_id", "to_stop_id", "transfer_type", "min_transfer_time"], [])
    print(f"{len(ZASTAVKY)} zastávok, {len(LINKY)} linky, {len(trips)} spojov, "
          f"{len(stop_times)} riadkov stop_times")


if __name__ == "__main__":
    main()
