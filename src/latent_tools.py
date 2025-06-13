# latent_tools
# Tools to help with the stuff.
#
# In Latent space no one can hear you scream...
# This is Python. There is no screaming in Python!
# Do pillows love it when we scream into them?
#
# Greg W. Moore - Jan 2025

import os
import logging
# from enum import Enum
from enum import StrEnum
from pathlib import Path

# use configparser for user settings in yaml file? ini? json?
# from configparser import ConfigParser

from PyQt6.QtWidgets import (QApplication, QMessageBox, QWidget, QVBoxLayout, QHBoxLayout,
                             QDialog, QTableWidget,  QTableWidgetItem, QTextEdit,
                             QPushButton, QHeaderView, QLayout, QTextEdit
                             )
from PyQt6.QtCore import Qt, QDir, QSize
from PyQt6.QtGui import QIcon

logger = logging.getLogger(__name__)

class Settings(StrEnum):
    APPNAME = 'LatentEye'
    VERSION = '0.2.0'
    AUTHOR = 'Greg W. Moore aka AnotherWorkingNerd'
    HOMEPAGE = 'https://github.com/AnotherWorkingNerd/LatentEye'
    DOCS =  ' URL to docs' # maybe git web page with help and can tie it to F1/help


# https://tsak.dev/posts/python-enum/ - the case for StrEnum in python 3.11
class SamplerNames(StrEnum):
    ddim = 'DDIM - Denoising Diffusion Implicit Models'
    ddpm = 'DDPM - Denoising Diffusion Probabilistic Models'
    dpm_a = 'DPM Apaptive'        # is this the actual dropdown name?
    dpm_fast = 'DPM fast'
    dpm_2 = 'DPM2'
    dpm_3 = 'DPM3'
    dpm_2_ancestral = 'DPM2 Ancestral'
    dpm2_karras = 'DPM2 Karras'
    dpm2_ancestral_karras ='DPM2 a Karras'
    dpmpp_sde = 'DPM++ SDE'
    dpmpp_sde_karras = 'DPM++ SDE Karras'
    dpmpp_2 = 'DPM++_2'
    dpmpp_2_ancestral = 'DPM++ 2 ancestral'
    dpmpp_2m = 'DPM++ 2M'
    dpmpp_2m_sde = 'DPM++ 2M SDE'
    dpmpp_2m_sde_gpu = 'DPM++ 2M SDE GPU'
    dpmpp_2m_karras = 'DPM++ 2M Karras'
    dpmpp_2s_ancestral = 'DPM++ 2S ancestral'
    dpmpp_2s_ancestral_karras = 'DPM++ 2S ancestral Karras'
    dpmpp_3m_sde ='DPM++ 3M SDE'
    dpmpp_3m_sde_gpu ='DPM++ 3M SDE GPU'
    dpmpp_3m_karras = 'DPM++ 3M Karras'
    dpm_adaptive = 'DPM Adaptive'
    dpm_solver = 'DPM-Solver'
    euler_a = 'Euler Ancestral'
    eulera = 'Euler Ancestral'
    euler =  'Euler'
    heun = 'Heun'
    heunpp2 = 'Heun++ 2'
    # 'heunapp2' = 'Heun'
    k_lms = 'LMS'
    k_euler_ancestral = 'Euler Ancestral'
    k_euler = 'Euler'
    k_heun = 'Heun'
    k_dpm_2 = 'DPM2'
    k_dpm_2_ancestral = 'DPM2 Ancestral'
    lcm = 'LCM - Latent Control Models'
    lms = 'LMS - Laplacian Pyramid Sampling'
    lms_karras = 'LMS Karras'
    plms = 'PLMS - Predictive Linear Multistep Sampling'
    restart= 'Restart'
    seniorious = 'Seniorious'
    seniorious_karras = 'Seniorious Karras'
    unipc = 'UniPC'

def show_error_box(errormessage, severity=None):
    #
    logger.debug(f'show_error_box: errormessage: {errormessage} - severity: {severity}')

    match severity:
        case 'critical':
            # set icon for crit
            # msg_icon = str( Path(__file__).parent.parent / 'assets/icons/darkModeIcons/exclamation-mark-triangle.svg')
            # print(f'msg_icon path: {msg_icon}')
            msg_icon = QMessageBox.Icon.Critical
        case 'warn':
            # set icon for warning
            msg_icon = QMessageBox.Icon.Warning
        case 'info':
            # set icon for info
            msg_icon = QMessageBox.Icon.Information
        case 'question':
            # set icon for info
            msg_icon = QMessageBox.Icon.Question
        case _:
            # default case - info message
            msg_icon = QMessageBox.Icon.Information

    mbox = QMessageBox()
    mbox.setIcon(msg_icon)
    # mbox.setWindowTitle('Stuff Happened.')
    mbox.setText(errormessage)
    mbox.setStyleSheet("font-size = 16px; font-weight = bold;")  # make it look pretty
    mbox.adjustSize()
    mbox.exec()

# this is used by EyeSight and InfoView.
# Renamed the method so as not to get confused.
def clipboard_copy(self, tablename):
    # Copy the table's content to the clipboard.
    logger.debug('Copying table content to clipboard')
    clipboard = QApplication.clipboard()

    # if there isn't anything useful in the table, don't return anything.
    if tablename.rowCount() <= 3:
        logger.debug('nothing to copy to clipboard. clipboard set to None.')
        return clipboard.setText(None)

    content = []
    content.append(f'Metadata for {self.picture_path}\n')
    for row in range(tablename.rowCount()):
        row_data = []
        for col in range(tablename.columnCount()):
            item = tablename.item(row, col)
            row_data.append(item.text() if item else "")
        content.append("\t".join(row_data))
    clipboard.setText("\n".join(content))
    logger.debug('Table content copied successfully')

def ttip_color(fore, back='#787878'):
    # set background and foreground colors for QToolTips
    """Returns a QSS stylesheet string for QToolTip
       with the specified background and foreground colors
       using either known color names or hex RGB values like
       'white', 'darkkhaki' or '#00246B'. The border is set
       to `black 1px` so TT shows. Without a border, No TT.
       foreground color is required.
       background color is optional. Default value: '#787878'
       usage:
            label.setStyleSheet(ttip_color('#FAFAFA'))
            label.setStyleSheet(ttip_color('#DECADE','#FABCAD'))
            ttip_color('#FACADE')
    """

    return f"""
        QToolTip {{
            background-color: {back};
            color: {fore};
            font: 14pt;
            border: black solid 1px;
            padding: 2px;
        }}
    """

def read_user_config(self) :
    ...
    # WIP configparser setup for user settings.

class Style:
    """ A collection of QSS stylesheet strings that are used by LatentEye."""

    # Qss for QProgressBar:
    PROGRESSBAR_QSS = f"""
        QProgressBar {{
            border: 2px solid grey;
            border-radius: 5px;
            text-align: center;
        }}
        QProgressBar::chunk {{
            background-color: #05B8CC;
            width: 20px;
        }}
"""
