"""Utility functions for working with QGIS vector layers."""

from qgis.PyQt.QtCore import QVariant
from qgis.core import (
    QgsFeature,
    QgsField,
    QgsFields,
    QgsGeometry,
    QgsPointXY,
    QgsProject,
    QgsVectorLayer,
    QgsWkbTypes
)

from .exceptions import AddingFeaturesException


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

def create_features(
    fields: QgsFields,
    geometry_type: str,
    points: list[QgsPointXY],
    feature_name: str,
) -> list[QgsFeature]:
    """Create QGIS features from points and the specified geometry type.

    For point geometry, creates one feature per point and appends a
    sequential number to the feature name. For line and polygon geometry,
    creates a single feature using all provided points.

    :param fields: Fields for the created QGIS features.
    :param geometry_type: Geometry type to create: ``Point``, ``LineString``, or ``Polygon``.
    :param points: Points used to construct the feature geometry.
    :param feature_name: Base name assigned to the created features
    :return: A list of created QGIS features.
    """
    features = []

    if geometry_type == "Point":
        for i, point in enumerate(points, start=1):
            feature = QgsFeature(fields)
            feature.setGeometry(QgsGeometry.fromPointXY(point))
            feature.setAttribute("FEAT_NAME", f"{feature_name}_{i}")
            features.append(feature)
    else:
        feature = QgsFeature(fields)
        feature.setAttribute("FEAT_NAME", feature_name)

        if geometry_type == "LineString":
            feature.setGeometry(QgsGeometry.fromPolylineXY(points))
        elif geometry_type == "Polygon":
            feature.setGeometry(QgsGeometry.fromPolygonXY([points]))
        features.append(feature)

    return features


def add_features_to_layer(
        layer: QgsVectorLayer,
        features: list[QgsFeature],
) -> None:
    """Add features (geometry based on extracted coordinates from plain text) to the target layer.

    :param layer: Target vector layer.
    :param features: Features to add.
    """
    if not layer.isEditable():
        layer.startEditing()

    success, _ = layer.dataProvider().addFeatures(features)

    if not success:
        layer.rollBack()
        raise AddingFeaturesException("Adding feature(s) failed.")

    layer.commitChanges()
