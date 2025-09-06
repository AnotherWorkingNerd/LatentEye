# eye_sight.py
# Greg W. Moore - Dec 2024
#
# Display a full size image. Used by the thumbnail double click in
# the thumbnail viewer. This includes a menu and toolbar.
#
# Resizable image viewer window designed to work separate from MainWindow.
# Provides ability to zoom in on image.
# Closes when main app closes if this window is still open
# Metadata for current image can be displayed in a dialog box
# Metadata can be copied to the system clipboard.
#
# Usage: pass in tooltip from thumbnail which is the fully qualified filename.
# so.. something like es = EyeSight(filename)

import logging
# import platform
import sys
from pathlib import Path

from PyQt6.QtCore import Qt, QDir, QFileInfo, QPoint
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QScrollArea,
                             QWidget, QMenuBar, QToolBar, QMessageBox, QDialog,
                             QDialogButtonBox, QPushButton, QLabel)

from PyQt6.QtGui import QPixmap, QPalette, QAction, QIcon, QKeySequence, QWheelEvent
from .metadatatable import MetadataTable
from .latent_tools import Settings, clipboard_copy

logger = logging.getLogger(__name__)

class EyeSight(QMainWindow):
    """
    EyeSight: a vision of the selected thumbnail.
    It will appear as a non-modal window.
    """
    # image path = fqpn of image
    def __init__(self, image_path):
        """
        Create EyeSight with the given image path.
        Args: (str) - FQPN of the image to see.
        """

        super().__init__()

        logger.debug('Opening EyeSight')
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        QDir.addSearchPath('icon', str(Path(__file__).parent / '../assets/icons/darkModeIcons'))
        self.picture_path = image_path
        logger.debug(f'__init__(): picture_path = {self.picture_path} ')
        _title = "EyeSight - " + image_path
        self.setWindowTitle(f'{_title}')
        self.setMinimumSize(1024, 1024)

        logger.debug('__init__(): set scroll area')
        #Scroll Area Properties
        self.pic_scroll = QScrollArea(self)
        self.pic_scroll.setBackgroundRole(QPalette.ColorRole.Dark)
        self.pic_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.pic_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.pic_scroll.setWidgetResizable(True)
        self.setCentralWidget(self.pic_scroll)
        es_layout = QWidget(self)
        layout = QVBoxLayout(es_layout)
        # layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.pic_scroll)
        self.setCentralWidget(es_layout)

        # default image scale factor.
        self.scale_factor = 1.0

        # Create the Image Label
        self.pixmap = None
        # self.scale_factor
        self.lbl_pict = QLabel(self)
        self.lbl_pict.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pic_scroll.setWidget(self.lbl_pict)
        self.pic_scroll.setWidgetResizable(True)

        # setup the menubar and toolbar
        self.init_menubar()
        self.init_toolbar()

        # Load and display the image
        self.load_image(self.picture_path)

    def init_menubar(self):
        """
        Create the the menubar for EyeSight
        """
        # add a simple menu bar
        # mainly needed for View menu.
        pw_menu = QMenuBar(self)

        logger.debug("init_menubar(): Adding menu to main window.")
        file_menu = pw_menu.addMenu("File")
        quit_action = QAction("Close Window", self)
        quit_action.triggered.connect(self.closeEvent)
        file_menu.addAction(quit_action)

        view_menu = pw_menu.addMenu("View")
        # add tool bar visibility toggle
        tb_action = QAction("Show Toolbar", self, checkable=True)
        tb_action.setChecked(True)
        tb_action.triggered.connect(self.something)
        view_menu.addAction(tb_action)

        # add metadata dialog
        md_action = QAction("Show image metadata", self)
        md_action.triggered.connect(lambda: self.get_image_data(self.picture_path))
        view_menu.addAction(md_action)
        pw_menu.show()

        logger.debug('leaving init_menubar()')

    def init_toolbar(self):
        """
        Create the the toolbar for EyeSight along
        with the associated buttons and actions
        """
        # tb_background = '#f0f0f0'    # nearest to css color: Gainsboro (#DCDCDC)
        # tb_background = '#616161'    # closest matching CSS color: DimGrey #696969
        # tb_background = '#37474F'    # dark slate gray with a bluish tint. No matching CSS Color.
        tb_background = '#37474F'      # nice Gray'
        # without 'border:none' nothing changes. another Qt Quirk?
        toolbar_style = f'QToolBar {{ background: {tb_background}; spacing: 2px; border: none}}'
        self.pw_toolbar = QToolBar('PW Toolbar', self)
        logger.debug("init_toolbar(): Toolbar created.")
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.pw_toolbar)
        logger.debug("init_toolbar(): Toolbar added to main window.")
        self.pw_toolbar.setVisible(True)
        logger.debug("init_toolbar(): Toolbar set visible")
        # TB background color and spacing between items in the tool bar
        self.pw_toolbar.setStyleSheet(toolbar_style)
        # follow system style regarding display text labels with icons
        self.pw_toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonFollowStyle)

        # Key_Meta On macOS, this corresponds to the Control keys.
        # On Windows keyboards, this key is mapped to the Windows key.
        # Key_Control On macOS, this corresponds to the Command keys.
        # as per https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtcore/qt.html#Key
        # https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtgui/qkeysequence.html#standard-shortcuts

        self.fit_win = QAction(QIcon('icon:toggle-off.svg'), 'Fit To Window', self)
        std_key  = QKeySequence.StandardKey.FullScreen
        self.fit_win.setShortcut(QKeySequence(std_key))
        self.fit_to_window()
        self.fit_win.setCheckable(True)
        self.fit_win.triggered.connect(self.fit_to_window)
        # do I need a status tip... maybe?!?
        # fit_win.setStatusTip("Fit To Window Button")

        self.pw_toolbar.addSeparator()
        self.image_zoom_in_action = QAction(QIcon('icon:magnifying-glass-plus.svg'), 'Zoom In', self)
        std_key  = QKeySequence.StandardKey.ZoomIn
        self.image_zoom_in_action.setShortcut(std_key)
        self.image_zoom_in_action.triggered.connect(self.zoom_in)

        self.image_zoom_out_action = QAction(QIcon('icon:magnifying-glass-minus.svg'), 'Zoom Out', self)
        fs_key  = QKeySequence.StandardKey.ZoomOut
        self.image_zoom_out_action.setShortcut(std_key)
        self.image_zoom_out_action.triggered.connect(self.zoom_out)

        image_zoom_reset_action = QAction(QIcon('icon:actual-size.svg'), 'Reset Zoom', self)
        # fs_key  = QKeySequence.StandardKey.
        image_zoom_reset_action.setShortcut('Ctrl+R')
        image_zoom_reset_action.triggered.connect(self.normal_size)

        self.pw_toolbar.addSeparator()
        meta_action = QAction(QIcon('icon:metadata-eye.svg'), 'Metadata', self)
        meta_action.setShortcut('Ctrl+E')   # E for eye? not sure what is best.
        meta_action.triggered.connect(lambda: self.get_image_data(self.picture_path))

        self.pw_toolbar.addSeparator()
        close_action_icon = QIcon('icon:x-circle.svg')
        close_action = QAction(close_action_icon, 'Close Image', self)
        fs_key  = QKeySequence.StandardKey.Close
        close_action.setShortcut(fs_key)
        close_action.triggered.connect(self.close)

        self.pw_toolbar.addAction(self.image_zoom_in_action)
        self.pw_toolbar.addAction(self.image_zoom_out_action)
        self.pw_toolbar.addAction(image_zoom_reset_action)
        self.pw_toolbar.addAction(meta_action)
        self.pw_toolbar.addAction(self.fit_win)
        self.pw_toolbar.addAction(close_action)
        logger.debug('init_toolbar(): Toolbar actions added')

        self.pw_toolbar.show()
        logger.debug('init_toolbar(): Toolbar shown. Leaving init_toolbar')

    def something(self):
        # this is used for actions that are still a WIP.
        print('Still under development.')

    def get_image_data(self, file_path):
        """
        get the image data by calling metadataTable
        if table contains data then pass the table to show_metadata_dialog()
        if table does not contain data then show a waning messagebox with
        show_metadata_error()

        Args: (str) - FQPN of the image.
        """

        # get the SD data embedded in the image
        # mdt is, of course, Meta. Data. Table.
        mdt = MetadataTable()
        md_table = mdt.get_metadata_table(file_path)
        if md_table:
            logger.debug('get_image_data(): MDT populated')
            self.show_metadata_dialog(md_table)
        else:
            logger.debug('get_image_data(): No image metadata')
            self.show_metadata_error()

    def show_metadata_dialog(self, metadata_table):
        """
        display a dialog box that contains a table
        with the image metadata info. The table is
        styled using the QSS `styles_string` defined
        in metadata_view.py

        Args: metadata table -
                a QTableWidget with the image metadata
        """

        logger.debug('entering show_metadata_dialog()')
        self.populated_table = metadata_table
        dlg = QDialog(self)
        dlg.setWindowTitle('Image Metadata')
        dlg.setGeometry(200, 300, 600, 450)
        dlg.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        self.copy_btn = QPushButton("Copy to Clipboard")
        self.bbox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        self.bbox.addButton(self.copy_btn, QDialogButtonBox.ButtonRole.ActionRole)
        self.bbox.accepted.connect(dlg.accept)
        self.copy_btn.clicked.connect(lambda: clipboard_copy(self.populated_table))

        col_width = 625
        self.populated_table.setWordWrap(True)
        self.populated_table.horizontalHeader().SizeAdjustPolicy.AdjustToContents
        self.populated_table.setColumnWidth(1, col_width)
        self.populated_table.resizeRowToContents(0)
        self.populated_table.resizeRowToContents(1)

        dlg_layout = QVBoxLayout()
        logger.debug('show_metadata_dialog(): initialized dlg layout')
        dlg_layout.addWidget(self.populated_table)
        dlg_layout.addWidget(self.bbox)
        dlg.setLayout(dlg_layout)
        logger.debug('show_metadata_dialog(): dlg.exec show_metadata_dialog()')
        ctr = self.screen().availableGeometry().center()
        dlg.move(ctr)
        dlg.show()      # I want this Non-Modal. using .exec() its modal.

    def show_metadata_error(self):
        """
        Display a custom error message box if no Stable Diffusion
        metadata is found in the image.

        Only called by get_image_data()
        """
        # maybe this is more informative or more specific?
        logger.debug('entering show_metadata_error()')
        finfo = QFileInfo(self.picture_path)
        mbox = QMessageBox(self)
        mbox.setWindowTitle(Settings.APPNAME)
        mbox.setIcon(QMessageBox.Icon.Warning)

        # mbox.setStyleSheet("font-size: 16px; font-weight: bold;")
        # looks like resizing a QMessagebox is very hacky and the cleanest requires something like:
        # msg.setStyleSheet("QLabel {min-width: 300px; min-height: 200px;}")
        # only use the filename not the entire path.
        _err_msg = f"<p style='text-align: center;'>No SD Metadata could be found in image:<br><em> {finfo.fileName()}</em></p>"
        mbox.setText("<p style='text-align: center;'><strong>No Metadata found.</p>")
        mbox.setInformativeText(_err_msg)
        mbox.setStandardButtons(QMessageBox.StandardButton.Ok)
        mbox.setDefaultButton(QMessageBox.StandardButton.Ok)
        mbox.exec()

    def toggle_toolbar(self, state):
        """ Toggle visibility of the Toolbar """
        if state:
            # self.pw_toolbar.show()
            self.pw_toolbar.toggleViewAction().setChecked(True)
            self.pw_toolbar.toggleViewAction().trigger()
        else:
            self.pw_toolbar.toggleViewAction().setChecked(False)
            self.pw_toolbar.toggleViewAction().trigger()
            # self.pw_toolbar.hide()

    # zoomy zoom zoom.
    def zoom_in(self):
        self.scale_image(1.25)

    def zoom_out(self):
        self.scale_image(0.8)

    def normal_size(self):
        # Reset image to original size
        if not self.pixmap:
            return

        self.scale_image(1.25)
        self.lbl_pict.setPixmap(self.pixmap.scaled(self.pixmap.size(),
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation
                        ))
        self.lbl_pict.adjustSize()

    def fit_to_window(self):
        """ Toggle the "Fit to Window" mode, adjusting the image display accordingly. """
        if not self.pixmap:
            return

        fit_win_checked = self.fit_win.isChecked()
        if fit_win_checked:
            self.fit_win.setIcon(QIcon('icon:toggle-on.svg'))
            logger.debug('Fit to Window checked')
            self.pw_toolbar.activateWindow()
            viewport_size = self.pic_scroll.viewport().size()
            scaled = self.pixmap.scaled(viewport_size,
                                Qt.AspectRatioMode.KeepAspectRatio,
                                Qt.TransformationMode.SmoothTransformation
                            )
            self.lbl_pict.setPixmap(scaled)
            self.lbl_pict.resize(scaled.size())
            # Disable zoom actions while fit mode is toggled
            self.image_zoom_in_action.setEnabled(False)
            self.image_zoom_out_action.setEnabled(False)

        if not fit_win_checked:
            self.fit_win.setIcon(QIcon('icon:toggle-off.svg'))
            logger.debug('Fit to Window unchecked')
            self.normal_size()
            self.image_zoom_in_action.setEnabled(True)
            self.image_zoom_out_action.setEnabled(True)

    def scale_image(self, factor):
        """
        Scale the image based on zoom factor, maintaining aspect ratio and updating scrollbars.
        This should only be called once per zoom action (button click or wheel event).
        Enables/disables zoom actions at max/min zoom.
        """
        if not self.pixmap:
            return

        # Update scale factor, clamp to allowed range
        max_scale = 6.0
        min_scale = 0.333
        self.scale_factor *= factor
        if self.scale_factor > max_scale:
            self.scale_factor = max_scale
        if self.scale_factor < min_scale:
            self.scale_factor = min_scale

        logger.debug(f'scale_image: factor: {factor} | scale factor {self.scale_factor}')

        new_size = self.scale_factor * self.pixmap.size()
        scaled = self.pixmap.scaled(
            new_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.lbl_pict.setPixmap(scaled)
        self.lbl_pict.resize(scaled.size())
        self.adjust_scrollbar(self.pic_scroll.horizontalScrollBar(), factor)
        self.adjust_scrollbar(self.pic_scroll.verticalScrollBar(), factor)

        # Enable/disable zoom actions at limits
        self.image_zoom_in_action.setEnabled(self.scale_factor < max_scale)
        self.image_zoom_out_action.setEnabled(self.scale_factor > min_scale)

    def adjust_scrollbar(self, scrollbar, factor):
        # Center the view on zoom
        scrollbar.setValue(int(factor * scrollbar.value() + ((factor - 1) * scrollbar.pageStep() / 2)))

    def load_image(self, img_file):
        """
        Loads and displays an image. shows error message if unable to load
        :param file_path: String. Fully qualified path to the image file.

        called by Eyesight.__init__()
        """
        logger.debug('start load_image()')
        try:
            self.pixmap = QPixmap(img_file)
            if self.pixmap.isNull():
                raise ValueError(f'Unable to Load {img_file}')
        except Exception as ex:
            logger.debug('Load_image() raised Exception. No SD metadata in image.')
            self.lbl_pict.setText("OOPS....")

            mbox = QMessageBox(self)
            mbox.setIcon(QMessageBox.Icon.Critical)
            mbox.setWindowTitle("I/O Error")
            mbox.setText(f"Error loading image:\n{img_file}")
            mbox.setInformativeText(f"Details:\n{ex}")
            mbox.setStandardButtons(QMessageBox.StandardButton.Ok)
            mbox.exec()
            # Do I want a close here?
            self.close()
        else:
            logger.debug('load_image(): else of try..except ')
            self.lbl_pict.setPixmap(
                self.pixmap.scaled(
                    self.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        logger.debug('exiting load_image()')

    def adjust_scrollbar(self, scrollBar, factor):
        """
        Adjust the scrollbar position based on the zoom level
        Args: what QScrollBar to adjust, zoom factor
        """
        scrollBar.setValue(int(factor * scrollBar.value()
                               + ((factor - 1) * scrollBar.pageStep() / 2)))

    def wheelEvent(self, event: QWheelEvent):
        """ Handles QWheelEvent - zooming with Alt/Opt + Mouse Wheel """
        delta = event.angleDelta().y()
        if self._is_zoom_modifier(event.modifiers()):
            if delta > 0:
                self.zoom_in()
            elif delta < 0:
                self.zoom_out()
        else:
            super().wheelEvent(event)

    def _is_zoom_modifier(self, modifiers):
        """ so many keys.... alt, option, windows, meta, control, command"""
        if sys.platform == 'darwin':
            return modifiers & Qt.KeyboardModifier.AltModifier  # Option key
        else:   # if its not Mac, its either Linux or Windows.
            return modifiers & Qt.KeyboardModifier.AltModifier

    def resizeEvent(self, event):
        if self.fit_win.isChecked():
            self.fit_to_window()
        super().resizeEvent(event)

    def closeEvent(self, event):
        """
        Explicitly delete the pixmap to free memory
        and Cleanup resources when the window is closed.
        when close even triggered.
        """
        self.pixmap = None
        self.lbl_pict.clear()
        self.deleteLater()
        super().closeEvent(event)
