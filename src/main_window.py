# MainWindow.py
#
# This module defines the MainWindow class, which serves as the primary
# interface for the LatentEye application.
#
# Author: Greg M.
# Date: November 2024

import logging
from pathlib import Path

from PyQt6.QtWidgets import (QApplication, QComboBox, QLabel, QMainWindow,
                             QMessageBox, QVBoxLayout, QSplitter, QWidget )
from PyQt6.QtCore import Qt, QDir
from PyQt6.QtGui import QAction, QIcon, QKeySequence

from .file_tree import FileTreeView
from .info_view import InfoView
from .latent_tools import Settings, show_error_box
from .thumbnail_view import ThumbnailView

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """
    LatentEye main application window. Everything starts from here.
    menu bar, toolbar, window splitters with file tree, Metadata view
    and center thumbnail view.
    """


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
        # self.splitter.setStyleSheet(splitter_style)
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
        self.setCentralWidget(self.splitter)
        logger.debug('past setCentralWidget().')

    def center_window(self):
        """
        Center the app window in center of the desktop of
        the current monitor.
        """
        # get the geometry of the Main Window
        app_frame = self.frameGeometry()
        # Then the reported screen resolution and the center point
        # of the current monitor. There could be more then one monitor.
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

    # TODO: FV - Need to add functionality to the Docs
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

        # Sorting dropdown - still a work in progress
        sort_lbl = QLabel('Sort: ')
        toolbar.addWidget(sort_lbl)
        self.sort_dropdown = QComboBox()
        self.sort_dropdown.addItems(['Work in Progress', 'Default', 'Name', 'Creation Date', 'File Size'])
        self.sort_dropdown.currentIndexChanged.connect(self.on_sort_changed)
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
        logger.debug('exiting toobar')

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
        show_error_box("I'm working on it, don't be so <i>impatient<i>.")

    def helpMe(self):
        """ need professional help to get things straight """
    # TODO: FV - complete the helpme function
        msg = 'Docs haven\'t been integrated here yetHowever they are available on' + \
               'Github at <a href="https://github.com/AnotherWorkingNerd/LatentEye" target="_blank">LatentEye Docs</a>'
        show_error_box(msg, 'info')

    def about_box(self):
        """ Its all About me in a box. """
        QMessageBox.about(self,'About LatentEye',
                          'LatentEye: Seeing the hidden metadata in AI generated images.<br><br> '
                          'In Latent Space only the AI hears the screams.<br><br>'
                          'Thanks to <a href="https://www.svgrepo.com" target="_blank">SVG Repo</a> for the icons used in LatentEye.')

    def get_selected_directory(self, selected_dir):
        """
        Based on directory selected in file tree, updates thumbnails
        Args: string - path of the selected directory
        """
        logger.debug(f'get_selected_directory(): {selected_dir}')
        # Everything I read recommended doing it this way to prevent
        # the dropdown showing one thing and the FileTree another
        curr_dir = selected_dir
        logger.debug('get_selected_directory(): calling load_thumbnails')
        self.thumbnail_view.load_thumbnails(curr_dir)

    def get_thumbnail_metadata(self, selected_tn):
        """
        shows Stable Diffusion metadata for selected image
        in right side of MainWindow.
        """
        logger.debug(f'get_thumbnail_metadata(): {selected_tn}')
        self.info_view.show_metadata(selected_tn)

    def on_sort_changed(self):
        """
        NEEDS WORK:
        Get the selected sorting criterion
        """
        logger.debug('entering on_sort_changed()')
        sort_by = self.sort_dropdown.currentText().lower().replace(' ', '_')
        sorted_thumbnails = self.thumbnail_view.sort_thumbnails(self.thumbnail_view.current_thumbnails, sort_by)
        self.thumbnail_view.load_thumbnails(sorted_thumbnails)
        logger.debug('exiting')

    def sort_thumbnails(self, criterion):
        """
        NEEDS WORK:
        Sorts thumbnails by the given criterion.
        """
        logger.debug('sort_thumbnails')
        image_paths = self.thumbnail_view.get_image_paths()

        if criterion == 'name':
            image_paths.sort()  # Sort alphabetically
        elif criterion == 'creation date':
            # image_paths.sort(key=lambda path: os.path.getctime(path))
            # Well I honestly don't feel pathlib makes this easier to
            # read... but gotta keep up with the times.
            image_paths.sort(key=lambda path: Path(path).stat().st_ctime)
        elif criterion == 'file size':
            image_paths.sort(key=lambda path: Path(path).stat().st_size)
        logger.debug('Sort_thumbnails() - thumbnail_view() call')
        self.thumbnail_view.load_thumbnails(image_paths)

    def closeEvent(self, event):
        """
        Ensures all windows are closed when the main window is closed.
        """

        QApplication.closeAllWindows()
        super().closeEvent(event)
        event.accept()
