# info_view.py
# metadata display and maybe workflow.
#
# this is used by main_window to display the SD metadata info
# contained in a given image.
#
# This has a rather generic name and while, right now, the
# primary function is to display the Stable Diffusion
# metadata that is stored in the generated images at some
# point there may be additional features added to this class.
# Most likely this will be for the Comfy workflows but who
# knows what else.
#

import logging
from pathlib import Path

from PyQt6.QtCore import Qt, QDir, QSize
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QDialog,
                             QTableWidget,  QTableWidgetItem, QTextEdit, QPushButton,
                             QMessageBox)
from PyQt6.QtGui import QIcon

from .metadatatable import MetadataTable
from .latent_tools import Settings, clipboard_copy, Style

# Set up logging
logger = logging.getLogger(__name__)

class InfoView(QWidget):
    # setup the info view for the right hand column.
    # This will show the image metadata once an image
    # is selected from the available thumbnails.
    #
    # requires: metadatatable.py
    # usage: infoview.show_metadata([FQPN of image])

    def __init__(self):
        super().__init__()
        logger.debug('entering InfoView')
        QDir.addSearchPath('icon', './assets/icons/')
        self.picture_path = ''
        iLayout = QVBoxLayout()     # info Layout but i couldn't resist iLayout because iPunny. :-D

        self.md_table = QTableWidget()
        # setup table for initial display.
        # this will be displayed until an image is clicked on.
        self.md_table.setColumnCount(2)
        self.md_table.setRowCount(1)
        self.md_table.setHorizontalHeaderLabels(['Image Info', 'Value'])
        self.md_table.setItem(0, 0,  QTableWidgetItem(' No Data '))
        self.md_table.setItem(0, 1,  QTableWidgetItem(' here yet.'))

        btn_layout = QHBoxLayout()
        logger.debug(f'Current app directory: {str(QDir.currentPath())}')
        self.copy_btn = QPushButton(icon=QIcon('icon:clipboard-copy.svg'), text='Copy', parent=self)
        self.copy_btn.setToolTip('Copy table to clipboard')
        self.copy_btn.setEnabled(True)
        self.copy_btn.setIconSize(QSize(30, 30))
        self.copy_btn.resize(self.copy_btn.sizeHint())
        self.copy_btn.clicked.connect(lambda: clipboard_copy(self.picture_path, self.md_table))

        self.wf_show = QPushButton(icon=QIcon('icon:workflow-eye.svg'), text='Show Workflow', parent=self)
        self.wf_show.setEnabled(False)        # until workflow works, disable it.
        self.wf_show.setToolTip('Still a work in Progress.')
        self.wf_show.setIconSize(QSize(30, 30))
        self.wf_show.resize(self.copy_btn.sizeHint())
        self.wf_show.clicked.connect(lambda: self.show_comfyui_workflow(self.img_path))
        btn_layout.addWidget(self.copy_btn)
        btn_layout.addWidget(self.wf_show)

        iLayout.addLayout(btn_layout)
        iLayout.addWidget(self.md_table)
        self.setLayout(iLayout)

    def show_metadata(self, image_path, width=300):
        """
        Gets and displays the metadata table for the given image.
        Args:
             (str) FQPN path of the image to read the SD metadata
             (int): Width of the second column in the metadata table.
                    Defaults to 300.
        """
        # get the metadata table info
        # it seems that all the programmatic ways to get the available
        # width for a column, make the data column too wide. at least
        # the ways I tried. So it's hard coded. C'est La PyQt
        self.picture_path = image_path
        logger.debug(f'show_metadata(): {self.picture_path=}')
        mtab = MetadataTable()
        new_mdtable = mtab.get_metadata_table(self.picture_path)
        layout = self.layout()

        if new_mdtable.rowCount() >1:
            self.md_table.clearContents()
            logger.debug('show_metadata(): New Metadata Table populated')
            logger.debug(f'{new_mdtable.rowCount() } rows in metadata Table')
            # col_width = 625
            new_mdtable.setWordWrap(True)
            new_mdtable.setColumnWidth(1, width)
            new_mdtable.resizeRowToContents(0)
            new_mdtable.resizeRowToContents(1)

            # Ah the Wonders of Qt. There is no refresh or update AFAIK
            # based on the research I've done. In order to properly
            # update the new table it has to be removed from the layout
            # and replaced. Odd. but this works even if it is ugly.
            # if there is a better way, please let me know.
            if self.md_table:
                layout.removeWidget(self.md_table)
                self.md_table.deleteLater()
                layout.update()

            logger.debug('show_metadata(): adding new Table and updating layout')
            self.md_table = new_mdtable
            layout.addWidget(self.md_table)
            layout.update()
        else:
            logger.debug('show_metadata(): (else) Metadata Table NOT populated')
            logger.warning('Metadata Table NOT populated. Possibly no info in image.')
            self.md_table.clearContents()
            self.md_table.setRowCount(1)
            self.md_table.setItem(0, 0,  QTableWidgetItem('No metadata '))
            msg = f'found in {Path(self.picture_path).name}'
            self.md_table.setItem(0, 1,  QTableWidgetItem(msg))
            Style.set_table_styling(self.md_table)
            self.md_table.resizeColumnToContents(1)
            logger.debug(f'InfoView: TABLE SIZING PROBS?')
            layout.addWidget(self.md_table)
            layout.update()

    def show_metadata_error(self):
        """
        Show an error when no metadata is found in the Image.
        only called by get_image_data()
        """
        # only shown if the image contains no Stable Diffusion metadata information
        logger.debug('info_view.show_metadata_error() no metadata found' )
        mbox = QMessageBox()
        mbox.setWindowIcon(QIcon('../assets/icons/Trash-Lines.svg'))
        mbox.setWindowTitle(Settings.APPNAME.value)

        # add an error message to the messagebox along with an Ok button
        # even if its not Ok. A "DOH!" button would be nice but too much work.
        mbox.setStyleSheet("font-size: 16px; font-weight: bold;")  # make it look pretty
        mbox.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        mbox.setText('No image metadata.')
        mbox.setInformativeText(f'No Metadata could be found in {self.picture_path}')

        ok_btn = mbox.addButton(QMessageBox.Ok)
        mbox.setDefaultButton(QMessageBox.Ok)
        ok_btn.clicked.connect(self.accept)         # maybe QMessageBox.AcceptRole
        # ret = mbox.exec()
        mbox.exec()

    # do I need anything else?
    # aside from comfyUI workflow block diagram
    #
    def show_comfyui_workflow(self, filepath):
        """
        eventually show the workflow associated with the selected image.
        However, this is still a work in progress.
        """
        # WORK IN PROGRESS
        # Opens a resizable dialog to display the ComfyUI workflow.
        # show_comfyui_workflow() needs a lot of work.
        # AUG 2025 - This will likely move to its own module or package.
        #
        # WOW from what I have found this seems like this is gonna be a LOT of work.
        logger.debug("show_comfyui_workflow(): Displaying ComfyUI workflow.")

    def get_current_workflow(self):
        # WORK IN PROGRESS
        # the eventual plan is to, if it exists,
        # Extract and return the current image's ComfyUI workflow.
        logger.debug("TBD: Extracting ComfyUI workflow.")
        # Placeholder for real workflow extraction logic
        # extract the ComfyUI workflow from metadata and
        # return it to show_comfyui_workflow()
        return "ComfyUI workflow data..."
