# -*- coding: utf-8 -*-
"""
/***************************************************************************
 movingTrafficSigns
                                 A QGIS plugin
 movingTrafficeSigns
                              -------------------
        begin                : 2019-05-08
        git sha              : $Format:%H$
        copyright            : (C) 2019 by TH
        email                : th@mhtc.co.uk
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

import resources
# Import the code for the dialog

import os.path

from PyQt4.QtGui import (
    QMessageBox,
    QPixmap,
    QDialog,
    QLabel,
    QPushButton,
    QDialogButtonBox,
    QImage,
    QApplication,
    QIcon,
    QAction,
    QDockWidget,
    QMenu
)

from PyQt4.QtCore import (
    QObject,
    QThread,
    pyqtSignal,
    pyqtSlot,
    Qt,
    QSettings, QTranslator, qVersion, QCoreApplication,
    QDateTime
)

from qgis.core import (
    QgsMessageLog,
    QgsExpressionContextUtils
)
from qgis.core import *
from qgis.gui import *



#############################################################################

class GeometryInfoMapTool(QgsMapToolIdentify):

    notifyFeatureFound = QtCore.pyqtSignal(QgsVectorLayer, QgsFeature)

    def __init__(self, iface):
        QgsMapToolIdentify.__init__(self, iface.mapCanvas())
        self.iface = iface

    def canvasReleaseEvent(self, event):
        # Return point under cursor

        self.event = event

        closestFeature, closestLayer = self.findNearestFeatureAtC(event.pos())

        QgsMessageLog.logMessage(("In Info - canvasReleaseEvent."), tag="TOMs panel")

        # Remove any current selection and add the new ones (if appropriate)

        if closestLayer == None:

            if self.iface.activeLayer():
                self.iface.activeLayer().removeSelection()

        else:

            QgsMessageLog.logMessage(
                ("In Info - canvasReleaseEvent. Feature selected from layer: " + closestLayer.name() + " id: " + str(
                    closestFeature.id())),
                tag="TOMs panel")

            if closestLayer <> self.iface.activeLayer():
                if self.iface.activeLayer():
                    self.iface.activeLayer().removeSelection()
                self.iface.setActiveLayer(closestLayer)

            if closestLayer.type() == QgsMapLayer.VectorLayer:
                QgsMessageLog.logMessage(("In Info - canvasReleaseEvent. layer type " + str(closestLayer.type())),
                                         tag="TOMs panel")

            if closestLayer.geometryType() == QGis.Point:
                QgsMessageLog.logMessage(("In Info - canvasReleaseEvent. point layer type "), tag="TOMs panel")

            if closestLayer.geometryType() == QGis.Line:
                QgsMessageLog.logMessage(("In Info - canvasReleaseEvent. line layer type "), tag="TOMs panel")

            self.notifyFeatureFound.emit(closestLayer, closestFeature)

            """QgsMessageLog.logMessage(
                "In GeometryInfoMapTool - releaseEvent. currRestrictionLayer: " + str(closestLayer.name()),
                tag="TOMs panel")

            # TODO: Sort out this for UPDATE
            # self.setDefaultRestrictionDetails(closestFeature, closestLayer)
            dialog = self.iface.getFeatureForm(closestLayer, closestFeature)
            self.setupDemandDialog(dialog, closestLayer, closestFeature)  # connects signals, etc
            dialog.show()"""

        pass

    def transformCoordinates(self, screenPt):
        """ Convert a screen coordinate to map and layer coordinates.

            returns a (mapPt,layerPt) tuple.
        """
        return (self.toMapCoordinates(screenPt))

    def findNearestFeatureAtC(self, pos):
        #  def findFeatureAt(self, pos, excludeFeature=None):
        # http://www.lutraconsulting.co.uk/blog/2014/10/17/getting-started-writing-qgis-python-plugins/ - generates "closest feature" function

        """ Find the feature close to the given position.

            'pos' is the position to check, in canvas coordinates.

            if 'excludeFeature' is specified, we ignore this feature when
            finding the clicked-on feature.

            If no feature is close to the given coordinate, we return None.
        """
        mapPt = self.transformCoordinates(pos)
        tolerance = 0.5
        searchRect = QgsRectangle(mapPt.x() - tolerance,
                                  mapPt.y() - tolerance,
                                  mapPt.x() + tolerance,
                                  mapPt.y() + tolerance)

        request = QgsFeatureRequest()
        request.setFilterRect(searchRect)
        request.setFlags(QgsFeatureRequest.ExactIntersect)

        #self.RestrictionLayers = QgsMapLayerRegistry.instance().mapLayersByName("RestrictionLayers")[0]
        self.currLayer = QgsMapLayerRegistry.instance().mapLayersByName("MovingTrafficSigns")[0]

        featureList = []
        layerList = []

        # Loop through all features in the layer to find the closest feature
        for f in self.currLayer.getFeatures(request):
            # Add any features that are found should be added to a list
            featureList.append(f)
            layerList.append(self.currLayer)

        QgsMessageLog.logMessage("In findNearestFeatureAt: nrFeatures: " + str(len(featureList)), tag="TOMs panel")

        if len(featureList) == 0:
            return None, None
        elif len(featureList) == 1:
            return featureList[0], layerList[0]
        else:
            # set up a context menu
            QgsMessageLog.logMessage("In findNearestFeatureAt: multiple features: " + str(len(featureList)),
                                     tag="TOMs panel")

            feature, layer = self.getFeatureDetails(featureList, layerList)

            QgsMessageLog.logMessage("In findNearestFeatureAt: feature: " + str(feature.attribute('id')),
                                     tag="TOMs panel")

            return feature, layer

        pass

    def getFeatureDetails(self, featureList, layerList):
        QgsMessageLog.logMessage("In getFeatureDetails", tag="TOMs panel")

        self.featureList = featureList
        self.layerList = layerList

        # Creates the context menu and returns the selected feature and layer
        QgsMessageLog.logMessage("In getFeatureDetails: nrFeatures: " + str(len(featureList)), tag="TOMs panel")

        self.actions = []
        self.menu = QMenu(self.iface.mapCanvas())

        for feature in featureList:

            try:

                title = str(feature.id())
                QgsMessageLog.logMessage("In featureContextMenu: adding: " + str(title), tag="TOMs panel")

            except TypeError:

                title = " (" + feature.attribute("SignType_1") + ")"

            action = QAction(title, self.menu)
            self.actions.append(action)

            self.menu.addAction(action)

        QgsMessageLog.logMessage("In getFeatureDetails: showing menu?", tag="TOMs panel")

        clicked_action = self.menu.exec_(self.iface.mapCanvas().mapToGlobal(self.event.pos()))
        QgsMessageLog.logMessage(("In getFeatureDetails:clicked_action: " + str(clicked_action)), tag="TOMs panel")

        if clicked_action is not None:

            QgsMessageLog.logMessage(("In getFeatureDetails:clicked_action: " + str(clicked_action.text())),
                                     tag="TOMs panel")
            idxList = self.getIdxFromGeometryID(clicked_action.text(), featureList)

            QgsMessageLog.logMessage("In getFeatureDetails: idx = " + str(idxList), tag="TOMs panel")

            if idxList >= 0:
                QgsMessageLog.logMessage("In getFeatureDetails: feat = " + str(featureList[idxList].attribute('id')),
                                         tag="TOMs panel")
                return featureList[idxList], layerList[idxList]

        QgsMessageLog.logMessage(("In getFeatureDetails. No action found."), tag="TOMs panel")

        return None, None


    def getIdxFromGeometryID(self, selectedGeometryID, featureList):
        #
        QgsMessageLog.logMessage("In getIdxFromGeometryID", tag="TOMs panel")

        idx = -1
        for feature in featureList:
            idx = idx + 1
            if str(feature.id()) == selectedGeometryID:
                return idx

        pass

        return idx

#############################################################################
class CreateSignTool(QgsMapToolCapture):

    notifyNewFeature = QtCore.pyqtSignal(list)

    # helpful link - http://apprize.info/python/qgis/7.html ??
    def __init__(self, iface, layer):

        QgsMessageLog.logMessage(("In CreateSignTool - init."), tag="TOMs panel")

        QgsMapToolCapture.__init__(self, iface.mapCanvas(), iface.cadDockWidget())
        #https: // qgis.org / api / classQgsMapToolCapture.html
        canvas = iface.mapCanvas()
        self.iface = iface
        self.layer = layer

        QgsMessageLog.logMessage("In CreateSignTool - geometryType for " + str(self.layer.name()) + ": " + str(self.layer.geometryType()), tag="TOMs panel")

        if self.layer.geometryType() == 0: # PointGeometry:
            self.setMode(CreateSignTool.CapturePoint)
        elif self.layer.geometryType() == 1: # LineGeometry:
            self.setMode(CreateSignTool.CaptureLine)
        elif self.layer.geometryType() == 2: # PolygonGeometry:
            self.setMode(CreateSignTool.CapturePolygon)
        else:
            QgsMessageLog.logMessage(("In CreateSignTool - No geometry type found. EXITING ...."), tag="TOMs panel")
            return

        QgsMessageLog.logMessage(("In CreateSignTool - mode set."), tag="TOMs panel")

        # Seems that this is important - or at least to create a point list that is used later to create Geometry
        self.sketchPoints = self.points()
        #self.setPoints(self.sketchPoints)  ... not sure when to use this ??

        # Set up rubber band. In current implementation, it is not showing feeback for "next" location

        #self.rb = self.createRubberBand(QGis.Line)  # what about a polygon ??

        #self.currLayer = self.layer

        #QgsMessageLog.logMessage(("In CreateSignTool - init. Curr layer is " + str(self.currLayer.name()) + "Incoming: " + str(self.layer)), tag="TOMs panel")

        # set up snapping configuration   *******************

        #self.snappingUtils = QgsSnappingUtils()

        #self.snappingUtils.setLayers([snapping_layer1, snapping_layer2, snapping_layer3])

        #self.snappingUtils.setSnapToMapMode(QgsSnappingUtils.SnapAdvanced)

        #self.TOMsTracer.setMaxFeatureCount(1000)
        self.lastPoint = None

        # set up function to be called when capture is complete
        #self.onCreateRestriction = onCreateRestriction

    def cadCanvasReleaseEvent(self, event):
        QgsMapToolCapture.cadCanvasReleaseEvent(self, event)
        QgsMessageLog.logMessage(("In Create - cadCanvasReleaseEvent"), tag="TOMs panel")

        if event.button() == Qt.LeftButton:
            if not self.isCapturing():
                self.startCapturing()

            checkSnapping = event.isSnapped
            QgsMessageLog.logMessage("In Create - cadCanvasReleaseEvent: checkSnapping = " + str(checkSnapping), tag="TOMs panel")

            # Now wanting to add point(s) to new shape. Take account of snapping and tracing

            self.currPoint = event.snapPoint(1)    #  1 is value of QgsMapMouseEvent.SnappingMode (not sure where this is defined)
            self.lastEvent = event
            # If this is the first point, add and k

            nrPoints = self.size()
            res = None

            if not self.lastPoint:

                self.result = self.addVertex(self.currPoint)
                QgsMessageLog.logMessage("In Create - cadCanvasReleaseEvent: adding vertex 0 " + str(self.result), tag="TOMs panel")

            self.lastPoint = self.currPoint

            QgsMessageLog.logMessage(("In Create - cadCanvasReleaseEvent (AddVertex/Line) Result: " + str(self.result) + " X:" + str(self.currPoint.x()) + " Y:" + str(self.currPoint.y())), tag="TOMs panel")

            if self.layer.geometryType() == 0:
                self.getPointsCaptured()

        elif (event.button() == Qt.RightButton):
            # Stop capture when right button or escape key is pressed

            self.getPointsCaptured()

            # Need to think about the default action here if none of these buttons/keys are pressed.

        pass

    def keyPressEvent(self, event):
        if (event.key() == Qt.Key_Backspace) or (event.key() == Qt.Key_Delete) or (event.key() == Qt.Key_Escape):
            self.undo()
            pass
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            pass
            # Need to think about the default action here if none of these buttons/keys are pressed.

    def getPointsCaptured(self):
        QgsMessageLog.logMessage(("In CreateSignTool - getPointsCaptured"), tag="TOMs panel")

        # Check the number of points
        self.nrPoints = self.size()
        QgsMessageLog.logMessage(("In CreateSignTool - getPointsCaptured; Stopping: " + str(self.nrPoints)),
                                 tag="TOMs panel")

        self.sketchPoints = self.points()

        for point in self.sketchPoints:
            QgsMessageLog.logMessage(("In CreateSignTool - getPointsCaptured X:" + str(point.x()) + " Y: " + str(point.y())), tag="TOMs panel")

        # stop capture activity
        self.stopCapturing()

        if self.nrPoints > 0:

            # take points from the rubber band and copy them into the "feature"
            self.notifyNewFeature.emit(self.sketchPoints)

