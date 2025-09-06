# MainWindow.py
#
# This module defines the MainWindow class, which serves as the primary
# interface for the LatentEye application.
#
# Author: Greg M.
# Date: November 2024

import logging
from pathlib import Path

from PyQt6.QtCore import Qt, QDir, pyqtSignal
from PyQt6.QtWidgets import (QApplication, QComboBox, QLabel, QMainWindow,
                             QMessageBox, QVBoxLayout, QSplitter, QWidget)
from PyQt6.QtGui import QAction, QIcon, QKeySequence

from .file_tree import FileTreeView
from .info_view import InfoView
from .latent_tools import Settings, show_error_box
from .thumbnail_view import ThumbnailView


logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    and center thumbnail view.
    """
    sortMethodChanged = pyqtSignal(str)
    def __init__(self):
        super().__init__()

        logger.debug('Starting MainWindow')
        QDir.addSearchPath('logo', str(Path(__file__).parent / '../assets'))
        QDir.addSearchPath('icon', str(Path(__file__).parent / '../assets/icons/darkModeIcons'))

        self.setWindowTitle(Settings.APPNAME.value)
        self.setWindowIcon(QIcon('logo:logo256.png'))
        self.setGeometry(100, 100, 1200, 800)
        self.center_window()

        # Init the menu and toolbars
        self.init_menu_bar()
        self.init_toolbar()

        # the main layout.
        main_layout = QVBoxLayout()
        main_widget = QWidget()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        logger.debug('Setting up qsplitter')
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.filetree_view = FileTreeView()
        self.thumbnail_view = ThumbnailView()
        self.info_view = InfoView()

        self.splitter.addWidget(self.filetree_view)
        self.splitter.addWidget(self.thumbnail_view)
        self.splitter.addWidget(self.info_view)

        # Optional: Set minimum sizes to prevent views from becoming too small
        self.filetree_view.setMinimumWidth(50)
        self.thumbnail_view.setMinimumWidth(400)
        self.info_view.setMinimumWidth(120)
        main_layout.addWidget(self.splitter, stretch=1)

        # Connect file tree selection to updating the thumbnails
        self.filetree_view.directoryChosen.connect(self.get_selected_directory)
        self.thumbnail_view.thumbnail_selected.connect(self.get_thumbnail_metadata)
        self.current_directory = ''         # used later by get_selected_directory and on_sort
        self.setCentralWidget(self.splitter)
        logger.debug('past setCentralWidget().')

    def center_window(self):
        """
        Center the app window in center of the desktop of
        the current monitor.
        """
        # get the geometry of the Main Window
        # Then the reported screen resolution and the center point
        # of the current monitor since there could be more then one monitor.
        app_frame = self.frameGeometry()
        ctr_point = self.screen().availableGeometry().center()
        # Set the center of the the app_frame rectangle to the center of
        # the screen & reset the app_frame position so it's centered
        app_frame.moveCenter(ctr_point)
        self.move(app_frame.topLeft())

    def init_menu_bar(self):
        logger.debug('Creating menu bar')
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu('File')

        quit_action = QAction('Quit', self)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        help_menu = menu_bar.addMenu('Help')
        docs_action = QAction('Docs', self)
        docs_action.setShortcut(QKeySequence.StandardKey.HelpContents)
        docs_action.triggered.connect(self.helpMe)
        help_menu.addAction(docs_action)
        help_menu.addSeparator()
        about_action = QAction('&About', self)
        about_action.triggered.connect(self.about_box)
        help_menu.addAction(about_action)
        logger.debug('exiting init menu bar')

    def init_toolbar(self):
        """
        Setup toolbar with sort dropdown, and buttons for toggling
        right and left panels.
        """
        logger.debug('Creating Main Toolbar')
        toolbar = self.addToolBar('Main Toolbar')
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonFollowStyle)

        # Button for refreshing the currently selected directory
        refresh_thumbnails_action = QAction(QIcon('icon:refresh.svg'), 'Refresh Thumbnails', self)
        refresh_thumbnails_action.triggered.connect(self.on_refresh_thumbnails)
        toolbar.addAction(refresh_thumbnails_action)

        # Sorting dropdown
        sort_lbl = QLabel('Sort: ')
        toolbar.addWidget(sort_lbl)
        self.sort_dropdown = QComboBox()
        self.sort_dropdown.addItems(['Name', 'Last modified date', 'File Size', 'Extension', 'Default'])
        self.sort_dropdown.activated.connect(self.on_sort_changed)
        toolbar.addWidget(self.sort_dropdown)

        # Buttons for toggling visibility of the side panels
        toggle_filespanel_action = QAction(QIcon('icon:pane-open-left-filled.svg'), 'Toggle Files Panel', self)
        toggle_filespanel_action.triggered.connect(self.toggle_files_panel)
        toolbar.addAction(toggle_filespanel_action)

        toggle_metapanel_action = QAction(QIcon('icon:pane-close-right-filled.svg'), 'Toggle Metadata Panel', self)
        toggle_metapanel_action.triggered.connect(self.toggle_metadata_panel)
        toolbar.addAction(toggle_metapanel_action)

        # Display text labels with icons
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        logger.debug('exiting toolbar')

    def on_refresh_thumbnails(self):
        logger.debug('entering on_refresh_thumbnails()')
        sort_method = self.sort_dropdown.currentText()
        self.thumbnail_view.sort_image_files(self.current_directory, sort_method)

    def on_sort_changed(self, index):
        """handles sort combobox selection change."""
        logger.debug('entering on_sort_changed()')

        sort_method = self.sort_dropdown.itemText(index)   # get the text of the current index
        curr_text = self.sort_dropdown.currentText()
        curr_idx = self.sort_dropdown.currentIndex()
        self.sortMethodChanged.connect(lambda: self.thumbnail_view.sort_image_files(self.current_directory, curr_text))
        logger.debug(f"main:Sort method changed to: {sort_method}")
        self.sortMethodChanged.emit(sort_method)

    def toggle_files_panel(self):
        """
        does what it says. its not a unicorn farting rainbows
        """
        logger.debug('button clicked. collapsing left')
        sizes = self.splitter.sizes()
        if sizes[0] > 0:
            self.splitter.setSizes([0, sizes[1] + sizes[0], sizes[2]])  # Collapse left
        else:
            self.splitter.setSizes([300, sizes[1] - 300, sizes[2]])     # Restore left size

    def toggle_metadata_panel(self):
        """
        does what it says. its not the secret of flying pigs.
        """
        logger.debug('button clicked. collapsing right')
        sizes = self.splitter.sizes()
        if sizes[2] > 0:
            self.splitter.setSizes([sizes[0], sizes[1] + sizes[2], 0])  # Collapse right
        else:
            self.splitter.setSizes([sizes[0], sizes[1] - 300, 300])     # Restore right size

    def abuseMe(self):
        """ just a empty place holder for not implemented yet """
        # also used as method to use for POC with menu and toolbar action testing.
        show_error_box("I'm working on it, don't be so <i>impatient<i>.")

    def helpMe(self):
        """ need professional help to get things straight """
    # TODO: FV - complete the helpMe function
        show_error_box(msg, 'info')
    # The idea is to open a page on the repo github pages that has the help info

    def about_box(self):
        """ Its all About me in a box. """
        QMessageBox.about(self,'About LatentEye',
                          'LatentEye: Seeing the hidden metadata in AI generated images.<br><br> '
                          'In Latent Space only the AI hears the screams.<br><br>'
                          'Thanks to <a href="https://www.svgrepo.com" target="_blank">SVG Repo</a> for the icons used in LatentEye.'
                          f'<p style="font-size: small;">version {Settings.VERSION}</p>')

    def get_selected_directory(self, selected_dir):
        """
        Based on directory selected in file tree, updates thumbnails.
        Args: string - path of the selected directory
        """
        logger.debug(f'get_selected_directory(): {selected_dir}')
        # Everything I read recommended doing it this way to prevent
        # the dropdown showing one thing and the FileTree another
        curr_dir = selected_dir
        self.current_directory = selected_dir
        curr_sort = self.sort_dropdown.currentText()
        logger.debug('get_selected_directory(): calling load_thumbnails')
        self.thumbnail_view.sort_image_files(self.current_directory, curr_sort)

    def get_thumbnail_metadata(self, selected_tn):
        """
        shows Stable Diffusion metadata for selected image
        in right side of MainWindow.
        """
        logger.debug(f'get_thumbnail_metadata(): {selected_tn}')
        self.info_view.show_metadata(selected_tn)

    def closeEvent(self, event):
        """
        Ensures all windows are closed when the main window is closed.
        """
        QApplication.closeAllWindows()
        super().closeEvent(event)
        event.accept()
