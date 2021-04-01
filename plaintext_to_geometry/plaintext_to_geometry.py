# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PlainTextToGeometry
                                 A QGIS plugin
 Extract coordinates from plain text and create points, line or polygon
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2021-03-22
        git sha              : $Format:%H$
        copyright            : (C) 2021 by Paweł Strzelewicz
        email                : @
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, QVariant
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QWidget, QMessageBox, QTableWidget, QTableWidgetItem
from qgis.core import *

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .plaintext_to_geometry_dialog import PlainTextToGeometryDialog
import os.path
from .aviation_gis_toolkit.coordinate_extraction import *
from .aviation_gis_toolkit.coordinate import *

coord_sequence = {
    1: SEQUENCE_LAT_LON,
    2: SEQUENCE_LON_LAT
}

coord_pair_sep = {
    1: COORD_PAIR_SEP_NONE,
    2: COORD_PAIR_SEP_SPACE,
    3: COORD_PAIR_SEP_HYPHEN,
    4: COORD_PAIR_SEP_SLASH,
    5: COORD_PAIR_SEP_BACKSLASH
}

coord_format = {
    1: DMSH_COMP,
    2: HDMS_COMP,
    3: DMSH_SEP,
    4: HDMS_SEP
}


class PlainTextToGeometry:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        self.coordinates_pair_format = {}
        self.coordinate_extractor = None
        self.geometry_type = None
        self.output_layer = None
        self.coordinates_extracted = False
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'PlainTextToGeometry_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&PlainTextToGeometry')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('PlainTextToGeometry', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/plaintext_to_geometry/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'PlainTextToGeometry'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&PlainTextToGeometry'),
                action)
            self.iface.removeToolBarIcon(action)

    def clear_coordinate_format_setting(self):
        self.dlg.comboBoxCoordinatesSequence.setCurrentIndex(0)
        self.dlg.comboBoxCoordinatesSeparator.setCurrentIndex(0)
        self.dlg.comboBoxCoordinatesFormat.setCurrentIndex(0)
        self.dlg.labelCoordinatesExample.setText('Define coordinate format to see example')

    def clear_coordinate_list(self):
        self.dlg.tableWidgetCoordinates.setRowCount(0)

    def plain_text_edited(self):
        if self.coordinates_extracted:
            self.coordinates_extracted = False
            self.dlg.tableWidgetCoordinates.setRowCount(0)
            self.clear_coordinates_marking()

    def clear_plugin_form(self):
        self.clear_coordinate_format_setting()
        self.dlg.lineEditOutputLayerName.clear()
        self.dlg.comboBoxOutputGeometryType.setCurrentIndex(0)
        self.dlg.lineEditFeatureName.clear()
        self.dlg.textEditPlainText.clear()
        self.clear_coordinate_list()

    def set_coordinate_pair_format(self):
        if (self.dlg.comboBoxCoordinatesSequence.currentIndex() >= 1 and
                self.dlg.comboBoxCoordinatesSeparator.currentIndex() >= 1 and
                self.dlg.comboBoxCoordinatesFormat.currentIndex() >= 1):
            self.coordinates_pair_format['sequence'] = coord_sequence[self.dlg.comboBoxCoordinatesSequence.currentIndex()]
            self.coordinates_pair_format['coordinate_format'] = coord_format[
                self.dlg.comboBoxCoordinatesFormat.currentIndex()]
            self.coordinates_pair_format['separator'] = coord_pair_sep[
                self.dlg.comboBoxCoordinatesSeparator.currentIndex()]
            self.set_coordinate_extractor()
            self.show_sample_coordinate_format()
        else:
            self.coordinates_pair_format = {}
            self.coordinate_extractor = None
            self.dlg.labelCoordinatesExample.setText('Define coordinate format to see example')

    def set_coordinate_extractor(self):
        self.coordinate_extractor = CoordinatePairExtraction(self.coordinates_pair_format['sequence'],
                                                             self.coordinates_pair_format["coordinate_format"],
                                                             self.coordinates_pair_format['separator'])

    def show_sample_coordinate_format(self):
        example_coordinates = self.coordinate_extractor.get_coordinates_pair_example()
        self.dlg.labelCoordinatesExample.setText(example_coordinates)

    def get_plain_text(self):
        return self.dlg.textEditPlainText.toPlainText()

    def set_geometry_type(self):
        geometry_type = self.dlg.comboBoxOutputGeometryType.currentText()
        if geometry_type == 'Line':
            geometry_type += 'String'
        self.geometry_type = geometry_type

    @staticmethod
    def get_vector_layers_by_name(layer_name):
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

    @staticmethod
    def not_memory_layer(layer):
        """ Return true if layer is not memory (provider data type is other than memory).
        param layer_name: str
        return: bool
        """
        return bool('memory' != layer.providerType())

    @staticmethod
    def geometry_type_as_string(layer):
        """ Return string representation of the layer geometry type.
        param layer: QgsVectorLayer
        return: str, example Point., LineString, Polygon
        """
        return QgsWkbTypes.displayString(int(layer.wkbType()))

    def not_geometry_type(self, layer, geometry_type):
        """ Return true if layer geometry type is different than passed by geometry_type).
        param layer: QgsVectorLayer
        param geometry_type: str, example: Point, LineString, Polygon
        return: bool
        """
        return bool(geometry_type != self.geometry_type_as_string(layer))

    def get_potential_plaintext_layers(self, layers):
        """ Return list of QgsVectorLayer that match plugin PlainTextToGeometry output layer:
            - layer is memory type
            - geometry type is the same as Geometry type set by plugin
        param layers: list -> QgsVectorLayer
        return: list -> QgsVectorLayer
        """
        layer_candidates = []
        for layer in layers:
            if self.not_memory_layer(layer):
                continue
            if self.not_geometry_type(layer, self.geometry_type):
                continue
            layer_candidates.append(layer)
        return layer_candidates

    def get_matching_layers_from_map(self, layer_name):
        """ Check layers in Layer (TOC) in current Qgs Project and return those layers that match
        plugin PlainTextToGeometry output layer.
        param layer_name: str
        return: list -> QgsVectorLayer
        """
        vector_layers = self.get_vector_layers_by_name(layer_name)
        if vector_layers:
            candidate_layers = self.get_potential_plaintext_layers(vector_layers)
            return candidate_layers

    def create_new_memory_layer(self, layer_name):
        """ Create memory layer with geometry type assigned by PlainTextToGeometry plugin.
        param layer_name: str
        return: QgsVectorLayer
        """
        layer = QgsVectorLayer('{}?crs=epsg:4326'.format(self.geometry_type), layer_name, 'memory')
        provider = layer.dataProvider()
        layer.startEditing()
        provider.addAttributes([QgsField("FEAT_NAME", QVariant.String, len=100)])
        layer.commitChanges()
        QgsProject.instance().addMapLayer(layer)
        return layer

    def get_coordinates_from_plain_text(self):
        plain_text = self.dlg.textEditPlainText.toHtml()
        coordinates = self.coordinate_extractor.extract_coordinates(plain_text)
        return coordinates

    def mark_coordinates(self, coordinates):
        """ Mark extracted coordinates in plain text - set the color to green.
        param coordinates: list, list of extracted coordinates
        """
        if coordinates:
            text = self.dlg.textEditPlainText.toHtml()
            for c1, c2 in coordinates:
                coord_pair = '{}{}{}'.format(c1, self.coordinates_pair_format["separator"], c2)
                text = re.sub(coord_pair, '<span style="color:green;">{}</span>'.format(coord_pair), text)

            self.dlg.textEditPlainText.setHtml(text)

    def clear_coordinates_marking(self):
        """ Clear green color for extracted coordinates in plain text. """
        html = self.dlg.textEditPlainText.toHtml()
        html = html.replace('<span style=" color:#008000;">', '')
        html = html.replace('</span>', '')
        self.dlg.textEditPlainText.setHtml(html)

    def insert_coordinates_to_list(self, lon, lat):
        row_pos = self.dlg.tableWidgetCoordinates.rowCount()
        self.dlg.tableWidgetCoordinates.insertRow(row_pos)
        self.dlg.tableWidgetCoordinates.setItem(row_pos, 0, QTableWidgetItem(lon))
        self.dlg.tableWidgetCoordinates.setItem(row_pos, 1, QTableWidgetItem(lat))

    def fill_in_coordinate_list(self, coordinate_list):
        self.dlg.tableWidgetCoordinates.setRowCount(0)
        if self.coordinate_extractor.coord_sequence == SEQUENCE_LON_LAT:
            for lon, lat in coordinate_list:
                self.insert_coordinates_to_list(lon, lat)
        elif self.coordinate_extractor.coord_sequence == SEQUENCE_LAT_LON:
            for lat, lon in coordinate_list:
                self.insert_coordinates_to_list(lon, lat)

    def get_qgspoints(self):
        """ Create list of QgsPoints based on extracted coordinates.
        return: points: list of QGsPoint
        """
        points = []
        points_count = self.dlg.tableWidgetCoordinates.rowCount()

        for i in range(0, points_count):
            lon = Coordinate(self.dlg.tableWidgetCoordinates.item(i, 0).text(), AT_LONGITUDE)
            lat = Coordinate(self.dlg.tableWidgetCoordinates.item(i, 1).text(), AT_LATITUDE)
            lon_dd = lon.convert_to_dd()
            lat_dd = lat.convert_to_dd()

            if lon_dd is not None and lat_dd is not None:
                point = QgsPointXY(lon_dd, lat_dd)
                points.append(point)

        return points

    def add_points(self, points):
        """ Add point features to output layer.
        param points: list of QGsPoint
        """
        feat = QgsFeature()
        self.output_layer.startEditing()
        prov = self.output_layer.dataProvider()
        point_nr = 0
        for point in points:
            point_nr += 1
            point_name = '{}_{}'.format(self.dlg.lineEditFeatureName.text().strip(), point_nr)
            point_geom = QgsGeometry.fromPointXY(point)
            feat.setGeometry(point_geom)
            feat.setAttributes([point_name])
            prov.addFeatures([feat])
        self.output_layer.commitChanges()
        self.output_layer.updateExtents()
        self.iface.mapCanvas().setExtent(self.output_layer.extent())
        self.iface.mapCanvas().refresh()

    def add_feature(self, points):
        """ Add feature (points, line or polygon) to  output layer based on extracted coordinates.
        param points: list of QGsPoint
        """
        if self.geometry_type == 'Point':
            self.add_points(points)
        else:
            feat = QgsFeature()
            self.output_layer.startEditing()
            prov = self.output_layer.dataProvider()

            if self.geometry_type == 'LineString':
                feat_geom = QgsGeometry.fromPolylineXY(points)
            else:  # Polygon
                feat_geom = QgsGeometry.fromPolygonXY([points])

            feat.setGeometry(feat_geom)
            feat.setAttributes([self.dlg.lineEditFeatureName.text().strip()])
            prov.addFeatures([feat])
            self.output_layer.commitChanges()
            self.output_layer.updateExtents()
            self.iface.mapCanvas().setExtent(self.output_layer.extent())
            self.iface.mapCanvas().refresh()

    def is_required_input_plugin_form(self):
        """ Check if required data such as: coordinate formats defined, plain text etc. is entered in plugin form. """
        err_msg = ''
        if not self.coordinates_pair_format:
            err_msg += 'Set coordinate format!\n'
        if not self.dlg.lineEditOutputLayerName.text().strip():
            err_msg += 'Output layer name is required!\n'
        if not self.dlg.lineEditFeatureName.text().strip():
            err_msg += 'Point(s) prefix, line, polygon name is required!\n'
        if not self.get_plain_text():
            err_msg += 'Plain text is required!\n'
        if err_msg:
            QMessageBox.critical(QWidget(), "Message", err_msg)
        else:
            return True

    def plain_text_to_geometry(self):
        self.coordinates_extracted = False
        if self.is_required_input_plugin_form():
            self.set_geometry_type()
            layers = self.get_matching_layers_from_map(self.dlg.lineEditOutputLayerName.text().strip())
            if layers:
                layer_count = len(layers)
                if layer_count == 1:
                    self.output_layer = layers[0]
                else:
                    QMessageBox.critical(QWidget(), "Message", "{} matching layers with name {}".format(layer_count, self.dlg.lineEditOutputLayerName.text().strip()))
                    self.output_layer = None
            else:
                self.output_layer = self.create_new_memory_layer(self.dlg.lineEditOutputLayerName.text().strip())
            if self.output_layer:
                self.iface.setActiveLayer(self.output_layer)

            coordinates = self.get_coordinates_from_plain_text()
            if coordinates:
                self.mark_coordinates(coordinates)
                self.fill_in_coordinate_list(coordinates)
                self.add_feature(self.get_qgspoints())
                self.coordinates_extracted = True
            else:
                self.dlg.tableWidgetCoordinates.setRowCount(0)
                self.clear_coordinates_marking()

    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = PlainTextToGeometryDialog()
            self.dlg.comboBoxCoordinatesSequence.currentIndexChanged.connect(self.set_coordinate_pair_format)
            self.dlg.comboBoxCoordinatesSeparator.currentIndexChanged.connect(self.set_coordinate_pair_format)
            self.dlg.comboBoxCoordinatesFormat.currentIndexChanged.connect(self.set_coordinate_pair_format)
            self.dlg.pushButtonCancel.clicked.connect(self.dlg.close)
            self.dlg.pushButtoPlainTextToGeometry.clicked.connect(self.plain_text_to_geometry)
            self.dlg.textEditPlainText.textChanged.connect(self.plain_text_edited)

        # show the dialog
        self.dlg.show()
        self.clear_plugin_form()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass
