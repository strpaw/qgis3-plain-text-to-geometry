"""Utility functions for working with QGIS vector layers."""

from qgis.PyQt.QtCore import QVariant
from qgis.core import (
    QgsField,
    QgsProject,
    QgsVectorLayer,
    QgsWkbTypes
)


def find_vector_layers(layer_name: str) -> list[QgsVectorLayer]:
    """Return all vector layers with the given name.

    param layer_name: Name of the vector layers to find.
    return: A list of matching QgsVectorLayer instances. Returns an empty list if no matching vector layers are found.
    """
    layers = QgsProject.instance().mapLayersByName(layer_name)
    return [layer for layer in layers if isinstance(layer, QgsVectorLayer)]


def is_memory_layer(layer: QgsVectorLayer) -> bool:
    """Return True if the layer uses the memory provider.

    param layer: layer to be checked.
    return: Ture if layer is memory provider, False otherwise.
    """
    return layer.providerType() == "memory"


def has_geometry_type(
    layer: QgsVectorLayer,
    geometry_type: str,
) -> bool:
    """Check if the layer has the specified geometry type.

    :param layer: layer whose geometry type is being checked.
    :param geometry_type:
    :return: True if the layer's geometry type matches `geometry_type`, otherwise False.
    """
    return QgsWkbTypes.displayString(layer.wkbType()) == geometry_type


def create_output_layer(layer_name: str,
                        geometry_type: str) -> QgsVectorLayer:
    """Create and register an in-memory QGIS vector layer where feature with extracted coordinates will be stored.

    :param layer_name: Name of the output layer.
    :param geometry_type: QGIS geometry type, such as ``"Point"``, ``"LineString"``, or ``"Polygon"``
    :return: The newly created and registered ``QgsVectorLayer``.
    """
    layer = QgsVectorLayer(f'{geometry_type}?crs=epsg:4326', layer_name, 'memory')
    provider = layer.dataProvider()
    layer.startEditing()
    provider.addAttributes([QgsField("FEAT_NAME", QVariant.String, len=100)])
    layer.commitChanges()
    QgsProject.instance().addMapLayer(layer)
    return layer


def get_potential_output_layers(
        layers: list[QgsVectorLayer],
        geometry_type: str,
) -> list[QgsVectorLayer]:
    """Return memory layers matching the specified geometry type.

    :param layers: Layers to filter.
    :param geometry_type: Expected QGIS geometry type, e.g. ``Point``, ``LineString``, or ``Polygon``.
    :return: Memory vector layers with the specified geometry type.
    """
    return [
        layer
        for layer in layers
        if is_memory_layer(layer)
           and has_geometry_type(layer, geometry_type)
    ]
