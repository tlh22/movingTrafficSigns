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
from movingTrafficSigns_dialog import movingTrafficSignsDialog
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

try:
    import cv2
except ImportError:
    None

class movingTrafficSigns:
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
        self.dlg = movingTrafficSignsDialog()

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


        self.actionCreateMovingTrafficSign = QAction(QIcon(":/plugins/movingTrafficSigns/resources/mActionSetEndPoint.svg"),
                                                    QCoreApplication.translate("MyPlugin", "Create moving traffic sign"),
                                                    self.iface.mainWindow())
        self.actionCreateMovingTrafficSign.setCheckable(True)

        self.actionSignDetails = QAction(QIcon(":/plugins/movingTrafficSigns/resources/mActionGetInfo.svg"),
                               QCoreApplication.translate("MyPlugin", "Get Sign Details"),
                               self.iface.mainWindow())
        self.actionSignDetails.setCheckable(True)

        self.actionRemoveSign = QAction(QIcon(":plugins/movingTrafficSigns/resources/mActionDeleteTrack.svg"),
                               QCoreApplication.translate("MyPlugin", "Remove Sign"),
                               self.iface.mainWindow())
        self.actionRemoveSign.setCheckable(True)


        self.toolbar.addAction(self.actionCreateMovingTrafficSign)
        self.toolbar.addAction(self.actionSignDetails)
        self.toolbar.addAction(self.actionRemoveSign)

        self.actionCreateMovingTrafficSign.triggered.connect(self.doCreateMovingTrafficSign)
        self.actionSignDetails.triggered.connect(self.doSignDetails)
        self.actionRemoveSign.triggered.connect(self.doRemoveSign)

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

        #self.proposalsManager.TOMsToolChanged.emit()

        self.currLayer = QgsMapLayerRegistry.instance().mapLayersByName("MovingTrafficSigns")[0]

        if self.currLayer.startEditing() == False:
            reply = QMessageBox.information(None, "Information",
                                            "Could not start transaction on " + self.currLayer.name(), QMessageBox.Ok)
            return

        self.iface.setActiveLayer(self.currLayer)
        if not self.actionSignDetails.isChecked():
            self.actionSignDetails.setChecked(False)
            self.iface.mapCanvas().unsetMapTool(self.mapTool)
            self.mapTool = None
            # self.actionPan.connect()
            return

        self.actionSignDetails.setChecked(True)

        self.mapTool = GeometryInfoMapTool(self.iface)
        self.mapTool.setAction(self.actionSignDetails)
        self.iface.mapCanvas().setMapTool(self.mapTool)



    def doCreateMovingTrafficSign(self):

        QgsMessageLog.logMessage("In doCreateMovingTrafficSign", tag="TOMs panel")

        #self.proposalsManager.TOMsToolChanged.emit()

        self.mapTool = None

        # Get the current proposal from the session variables
        #currProposalID = self.proposalsManager.currentProposal()

        #if currProposalID > 0:

        if self.actionCreateMovingTrafficSign.isChecked():
            # self.iface.mapCanvas().setMapTool(CreateRestrictionTool)
            # self.actionCreateRestiction.setChecked(True)

            # set TOMs layer as active layer (for editing)...

            QgsMessageLog.logMessage("In doCreateMovingTrafficSign - tool activated", tag="TOMs panel")

            #self.restrictionTransaction.startTransactionGroup()  # start editing

            self.currLayer = QgsMapLayerRegistry.instance().mapLayersByName("MovingTrafficSigns")[0]

            if self.currLayer.startEditing() == False:
                reply = QMessageBox.information(None, "Information", "Could not start transaction on " + self.currLayer.name(), QMessageBox.Ok)
                return

            #currLayer = self.tableNames.BAYS

            self.iface.setActiveLayer(self.currLayer)

            #self.restrictionTransaction.startTransactionGroup()  # start editing

            self.mapTool = CreateSignTool(self.iface, self.currLayer)

            self.mapTool.setAction(self.actionCreateMovingTrafficSign)
            self.iface.mapCanvas().setMapTool(self.mapTool)

            #self.currLayer.featureAdded.connect(self.proposalsManager.updateMapCanvas)

            #self.currLayer.editingStopped.connect (self.proposalsManager.updateMapCanvas)

        else:

            QgsMessageLog.logMessage("In doCreateMovingTrafficSign - tool deactivated", tag="TOMs panel")

            self.iface.mapCanvas().unsetMapTool(self.mapTool)
            self.mapTool = None
            self.actionCreateMovingTrafficSign.setChecked(False)

            #self.currLayer.featureAdded.disconnect(self.proposalsManager.updateMapCanvas)

            #self.currLayer.editingStopped()

        """else:

            if self.actionCreateBayRestriction.isChecked():
                self.actionCreateBayRestriction.setChecked(False)
                if self.mapTool == None:
                    self.actionCreateBayRestriction.setChecked(False)

            reply = QMessageBox.information(self.iface.mainWindow(), "Information", "Changes to current data is not allowed. Changes are made via Proposals",
                                            QMessageBox.Ok)

        pass"""

    def doRemoveSign(self):

        QgsMessageLog.logMessage("In doRemoveSign", tag="TOMs panel")

        #self.proposalsManager.TOMsToolChanged.emit()

        #self.mapTool = None

        # Get the current proposal from the session variables
        #self.currProposalID = self.proposalsManager.currentProposal()

        if self.currProposalID > 0:

            currRestrictionLayer = self.iface.activeLayer()

            #currRestrictionLayer.editingStopped.connect(self.proposalsManager.updateMapCanvas)

            if currRestrictionLayer:

                QgsMessageLog.logMessage("In doRemoveRestriction. currLayer: " + str(currRestrictionLayer.name()), tag="TOMs panel")

                if currRestrictionLayer.selectedFeatureCount() > 0:

                    selectedRestrictions = currRestrictionLayer.selectedFeatures()

                    self.restrictionTransaction.startTransactionGroup()

                    for currRestriction in selectedRestrictions:
                        self.onRemoveRestriction(currRestrictionLayer, currRestriction)

                else:

                    reply = QMessageBox.information(self.iface.mainWindow(), "Information",
                                                    "Select restriction for delete",
                                                    QMessageBox.Ok)

            pass

        else:

            """if self.actionRemoveRestriction.isChecked():
                self.actionRemoveRestriction.setChecked(False)
                if self.mapTool == None:
                    self.actionRemoveRestriction.setChecked(False)"""

            reply = QMessageBox.information(self.iface.mainWindow(), "Information", "Changes to current data are not allowed. Changes are made via Proposals",
                                            QMessageBox.Ok)

        pass

    def onRemoveRestriction(self, currRestrictionLayer, currRestriction):
        QgsMessageLog.logMessage("In onRemoveRestriction. currLayer: " + str(currRestrictionLayer.id()) + " CurrFeature: " + str(currRestriction.id()), tag="TOMs panel")

        #self.currRestrictionLayer = currRestrictionLayer
        #self.currRestriction = currRestriction

        currProposalID = self.proposalsManager.currentProposal()

        currRestrictionLayerID = self.getRestrictionLayerTableID(currRestrictionLayer)

        idxRestrictionID = currRestriction.fieldNameIndex("RestrictionID")

        if self.restrictionInProposal(currRestriction[idxRestrictionID], currRestrictionLayerID, currProposalID):
            # remove the restriction from the RestrictionsInProposals table - and from the currLayer, i.e., it is totally removed.
            # NB: This is the only case of a restriction being truly deleted

            QgsMessageLog.logMessage("In onRemoveRestriction. Removing from RestrictionsInProposals and currLayer.", tag="TOMs panel")

            # Delete from RestrictionsInProposals
            result = self.deleteRestrictionInProposal(currRestriction[idxRestrictionID], currRestrictionLayerID, currProposalID)

            if result:
                QgsMessageLog.logMessage("In onRemoveRestriction. Deleting restriction id: " + str(currRestriction.id()),
                                         tag="TOMs panel")
                deleteStatus = currRestrictionLayer.deleteFeature(currRestriction.id())
                QgsMessageLog.logMessage("In onRemoveRestriction. deleteStatus: " + str(deleteStatus),
                                     tag="TOMs panel")

            else:
                QMessageBox.information(None, "ERROR", ("Error deleting restriction ..."))

        else:
            # need to:
            #    - enter the restriction into the table RestrictionInProposals as closed, and
            #
            QgsMessageLog.logMessage("In onRemoveRestriction. Closing existing restriction.",
                                     tag="TOMs panel")

            self.addRestrictionToProposal(currRestriction[idxRestrictionID], currRestrictionLayerID, currProposalID,
                                                          ACTION_CLOSE_RESTRICTION())  # 2 = Close

        # Now save all changes

        # Trying to unset map tool to force updates ...
        #self.iface.mapCanvas().unsetMapTool(self.iface.mapCanvas().mapTool())

        self.restrictionTransaction.commitTransactionGroup(None)
        #self.restrictionTransaction.deleteTransactionGroup()

        #currRestrictionLayer.triggerRepaint()  # This shouldn't be required ...




