# -*- coding: utf-8 -*-
"""
/***************************************************************************
 movingTrafficSigns
                                 A QGIS plugin
 movingTrafficeSigns
                             -------------------
        begin                : 2019-05-08
        copyright            : (C) 2019 by TH
        email                : th@mhtc.co.uk
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load movingTrafficSigns class from file movingTrafficSigns.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .movingTrafficSigns import movingTrafficSigns
    return movingTrafficSigns(iface)
