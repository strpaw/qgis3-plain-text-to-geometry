from dataclasses import dataclass


@dataclass(frozen=True)
class CoordinatePair:
    """Represent a pair of geographic coordinates.

    Attributes:
        longitude: Longitude coordinate value.
        latitude: Latitude coordinate value.
    """
    longitude: str
    latitude: str
