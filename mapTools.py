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

from .formUtils import demandFormUtils

#############################################################################
class CreateSignTool(QgsMapToolCapture, demandFormUtils):

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

        self.rb = self.createRubberBand(QGis.Line)  # what about a polygon ??

        self.currLayer = self.layer

        #QgsMessageLog.logMessage(("In CreateSignTool - init. Curr layer is " + str(self.currLayer.name()) + "Incoming: " + str(self.layer)), tag="TOMs panel")

        # set up snapping configuration   *******************

        self.snappingUtils = QgsSnappingUtils()

        #self.snappingUtils.setLayers([snapping_layer1, snapping_layer2, snapping_layer3])

        self.snappingUtils.setSnapToMapMode(QgsSnappingUtils.SnapAdvanced)

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

            #self.sketchPoints = sketchPoints

            if self.currLayer.startEditing() == False:
                reply = QMessageBox.information(None, "Information",
                                                "Could not start transaction on " + self.currLayer.name(),
                                                QMessageBox.Ok)
                return

            fields = self.currLayer.fields()
            feature = QgsFeature(fields)
            # feature.setFields(fields)

            if self.currLayer.geometryType() == 0:  # Point
                feature.setGeometry(QgsGeometry.fromPoint(self.sketchPoints[0]))
            elif self.currLayer.geometryType() == 1:  # Line
                feature.setGeometry(QgsGeometry.fromPolyline(self.sketchPoints))
            elif self.currLayer.geometryType() == 2:  # Polygon
                feature.setGeometry(QgsGeometry.fromPolygon([self.sketchPoints]))
                # feature.setGeometry(QgsGeometry.fromPolygon(self.sketchPoints))
            else:
                QgsMessageLog.logMessage(("In CreateRestrictionTool - no geometry type found"), tag="TOMs panel")
                return

            QgsMessageLog.logMessage(
                ("In Create - getPointsCaptured; geometry prepared; " + str(feature.geometry().exportToWkt())),
                tag="TOMs panel")

            # set any geometry related attributes ...

            self.setDefaultRestrictionDetails(feature, self.currLayer)

            self.dialog = self.iface.getFeatureForm(self.currLayer, feature)
            self.setupDemandDialog(self.dialog, self.currLayer, feature)  # connects signals, etc
            self.dialog.show()

            #self.notifyNewFeature.emit(self.sketchPoints)