class demandFormUtils():
    def __init__(self, iface):
        self.iface = iface

    def setDefaultRestrictionDetails(self, currRestriction, currRestrictionLayer):
        QgsMessageLog.logMessage("In setDefaultRestrictionDetails: ", tag="TOMs panel")

        self.userName = (QgsExpressionContextUtils.globalScope().variable("user_full_name"))
        QgsMessageLog.logMessage("In setDefaultRestrictionDetails: curr user name: " + self.userName, tag="TOMs panel")

        try:
            currRestriction.setAttribute("Signs_DateTime", QDateTime.currentDateTime())
            currRestriction.setAttribute("Surveyor", self.userName)
        except:
            reply = QMessageBox.information(None, "Information", "Problems with default values ...",
                                            QMessageBox.Ok)
        #generateGeometryUtils.setRoadName(currRestriction)

    def setupDemandDialog(self, demandDialog, currDemandLayer, currFeature):

        # self.restrictionDialog = restrictionDialog
        self.demandDialog = demandDialog
        #self.demandAttributeForm = self.demandDialog.attributeForm()
        #self.demandAttributeForm = self.demandDialog
        self.currDemandLayer = currDemandLayer
        self.currFeature = currFeature
        # self.restrictionTransaction = restrictionTransaction


        if self.demandDialog is None:
            QgsMessageLog.logMessage(
                "In setupDemandDialog. dialog not found",
                tag="TOMs panel")

        button_box = self.demandDialog.findChild(QDialogButtonBox, "button_box")

        if button_box is None:
            QgsMessageLog.logMessage(
                "In setupDemandDialog. button box not found",
                tag="TOMs panel")
            reply = QMessageBox.information(None, "Information", "Please reset form. There are missing buttons",
                                            QMessageBox.Ok)
            return

        self.demandDialog.attributeForm().disconnectButtonBox()
        try:
            button_box.accepted.disconnect()
        except:
            None

        button_box.accepted.connect(functools.partial(self.onSaveDemandDetails, currFeature,
                                                      currDemandLayer, self.demandDialog))

        try:
            button_box.rejected.disconnect()
        except:
            None

        button_box.rejected.connect(self.onRejectDemandDetailsFromForm)

        self.demandDialog.attributeForm().attributeChanged.connect(
            functools.partial(self.onAttributeChangedClass2, self.currFeature, self.currDemandLayer))

        self.photoDetails()

    def onSaveDemandDetails(self, currFeature, currFeatureLayer, dialog):
        QgsMessageLog.logMessage("In onSaveDemandDetails: ", tag="TOMs panel")

        try:
            self.camera1.endCamera()
        except:
            None

        attrs1 = currFeature.attributes()
        QgsMessageLog.logMessage("In onSaveRestrictionDetails: currRestriction: " + str(attrs1),
                                 tag="TOMs panel")

        if currFeatureLayer.updateFeature(currFeature) == False:
            status = currFeatureLayer.addFeature(currFeature)
            QgsMessageLog.logMessage("In onSaveDemandDetails: added Feature: " + str(status), tag="TOMs panel")
        else:
            QgsMessageLog.logMessage("In onSaveDemandDetails: updated Feature: ", tag="TOMs panel")

        if currFeatureLayer.commitChanges() == False:
            reply = QMessageBox.information(None, "Information", "Problem committing changes" + str(currFeatureLayer.commitErrors()), QMessageBox.Ok)
        else:
            QgsMessageLog.logMessage("In onSaveDemandDetails: changes committed", tag="TOMs panel")

        status = dialog.close()

    def onRejectDemandDetailsFromForm(self):
        QgsMessageLog.logMessage("In onRejectDemandDetailsFromForm", tag="TOMs panel")
        # self.currDemandLayer.destroyEditCommand()

        try:
            self.camera1.endCamera()
        except:
            None

        self.demandDialog.reject()

        if self.currDemandLayer.rollBack() == False:
            reply = QMessageBox.information(None, "Information", "Problem rolling back changes", QMessageBox.Ok)
        else:
            QgsMessageLog.logMessage("In onRejectDemandDetailsFromForm: rollBack successful ...", tag="TOMs panel")


    def onAttributeChangedClass2(self, currFeature, layer, fieldName, value):
        QgsMessageLog.logMessage(
            "In FormOpen:onAttributeChangedClass 2 - layer: " + str(layer.name()) + " (" + fieldName + "): " + str(
                value), tag="TOMs panel")

        # self.currFeature.setAttribute(fieldName, value)
        try:

            currFeature[layer.fieldNameIndex(fieldName)] = value
            # currFeature.setAttribute(layer.fieldNameIndex(fieldName), value)

        except:

            reply = QMessageBox.information(None, "Error",
                                            "onAttributeChangedClass2. Update failed for: " + str(
                                                layer.name()) + " (" + fieldName + "): " + str(value),
                                            QMessageBox.Ok)  # rollback all changes
        return

    def transformCoordinates(self, screenPt):
        """ Convert a screen coordinate to map and layer coordinates.

            returns a (mapPt,layerPt) tuple.
        """
        return (self.toMapCoordinates(screenPt))

    def photoDetails(self):

        # Function to deal with photo fields

        QgsMessageLog.logMessage("In photoDetails", tag="TOMs panel")

        FIELD1 = self.demandDialog.findChild(QLabel, "Photo_Widget_01")
        FIELD2 = self.demandDialog.findChild(QLabel, "Photo_Widget_02")
        FIELD3 = self.demandDialog.findChild(QLabel, "Photo_Widget_03")

        photoPath = QgsExpressionContextUtils.projectScope().variable('PhotoPath')
        projectFolder = QgsExpressionContextUtils.projectScope().variable('project_folder')
        path_absolute = os.path.join(projectFolder, photoPath)

        if path_absolute == None:
            reply = QMessageBox.information(None, "Information", "Please set value for PhotoPath.", QMessageBox.Ok)
            return

        # Check path exists ...
        if os.path.isdir(path_absolute) == False:
            reply = QMessageBox.information(None, "Information", "PhotoPath folder " + str(
                path_absolute) + " does not exist. Please check value.", QMessageBox.Ok)
            return

        layerName = self.currDemandLayer.name()

        # Generate the full path to the file

        # fileName1 = "Photos"
        fileName1 = "Photos_01"
        fileName2 = "Photos_02"
        fileName3 = "Photos_03"

        idx1 = self.currDemandLayer.fieldNameIndex(fileName1)
        idx2 = self.currDemandLayer.fieldNameIndex(fileName2)
        idx3 = self.currDemandLayer.fieldNameIndex(fileName3)

        QgsMessageLog.logMessage("In photoDetails. idx1: " + str(idx1) + "; " + str(idx2) + "; " + str(idx3),
                                 tag="TOMs panel")
        # if currFeatureFeature[idx1]:
        # QgsMessageLog.logMessage("In photoDetails. photo1: " + str(currFeatureFeature[idx1]), tag="TOMs panel")
        # QgsMessageLog.logMessage("In photoDetails. photo2: " + str(currFeatureFeature.attribute(idx2)), tag="TOMs panel")
        # QgsMessageLog.logMessage("In photoDetails. photo3: " + str(currFeatureFeature.attribute(idx3)), tag="TOMs panel")

        if FIELD1:
            QgsMessageLog.logMessage("In photoDetails. FIELD 1 exisits",
                                     tag="TOMs panel")
            if self.currFeature[idx1]:
                newPhotoFileName1 = os.path.join(path_absolute, self.currFeature[idx1])
            else:
                newPhotoFileName1 = None

            # QgsMessageLog.logMessage("In photoDetails. Photo1: " + str(newPhotoFileName1), tag="TOMs panel")
            pixmap1 = QPixmap(newPhotoFileName1)
            if pixmap1.isNull():
                pass
                # FIELD1.setText('Picture could not be opened ({path})'.format(path=newPhotoFileName1))
            else:
                FIELD1.setPixmap(pixmap1)
                FIELD1.setScaledContents(True)
                QgsMessageLog.logMessage("In photoDetails. Photo1: " + str(newPhotoFileName1), tag="TOMs panel")

            START_CAMERA_1 = self.demandDialog.findChild(QPushButton, "startCamera1")
            TAKE_PHOTO_1 = self.demandDialog.findChild(QPushButton, "getPhoto1")
            TAKE_PHOTO_1.setEnabled(False)

            self.camera1 = formCamera(path_absolute, newPhotoFileName1)
            START_CAMERA_1.clicked.connect(
                functools.partial(self.camera1.useCamera, START_CAMERA_1, TAKE_PHOTO_1, FIELD1))
            self.camera1.notifyPhotoTaken.connect(functools.partial(self.savePhotoTaken, idx1))

        if FIELD2:
            QgsMessageLog.logMessage("In photoDetails. FIELD 2 exisits",
                                     tag="TOMs panel")
            if self.currFeature[idx2]:
                newPhotoFileName2 = os.path.join(path_absolute, self.currFeature[idx2])
            else:
                newPhotoFileName2 = None

            # newPhotoFileName2 = os.path.join(path_absolute, str(self.currFeature[idx2]))
            # newPhotoFileName2 = os.path.join(path_absolute, str(self.currFeature.attribute(fileName2)))
            # QgsMessageLog.logMessage("In photoDetails. Photo2: " + str(newPhotoFileName2), tag="TOMs panel")
            pixmap2 = QPixmap(newPhotoFileName2)
            if pixmap2.isNull():
                pass
                # FIELD1.setText('Picture could not be opened ({path})'.format(path=newPhotoFileName1))
            else:
                FIELD2.setPixmap(pixmap2)
                FIELD2.setScaledContents(True)
                QgsMessageLog.logMessage("In photoDetails. Photo2: " + str(newPhotoFileName2), tag="TOMs panel")

            START_CAMERA_2 = self.demandDialog.findChild(QPushButton, "startCamera2")
            TAKE_PHOTO_2 = self.demandDialog.findChild(QPushButton, "getPhoto2")
            TAKE_PHOTO_2.setEnabled(False)

            self.camera2 = formCamera(path_absolute, newPhotoFileName2)
            START_CAMERA_2.clicked.connect(
                functools.partial(self.camera2.useCamera, START_CAMERA_2, TAKE_PHOTO_2, FIELD2))
            self.camera2.notifyPhotoTaken.connect(functools.partial(self.savePhotoTaken, idx2))

        if FIELD3:
            QgsMessageLog.logMessage("In photoDetails. FIELD 3 exisits",
                                     tag="TOMs panel")

            if self.currFeature[idx3]:
                newPhotoFileName3 = os.path.join(path_absolute, self.currFeature[idx3])
            else:
                newPhotoFileName3 = None

            # newPhotoFileName3 = os.path.join(path_absolute, str(self.currFeature[idx3]))
            # newPhotoFileName3 = os.path.join(path_absolute,
            #                                 str(self.currFeature.attribute(fileName3)))
            # newPhotoFileName3 = os.path.join(path_absolute, str(layerName + "_Photos_03"))

            # QgsMessageLog.logMessage("In photoDetails. Photo3: " + str(newPhotoFileName3), tag="TOMs panel")
            pixmap3 = QPixmap(newPhotoFileName3)
            if pixmap3.isNull():
                pass
                # FIELD1.setText('Picture could not be opened ({path})'.format(path=newPhotoFileName1))
            else:
                FIELD3.setPixmap(pixmap3)
                FIELD3.setScaledContents(True)
                QgsMessageLog.logMessage("In photoDetails. Photo3: " + str(newPhotoFileName3), tag="TOMs panel")

            START_CAMERA_3 = self.demandDialog.findChild(QPushButton, "startCamera3")
            TAKE_PHOTO_3 = self.demandDialog.findChild(QPushButton, "getPhoto3")
            TAKE_PHOTO_3.setEnabled(False)

            self.camera3 = formCamera(path_absolute, newPhotoFileName3)
            START_CAMERA_3.clicked.connect(
                functools.partial(self.camera3.useCamera, START_CAMERA_3, TAKE_PHOTO_3, FIELD3))
            self.camera3.notifyPhotoTaken.connect(functools.partial(self.savePhotoTaken, idx3))

        pass

    @pyqtSlot(str)
    def savePhotoTaken(self, idx, fileName):
        QgsMessageLog.logMessage("In demandFormUtils::savePhotoTaken ... " + fileName + " idx: " + str(idx),
                                 tag="TOMs panel")
        if len(fileName) > 0:
            simpleFile = ntpath.basename(fileName)
            QgsMessageLog.logMessage("In demandFormUtils::savePhotoTaken. Simple file: " + simpleFile,
                                     tag="TOMs panel")

            try:
                self.currFeature[idx] = simpleFile
                #self.currFeature.setAttribute(idx, simpleFile)
                QgsMessageLog.logMessage("In demandFormUtils::savePhotoTaken. attrib value changed",
                                         tag="TOMs panel")
            except:
                QgsMessageLog.logMessage("In demandFormUtils::savePhotoTaken. problem changing attrib value",
                                         tag="TOMs panel")
                reply = QMessageBox.information(None, "Error",
                                                "savePhotoTaken. problem changing attrib value",
                                                QMessageBox.Ok)

