"""Utility functions for working with QGIS vector layers."""

from qgis.core import (
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
