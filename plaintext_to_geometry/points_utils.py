from qgis.core import QgsPointXY

from .aviation_gis_toolkit.coordinate_extraction import (
    SEQUENCE_LON_LAT,
    SEQUENCE_LAT_LON
)

from .aviation_gis_toolkit.const import AT_LATITUDE, AT_LONGITUDE
from .aviation_gis_toolkit.coordinate import Coordinate
from .plugin_types import CoordinatePair


def normalize_coordinate_pairs(
    coordinates: list[tuple[str, str]],
    sequence: str,
) -> list[CoordinatePair] | Exception:
    """Normalize coordinate pairs to longitude/latitude order.

    :param coordinates: Coordinate pairs whose order is determined by ``sequence``.
    :param sequence: Coordinate order fo extracted pairs, determined by ``Sequence`` settings in plugin dialog.
    :return: Coordinate pairs normalized to longitude/latitude order.
    """
    result = []
    if sequence == SEQUENCE_LON_LAT:
        result= [
            CoordinatePair(longitude=lon, latitude=lat)
            for lon, lat in coordinates
        ]

    if sequence == SEQUENCE_LAT_LON:
        result=  [
            CoordinatePair(longitude=lon, latitude=lat)
            for lat, lon in coordinates
        ]

    return result


def to_qgis_points(
        coordinates: list[CoordinatePair],
) -> list[QgsPointXY]:
    """Convert coordinate pairs to QGIS points.

    :param coordinates: Coordinate pairs containing longitude and latitude
    :return: QGIS points with
    """
    points = []

    for coordinate in coordinates:
        longitude = Coordinate(
            coordinate.longitude,
            AT_LONGITUDE,
        )
        latitude = Coordinate(
            coordinate.latitude,
            AT_LATITUDE,
        )

        longitude_dd = longitude.convert_to_dd()
        latitude_dd = latitude.convert_to_dd()

        if longitude_dd is None or latitude_dd is None:
            continue

        points.append(
            QgsPointXY(longitude_dd, latitude_dd)
        )

    return points