#############################################################################

class GeometryInfoMapTool(QgsMapToolIdentify, demandFormUtils):
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

            # TODO: Sort out this for UPDATE
            # self.setDefaultRestrictionDetails(closestFeature, closestLayer)

            QgsMessageLog.logMessage(
                "In GeometryInfoMapTool - releaseEvent. currRestrictionLayer: " + str(closestLayer.name()),
                tag="TOMs panel")

            dialog = self.iface.getFeatureForm(closestLayer, closestFeature)
            self.setupDemandDialog(dialog, closestLayer, closestFeature)  # connects signals, etc
            dialog.show()

        pass

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

            QgsMessageLog.logMessage("In findNearestFeatureAt: feature: " + str(feature.attribute('GeometryID')),
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

                title = feature.attribute('id')
                QgsMessageLog.logMessage("In featureContextMenu: adding: " + str(title), tag="TOMs panel")

            except TypeError:

                title = " (" + feature.attribute('SignType_1') + ")"

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
            if feature.attribute("id") == selectedGeometryID:
                return idx

        pass

        return idx

#############################################################################
class CreateSignTool(QgsMapToolCapture, demandFormUtils):
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

        self.currLayer = self.currentVectorLayer()

        QgsMessageLog.logMessage(("In CreateSignTool - init. Curr layer is " + str(self.currLayer.name()) + "Incoming: " + str(self.layer)), tag="TOMs panel")

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

            # take points from the rubber band and copy them into the "feature"

            fields = self.layer.dataProvider().fields()
            feature = QgsFeature()
            feature.setFields(fields)

            QgsMessageLog.logMessage(("In CreateRestrictionTool. getPointsCaptured, layerType: " + str(self.layer.geometryType())), tag="TOMs panel")

            if self.layer.geometryType() == 0:  # Point
                feature.setGeometry(QgsGeometry.fromPoint(self.sketchPoints[0]))
            elif self.layer.geometryType() == 1:  # Line
                feature.setGeometry(QgsGeometry.fromPolyline(self.sketchPoints))
            elif self.layer.geometryType() == 2:  # Polygon
                feature.setGeometry(QgsGeometry.fromPolygon([self.sketchPoints]))
                #feature.setGeometry(QgsGeometry.fromPolygon(self.sketchPoints))
            else:
                QgsMessageLog.logMessage(("In CreateRestrictionTool - no geometry type found"), tag="TOMs panel")
                return

            QgsMessageLog.logMessage(("In Create - getPointsCaptured; geometry prepared; " + str(feature.geometry().exportToWkt())),
                                     tag="TOMs panel")

            if self.layer.name() == "ConstructionLines":
                self.layer.addFeature(feature)
                pass
            else:

                # set any geometry related attributes ...

                self.setDefaultRestrictionDetails(feature, self.layer)

                QgsMessageLog.logMessage("In In CreateRestrictionTool - getPointsCaptured. currRestrictionLayer: " + str(self.layer.name()),
                                         tag="TOMs panel")

                dialog = self.iface.getFeatureForm(self.layer, feature)
                self.setupDemandDialog(dialog, self.layer, feature)  # connects signals, etc
                dialog.show()

            pass

class formCamera(QObject):
    notifyPhotoTaken = QtCore.pyqtSignal(str)

    def __init__(self, path_absolute, currFileName):
        QtCore.QObject.__init__(self)
        self.path_absolute = path_absolute
        self.currFileName = currFileName
        self.camera = cvCamera()

    @pyqtSlot(QPixmap)
    def displayFrame(self, pixmap):
        # QgsMessageLog.logMessage("In formCamera::displayFrame ... ", tag="TOMs panel")
        self.FIELD.setPixmap(pixmap)
        self.FIELD.setScaledContents(True)
        QApplication.processEvents()  # processes the event queue - https://stackoverflow.com/questions/43094589/opencv-imshow-prevents-qt-python-crashing

    def useCamera(self, START_CAMERA_BUTTON, TAKE_PHOTO_BUTTON, FIELD):
        QgsMessageLog.logMessage("In formCamera::useCamera ... ", tag="TOMs panel")
        self.START_CAMERA_BUTTON = START_CAMERA_BUTTON
        self.TAKE_PHOTO_BUTTON = TAKE_PHOTO_BUTTON
        self.FIELD = FIELD

        # self.blockSignals(True)
        self.START_CAMERA_BUTTON.clicked.disconnect()
        self.START_CAMERA_BUTTON.clicked.connect(self.endCamera)

        """ Camera code  """

        self.camera.changePixmap.connect(self.displayFrame)
        self.camera.closeCamera.connect(self.endCamera)

        self.TAKE_PHOTO_BUTTON.setEnabled(True)
        self.TAKE_PHOTO_BUTTON.clicked.connect(functools.partial(self.camera.takePhoto, self.path_absolute))
        self.camera.photoTaken.connect(self.checkPhotoTaken)
        self.photoTaken = False

        QgsMessageLog.logMessage("In formCamera::useCamera: starting camera ... ", tag="TOMs panel")

        self.camera.startCamera()

    def endCamera(self):

        QgsMessageLog.logMessage("In formCamera::endCamera: stopping camera ... ", tag="TOMs panel")

        self.camera.stopCamera()
        self.camera.changePixmap.disconnect(self.displayFrame)
        self.camera.closeCamera.disconnect(self.endCamera)

        # del self.camera

        self.TAKE_PHOTO_BUTTON.setEnabled(False)
        self.START_CAMERA_BUTTON.setChecked(False)
        self.TAKE_PHOTO_BUTTON.clicked.disconnect()

        self.START_CAMERA_BUTTON.clicked.disconnect()
        self.START_CAMERA_BUTTON.clicked.connect(
            functools.partial(self.useCamera, self.START_CAMERA_BUTTON, self.TAKE_PHOTO_BUTTON, self.FIELD))

        if self.photoTaken == False:
            self.resetPhoto()

    @pyqtSlot(str)
    def checkPhotoTaken(self, fileName):
        QgsMessageLog.logMessage("In formCamera::photoTaken: file: " + fileName, tag="TOMs panel")

        if len(fileName) > 0:
            self.photoTaken = True
            self.notifyPhotoTaken.emit(fileName)
        else:
            self.resetPhoto()
            self.photoTaken = False

    def resetPhoto(self):
        QgsMessageLog.logMessage("In formCamera::resetPhoto ... ", tag="TOMs panel")

        pixmap = QPixmap(self.currFileName)
        if pixmap.isNull():
            pass
        else:
            self.FIELD.setPixmap(pixmap)
            self.FIELD.setScaledContents(True)


class cvCamera(QThread):
    changePixmap = QtCore.pyqtSignal(QPixmap)
    closeCamera = QtCore.pyqtSignal()
    photoTaken = QtCore.pyqtSignal(str)

    def __init__(self):
        QtCore.QThread.__init__(self)

    def stopCamera(self):
        QgsMessageLog.logMessage("In cvCamera::stopCamera ... ", tag="TOMs panel")
        self.cap.release()

    def startCamera(self):

        QgsMessageLog.logMessage("In cvCamera::startCamera: ... ", tag="TOMs panel")

        self.cap = cv2.VideoCapture(0)  # video capture source camera (Here webcam of laptop)

        self.cap.set(3, 640)  # width=640
        self.cap.set(4, 480)  # height=480

        while self.cap.isOpened():
            self.getFrame()
            # cv2.imshow('img1',self.frame) #display the captured image
            # cv2.waitKey(1)
            time.sleep(0.1)  # QTimer::singleShot()
        else:
            QgsMessageLog.logMessage("In cvCamera::startCamera: camera closed ... ", tag="TOMs panel")
            self.closeCamera.emit()

    def getFrame(self):

        """ Camera code  """

        # QgsMessageLog.logMessage("In cvCamera::getFrame ... ", tag="TOMs panel")

        ret, self.frame = self.cap.read()  # return a single frame in variable `frame`

        if ret == True:
            # Need to change from BRG (cv::mat) to RGB image
            cvRGBImg = cv2.cvtColor(self.frame, cv2.cv.CV_BGR2RGB)
            qimg = QImage(cvRGBImg.data, cvRGBImg.shape[1], cvRGBImg.shape[0], QImage.Format_RGB888)

            # Now display ...
            pixmap = QPixmap.fromImage(qimg)

            self.changePixmap.emit(pixmap)

        else:

            QgsMessageLog.logMessage("In cvCamera::useCamera: frame not returned ... ", tag="TOMs panel")
            self.closeCamera.emit()

    def takePhoto(self, path_absolute):

        QgsMessageLog.logMessage("In cvCamera::takePhoto ... ", tag="TOMs panel")
        # Save frame to file

        fileName = 'Photo_{}.png'.format(datetime.datetime.now().strftime('%Y%m%d_%H%M%S%z'))
        newPhotoFileName = os.path.join(path_absolute, fileName)

        QgsMessageLog.logMessage("Saving photo: file: " + newPhotoFileName, tag="TOMs panel")
        writeStatus = cv2.imwrite(newPhotoFileName, self.frame)

        if writeStatus is True:
            reply = QMessageBox.information(None, "Information", "Photo captured.", QMessageBox.Ok)
            self.photoTaken.emit(newPhotoFileName)
        else:
            reply = QMessageBox.information(None, "Information", "Problem taking photo.", QMessageBox.Ok)
            self.photoTaken.emit()

        # Now stop camera (and display image)

        self.cap.release()

        """def fps(self):
            fps = int(cv.GetCaptureProperty(self._cameraDevice, cv.CV_CAP_PROP_FPS))
            if not fps > 0:
                fps = self._DEFAULT_FPS
            return fps"""
        # https://stackoverflow.com/questions/44404349/pyqt-showing-video-stream-from-opencv
