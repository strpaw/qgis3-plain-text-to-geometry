"""Utility functions for working with QGIS vector layers."""

from qgis.core import (
    QgsMapLayer,
    QgsProject,
    QgsVectorLayer,
    QgsWkbTypes
)

def get_vector_layers_by_name(layer_name: str) -> list[QgsVectorLayer]:
    """ Return list of vector layers with given name.
    param layer_name: str
    return: list -> QgsVectorLayer
    """
    vector_layers = []
    layers = QgsProject.instance().mapLayersByName(layer_name)
    for layer in layers:
        if layer.type() == QgsMapLayer.VectorLayer:
            vector_layers.append(layer)
    return vector_layers


def not_memory_layer(layer: QgsVectorLayer) -> bool:
    """ Return true if layer is not memory (provider data type is other than memory).
    param layer_name: str
    return: bool
    """
    return bool('memory' != layer.providerType())


def geometry_type_as_string(layer: QgsVectorLayer) -> str:
    """ Return string representation of the layer geometry type.
    param layer: QgsVectorLayer
    return: str, example Point., LineString, Polygon
    """
    return QgsWkbTypes.displayString(layer.wkbType())


def not_geometry_type(layer: QgsVectorLayer, geometry_type: str) -> bool:
    """ Return true if layer geometry type is different than passed by geometry_type).
    param layer: QgsVectorLayer
    param geometry_type: str, example: Point, LineString, Polygon
    return: bool
    """
    return bool(geometry_type != geometry_type_as_string(layer))
