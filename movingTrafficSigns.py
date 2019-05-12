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
#from PyQt4.QtCore import
#from PyQt4.QtGui import QAction, QIcon
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
#from movingTrafficSigns_dialog import movingTrafficSignsDialog
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

import sys, os, ntpath
import numpy as np
#import cv2
import functools
import datetime
import time

from .mapTools import CreateSignTool
from .SelectTool import GeometryInfoMapTool
from .formUtils import demandFormUtils

try:
    import cv2
except ImportError:
    None

class movingTrafficSigns(demandFormUtils):
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'movingTrafficSigns_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)


        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&movingTrafficSigns')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'movingTrafficSigns')
        self.toolbar.setObjectName(u'movingTrafficSigns')

        # self.demandUtils = demandFormUtils(self.iface)


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
        return QCoreApplication.translate('movingTrafficSigns', message)


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

        # Create the dialog (after translation) and keep reference
        #self.dlg = movingTrafficSignsDialog()

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        """icon_path = ':/plugins/movingTrafficSigns/signs.png'
        self.add_action(
            icon_path,
            text=self.tr(u'movingTrafficSigns'),
            callback=self.doCreateMovingTrafficSign,
            parent=self.iface.mainWindow())"""


        """self.actionCreateMovingTrafficSign = QAction(QIcon(":/plugins/movingTrafficSigns/resources/mActionSetEndPoint.svg"),
                                                    QCoreApplication.translate("MyPlugin", "Create moving traffic sign"),
                                                    self.iface.mainWindow())
        self.actionCreateMovingTrafficSign.setCheckable(True)"""

        self.actionSignDetails = QAction(QIcon(":/plugins/movingTrafficSigns/resources/mActionGetInfo.svg"),
                               QCoreApplication.translate("MyPlugin", "Get Sign Details"),
                               self.iface.mainWindow())
        self.actionSignDetails.setCheckable(True)

        self.actionRemoveSign = QAction(QIcon(":plugins/movingTrafficSigns/resources/mActionDeleteTrack.svg"),
                               QCoreApplication.translate("MyPlugin", "Remove Sign"),
                               self.iface.mainWindow())
        self.actionRemoveSign.setCheckable(True)

        #self.toolbar.addAction(self.actionCreateMovingTrafficSign)
        self.toolbar.addAction(self.actionSignDetails)
        self.toolbar.addAction(self.actionRemoveSign)

        #self.actionCreateMovingTrafficSign.triggered.connect(self.doCreateMovingTrafficSign)
        self.actionSignDetails.triggered.connect(self.doSignDetails)
        self.actionRemoveSign.triggered.connect(self.doRemoveSign)

        #self.actionCreateMovingTrafficSign.toggled.connect(self.actionToggled)
        #self.actionCreateMovingTrafficSign.triggered.connect(self.actionTriggered)

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&movingTrafficSigns'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    def doSignDetails(self):
        """ Select point and then display details
        """
        QgsMessageLog.logMessage("In doSignDetails", tag="TOMs panel")

        #self.demandUtils.signToolChanged.emit()
        #self.demandUtils.signToolChanged.connect(self.actionToggled)
        #self.mapTool = None

        if self.actionSignDetails.isChecked():

            QgsMessageLog.logMessage("In doSignDetails - tool activated", tag="TOMs panel")

            self.currLayer = QgsMapLayerRegistry.instance().mapLayersByName("MovingTrafficSigns")[0]

            self.iface.setActiveLayer(self.currLayer)
            if not self.actionSignDetails.isChecked():
                QgsMessageLog.logMessage("In doSignDetails - resetting mapTool", tag="TOMs panel")
                self.actionSignDetails.setChecked(False)
                self.iface.mapCanvas().unsetMapTool(self.mapTool)
                self.mapTool = None
                # self.actionPan.connect()
                return

            self.actionSignDetails.setChecked(True)

            self.mapTool = GeometryInfoMapTool(self.iface)
            self.mapTool.setAction(self.actionSignDetails)
            self.iface.mapCanvas().setMapTool(self.mapTool)

            self.mapTool.notifyFeatureFound.connect(self.showSignDetails)

        else:

            QgsMessageLog.logMessage("In doSignDetails - tool deactivated", tag="TOMs panel")

            self.mapTool.notifyFeatureFound.disconnect(self.showSignDetails)
            self.iface.mapCanvas().unsetMapTool(self.mapTool)
            #del self.mapTool
            self.mapTool = None
            self.actionSignDetails.setChecked(False)


    @pyqtSlot(str)
    def showSignDetails(self, closestLayer, closestFeature):

        QgsMessageLog.logMessage(
            "In showSignDetails ... Layer: " + str(closestLayer.name()),
            tag="TOMs panel")

        if closestLayer.isEditable() == True:
            if closestLayer.commitChanges() == False:
                reply = QMessageBox.information(None, "Information",
                                                "Problem committing changes" + str(closestLayer.commitErrors()),
                                                QMessageBox.Ok)
            else:
                QgsMessageLog.logMessage("In onSaveDemandDetails: changes committed", tag="TOMs panel")

        if self.currLayer.startEditing() == False:
            reply = QMessageBox.information(None, "Information",
                                            "Could not start transaction on " + self.currLayer.name(), QMessageBox.Ok)
            return

        # TODO: Sort out this for UPDATE
        # self.setDefaultRestrictionDetails(closestFeature, closestLayer)

        self.dialog = self.iface.getFeatureForm(closestLayer, closestFeature)
        self.setupDemandDialog(self.dialog, closestLayer, closestFeature)  # connects signals, etc
        self.dialog.show()


        """def doCreateMovingTrafficSign(self):

        QgsMessageLog.logMessage("In doCreateMovingTrafficSign", tag="TOMs panel")

        #self.demandUtils.signToolChanged.emit()

        if self.actionCreateMovingTrafficSign.isChecked():

            QgsMessageLog.logMessage("In doCreateMovingTrafficSign - tool activated", tag="TOMs panel")

            self.currLayer = QgsMapLayerRegistry.instance().mapLayersByName("MovingTrafficSigns")[0]

            self.iface.setActiveLayer(self.currLayer)

            #self.actionCreateMovingTrafficSign.setChecked(True)

            self.mapTool = CreateSignTool(self.iface, self.currLayer)

            self.mapTool.setAction(self.actionCreateMovingTrafficSign)
            self.iface.mapCanvas().setMapTool(self.mapTool)

            self.mapTool.notifyNewFeature.connect(self.createNewSign)
            self.currLayer.editingStopped.connect(self.layerEditingStopped)
            self.currLayer.featureAdded.connect(self.layerfeatureAdded)

        else:

            QgsMessageLog.logMessage("In doCreateMovingTrafficSign - tool deactivated", tag="TOMs panel")

            self.mapTool.notifyNewFeature.disconnect(self.createNewSign)
            self.currLayer.editingStopped.disconnect(self.layerEditingStopped)
            self.currLayer.featureAdded.disconnect(self.layerfeatureAdded)

            self.iface.mapCanvas().unsetMapTool(self.mapTool)
            del self.mapTool
            #self.mapTool = None
            #self.actionCreateMovingTrafficSign.setChecked(False)"""

    @pyqtSlot(str)
    def actionToggled(self, answer):
        QgsMessageLog.logMessage(
            ("In actionToggled: *********************************"),
            tag="TOMs panel")

    @pyqtSlot(str)
    def actionTriggered(self, answer):
        QgsMessageLog.logMessage(
            ("In actionTriggered: *********************************"),
            tag="TOMs panel")

    @pyqtSlot(str)
    def layerEditingStopped(self):
        QgsMessageLog.logMessage(
            ("In layerEditingStopped: ********************************"),
            tag="TOMs panel")

    @pyqtSlot(str)
    def layerfeatureAdded(self, id):
        QgsMessageLog.logMessage(
            ("In layerfeatureAdded: ********************************" + str(id)),
            tag="TOMs panel")

    @pyqtSlot(str)
    def createNewSign(self, sketchPoints):

        QgsMessageLog.logMessage(
            ("In createNewSign, layerType: " + str(self.currLayer.geometryType())),
            tag="TOMs panel")

        self.sketchPoints = sketchPoints

        if self.currLayer.startEditing() == False:
            reply = QMessageBox.information(None, "Information",
                                            "Could not start transaction on " + self.currLayer.name(), QMessageBox.Ok)
            return

        fields = self.currLayer.fields()
        feature = QgsFeature(fields)
        #feature.setFields(fields)

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

    def doRemoveSign(self):

        QgsMessageLog.logMessage("In doRemoveSign", tag="TOMs panel")

        #self.demandUtils.signToolChanged.emit()

        #self.mapTool = None

        if self.actionRemoveSign.isChecked():

            QgsMessageLog.logMessage("In doSignDetails - tool activated", tag="TOMs panel")

            self.currLayer = QgsMapLayerRegistry.instance().mapLayersByName("MovingTrafficSigns")[0]

            self.iface.setActiveLayer(self.currLayer)
            if not self.actionRemoveSign.isChecked():
                QgsMessageLog.logMessage("In doSignDetails - resetting mapTool", tag="TOMs panel")
                self.actionRemoveSign.setChecked(False)
                self.iface.mapCanvas().unsetMapTool(self.mapTool)
                self.mapTool = None
                # self.actionPan.connect()
                return

            self.actionRemoveSign.setChecked(True)

            self.mapTool = GeometryInfoMapTool(self.iface)
            self.mapTool.setAction(self.actionRemoveSign)
            self.iface.mapCanvas().setMapTool(self.mapTool)

            self.mapTool.notifyFeatureFound.connect(self.removeSign)

        else:

            QgsMessageLog.logMessage("In doSignDetails - tool deactivated", tag="TOMs panel")

            self.mapTool.notifyFeatureFound.disconnect(self.removeSign)
            self.iface.mapCanvas().unsetMapTool(self.mapTool)
            del self.mapTool
            self.actionRemoveSign.setChecked(False)

    @pyqtSlot(str)
    def removeSign(self, closestLayer, closestFeature):

        QgsMessageLog.logMessage(
            "In removeSign ... Layer: " + str(closestLayer.name()),
            tag="TOMs panel")

        if closestLayer.isEditable() == True:
            if closestLayer.commitChanges() == False:
                reply = QMessageBox.information(None, "Information",
                                                "Problem committing changes" + str(closestLayer.commitErrors()),
                                                QMessageBox.Ok)
            else:
                QgsMessageLog.logMessage("In onSaveDemandDetails: changes committed", tag="TOMs panel")

        if self.currLayer.startEditing() == False:
            reply = QMessageBox.information(None, "Information",
                                            "Could not start transaction on " + self.currLayer.name(), QMessageBox.Ok)
            return

        # TODO: Sort out this for UPDATE
        # self.setDefaultRestrictionDetails(closestFeature, closestLayer)

        closestLayer.deleteFeature(closestFeature.id())

        if closestLayer.commitChanges() == False:
            reply = QMessageBox.information(None, "Information", "Problem committing changes" + str(closestLayer.commitErrors()), QMessageBox.Ok)
        else:
            QgsMessageLog.logMessage("In onSaveDemandDetails: changes committed", tag="TOMs panel")

