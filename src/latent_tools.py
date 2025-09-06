# latent_tools
# Tools to help with the stuff.
#
# In Latent space no one can hear you scream...
# This is Python. There is no screaming in Python!
# Do pillows love it when we scream into them?
#
# Greg W. Moore - Jan 2025


import logging
from enum import StrEnum
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QMessageBox, QHeaderView
from PyQt6.QtGui import QIcon, QFont, QFontMetrics

logger = logging.getLogger(__name__)

def show_error_box(errormessage, severity=None):
    """
    The show an message or error dialog box the way I wanted it to show.
    Yes, I know there are QMessagebox convenience functions but I didn't like the
    look of them.
    """
    # its my app I can build it any way I want. LOL
    match severity:
        case 'critical':
            # set icon for crit
            # msg_icon = str( Path(__file__).parent.parent / 'assets/icons/darkModeIcons/exclamation-mark-triangle.svg')
            # print(f'msg_icon path: {msg_icon}')
            msg_icon = QMessageBox.Icon.Critical
        case ['warn', 'warning']:
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
    mbox.setWindowTitle('Eye strain...')
    mbox.setText(errormessage)
    mbox.setStyleSheet("font-size = 16px; font-weight = bold;")  # make it look pretty
    mbox.adjustSize()
    mbox.exec()

def clipboard_copy(pic_path, datatable):
    """ Copies metadata info to system clipboard
        requires:
            pic_path - string. FQPN of the image.
            datatable - dict. dict that contains the metadata.
    """
    # this is used by EyeSight and InfoView.
    # Copy the table's content to the clipboard.
    logger.debug('Copying table content to clipboard')
    clipboard = QApplication.clipboard()

    # if there isn't anything useful in the table, don't return anything.
    if datatable.rowCount() <= 3:
        logger.debug('nothing to copy to clipboard. clipboard set to None.')
        show_error_box('You need to select an image before you go poking buttons. <br>There is no metadata to copy.', 'warn' )
        return clipboard.setText(None)

    content = []
    content.append(f'Metadata for {pic_path}\n')
    for row in range(datatable.rowCount()):
        row_data = []
        for col in range(datatable.columnCount()):
            item = datatable.item(row, col)
            row_data.append(item.text() if item else "")
        content.append("\t".join(row_data))
    clipboard.setText("\n".join(content))
    logger.debug('Table content copied to clipboard successfully')

def read_user_config(self) :
    ...
    # FV - configparser setup for user settings.


class Settings(StrEnum):
    APPNAME = 'LatentEye'
    VERSION = '0.3.0'
    AUTHOR = 'Greg W. Moore aka AnotherWorkingNerd'
    HOMEPAGE = 'https://github.com/AnotherWorkingNerd/LatentEye'
    DOCS =  ' URL to docs' # maybe git web page with help and can tie it to F1/help
# Other stuff?


class SamplerNames(StrEnum):
    # This may be a futile attempt to convert the sampler names into
    # human readable names. I feel this may always be out of date with
    # with the speed of change in GenAI. Maybe I need to re-think
    # how I do this...

