"""Spoločné fixtures pre testy."""

from pathlib import Path

import pytest

from mhd.gtfs import CestovnyPoriadok

TOY = Path(__file__).parent / "data" / "toy_gtfs"


@pytest.fixture(scope="session")
def cp() -> CestovnyPoriadok:
    """Cestovný poriadok toy siete (tests/data/toy_gtfs)."""
    return CestovnyPoriadok.nacitaj(str(TOY))