# cSpell:disable
    deis = 'DEIS - Diffusion Exponential Integrator Sampler'
    ddim = 'DDIM - Denoising Diffusion Implicit Models'
    ddpm = 'DDPM - Denoising Diffusion Probabilistic Models'
    dpm_a = 'DPM Apaptive'        # is this the actual dropdown name?
    dpm_adaptive = 'DPM Adaptive'
    dpm_fast = 'DPM fast'
    dpm_solver = 'DPM-Solver'
    dpmpp_sde = 'DPM++ SDE'
    dpmpp_sde_karras = 'DPM++ SDE Karras'
    dpm_2 = 'DPM2'
    dpm_3 = 'DPM3'
    dpm_2_ancestral = 'DPM2 Ancestral'
    dpm2_karras = 'DPM2 Karras'
    dpm2_ancestral_karras ='DPM2 a Karras'
    dpmpp_2 = 'DPM++_2'
    dpmpp_2_ancestral = 'DPM++ 2 ancestral'
    dpmpp_2m = 'DPM++ 2M'
    dpmpp_2m_sde = 'DPM++ 2M SDE'
    dpmpp_2m_sde_gpu = 'DPM++ 2M SDE GPU'
    dpmpp_2m_karras = 'DPM++ 2M Karras'
    dpmpp_2m_sgm_uniform = 'DPM++ 2m SGM Uniform'
    dpmpp_2s_ancestral = 'DPM++ 2S ancestral'
    dpmpp_2s_ancestral_karras = 'DPM++ 2S ancestral Karras'
    dpmpp_2s_ancestral_cfg_pp = 'DPM++ 2s Ancestral cfg++'
    dpmpp_3m_sde ='DPM++ 3M SDE'
    dpmpp_3m_sde_gpu ='DPM++ 3M SDE GPU'
    dpmpp_3m_karras = 'DPM++ 3M Karras'
    er_sde = 'er sde'
    euler =  'Euler'
    euler_a = 'Euler Ancestral'
    euler_ancestral = 'Euler Ancestral'
    euler_ancestral_cfg_pp = 'Euler Ancestral cfg++'
    euler_cfg_pp =  'Euler cfg++'
    heun = 'Heun'
    heunpp2 = 'Heun++ 2'
    # 'heunapp2' = 'Heun'
    idpm = 'idpm'
    idpm_v = 'idpm v'
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
    res_multistep = 'res multi-step'
    res_multistep_cfg_pp = 'res multi-step cfg++'
    res_multistep_ancestral = 'res ancestral'
    res_multistep_ancestral_cfg_pp = 'res ancestral cfg++'
    seeds_2 = 'seeds 2'
    seeds_3 = 'seeds 3'
    sa_solver = 'sa solver'
    sa_solver_pece = 'sa solver pece'
    seniorious = 'Seniorious'
    seniorious_karras = 'Seniorious Karras'
    unipc = 'UniPC'
    unipc_bh2 = 'UniPC bh2'
# cSpell:enable


class Style:
    """A collection of QSS stylesheet strings and static methods that
       that give LatentEye some Style."""

    # Qss for QProgressBar:
        # for visible chunk in the ::chunk qss use:
        #     width: 10px;
        #     margin: 0.5px;
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
    # set background and foreground colors for QToolTips.
    # the colors can be RBG values or known color names.
    # This is used by thumbnail_view.
    TOOLTIPCOLOR_QSS = f"""
            QToolTip {{
                background-color: #787878;
                color: #DAFAFA;
                font: 14pt;
                border: black solid 1px;
                padding: 2px;
            }}
        """

    @staticmethod
    def set_table_styling(table):
        """
        Add style to the passed in table.
        style consists of header row, colors, and fonts.
        Args:
            QTableWidget. Table to style
        """
        logger.debug('entering table_styling()')
        # Define fonts and colors. Eventually this should make its way to Settings.
        # so I think I'll just call this default styling. Since a QTableWidget
        # is being returned. It can be "restyled", right?

        fontsize = 15
        fontname = 'Arial'              # yea, its boring but its on every platform.
        background_color = "#5A5A5A"    # light blue
        alternate_color = "#00246B"     # dark blue
        header_color = "#0B2E40"        # dark indigo
        text_color = "#FFFFFF"          # White

        table_style_string = f"""
            QTableWidget {{
                background-color: {background_color};
                alternate-background-color: {alternate_color};
            }}
            QHeaderView::section {{
                background-color: {header_color};
                color: {text_color};
                font-size: 14pt;
            }}
            """
        table.setFont(QFont(fontname, fontsize))
        table.setAlternatingRowColors(True)
        table.setStyleSheet(table_style_string)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
