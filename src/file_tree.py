# file tree view
# This shows the directory tree with the user directory selected and the parents visible.
# The goal is to look and feel __similar__ to a regualr file browser that would be found on
# all major platforms.
# this should emit a a directory path to thumbnail_view.
#

import sys
import logging
from pathlib import Path

from PyQt6.QtWidgets import QTreeView, QVBoxLayout, QWidget, QLabel, QComboBox
from PyQt6.QtGui import QFileSystemModel, QColor, QFont, QIcon
from PyQt6.QtCore import Qt, QDir, QStorageInfo, pyqtSignal, QFileSystemWatcher

# # Set up logging
logger = logging.getLogger(__name__)

class CustomFileSystemModel(QFileSystemModel):
    """
    subclass QFileSystemModel and override its data() method to customize how the
    directories are displayed. Check if a directory contains any files that match the
    name filters that are in place and change the color of the directory and change
    the color of the icon and directory name.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        # Set the search path for icons
        # imho, pathlib.Path doesn't make this path easier to read and it has to be wrappred in str.
        # this allegedly is progress... smh.
        QDir.addSearchPath('icon', str(Path(__file__).parent.parent / 'assets/icons/darkModeIcons'))

    def data(self, index, role):
        """
        Override the data method to customize the appearance of directories and files.
        Args:
            index (QModelIndex): The index of the item in the model.
            role (Qt.ItemDataRole): The role for which data is requested.
        Returns:
            The data for the specified role.
        """

        # if item is a directory
        if self.isDir(index):
            dir_path = self.filePath(index)
            directory = QDir(dir_path)
            # and contains filter matching files
            contains_matching_files = bool(directory.entryList(
                                      self.nameFilters(), QDir.Filter.Files ))

            # By default, QFileSystemModel uses native icons
            # for directories and files. To override these, you must
            # supply your own icons or use QIcon Objecta.
            if role == Qt.ItemDataRole.DecorationRole:
                if contains_matching_files:
                    return QIcon('icon:folder-green.svg')
                else:
                    return QIcon('icon:folder-gray.svg')

            # Change the color of the directory name based as defined
            # by QFileSystemModel.SetNameFilters().
            # colors names are listed at
            # https://doc.qt.io/qt-6/qcolorconstants.html
            # for reference: Cyan = #00FFFF | darkGray = #808080
            # #36bb17 = rgb 54, 187,19
            if role == Qt.ItemDataRole.ForegroundRole:
                return (QColor(54, 187, 19) if contains_matching_files
                    else QColor(Qt.GlobalColor.gray))

            # and make the matching items bold
            if role == Qt.ItemDataRole.FontRole and contains_matching_files:
                return QFont('', weight=QFont.Weight.Bold)
        # Otherwise...
        return super().data(index, role)

class FileTreeView(QWidget):
    """
    FileTreeView provides a tree view for browsing the file system. It includes
    drive selection, directory expansion, and signals for the directory and/or 
    the file selected.
    """
    directoryChosen = pyqtSignal(str)
    fileSelected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Set up the file system model, and configure the UI.
        # the UI components.
        logger.debug('Entering FileTreeView')

        # Create a file system model that allow the entire FS.
        # and and looks like something we are all used to.
        self.model = CustomFileSystemModel()
        self.model.setRootPath('')
        logger.debug('FileTreeView: Root path set to the filesystem root.')

        # graphics filter might be a part of user settings.
        graphics_filters = ['*.png', '*.jpg', '*.jpeg', '*.webp']
        self.model.setNameFilters(graphics_filters)
        self.model.setNameFilterDisables(False)

        # only show directories aka folders.
        # or not. I'm not sure I that I like it.
        self.model.setFilter( QDir.Filter.NoDotAndDotDot | QDir.Filter.AllEntries | QDir.Filter.AllDirs )
        # self.model.setFilter(QDir.Filter.AllDirs | QDir.Filter.NoDotAndDotDot | QDir.Filter.AllEntries | QDir.Filter.System)
        logger.debug(f'FileTreeView: Applied graphics filters: {graphics_filters}')
        self.tree = QTreeView()
        self.tree.setModel(self.model)
        home_index = self.model.index(QDir.homePath())
        self.tree.setRootIndex(self.model.index(QDir.rootPath()))

        # Expand the user's home dir and parents
        current_index = home_index
        while current_index.isValid():
            self.tree.expand(current_index)
            current_index = current_index.parent()

        self.tree.setSortingEnabled(True)
        self.tree.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self.tree.setAnimated(True)
        self.tree.setIndentation(20)

        # Adjust column widths and remove unwanted columns
        # remove date, size, and type
        self.tree.setColumnHidden(1, True)
        self.tree.setColumnHidden(2, True)
        self.tree.setColumnHidden(3, True)

        # slot in click event. why not just call it connect? maybe connect event?
        # signal/slot only seems to be used in the Qt/PyQt Docs.
        self.tree.clicked.connect(self.onFileSelected)

        # Dropdown for drives/volumes
        self.driveSelector = QComboBox()
        self.populateDrives()
        self.driveSelector.currentTextChanged.connect(self.changeDrive)

        # The simple layout
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Select Drive/Volume:"))
        layout.addWidget(self.driveSelector)
        layout.addWidget(self.tree)
        self.setLayout(layout)

    def populateDrives(self):
        """
        Populate the dropdown with available drives or volumes using QStorageInfo.
        Exclude platform dependant system vcolumes or inaccesable storage.
        """
        drives = []
        # drives that I don't think should be shown
        mac_verboten = {'TimeMachine', 'System','Libary'}
        linux_verboten = {'proc', 'sys', 'run', 'etc', 'sbin', 'bin'}
        windows_verboten = {'$Recycle.Bin', 'System Volume Information'}

        for storage in QStorageInfo.mountedVolumes():
            if storage.isValid() and storage.isReady:
                root_path = storage.rootPath()
                volume_name = storage.displayName() or root_path
                logger.info(f'Found storage device: {volume_name}')

            if sys.platform == 'darwin':
                # Exclude Time Machine volumes on macOS
                # if mac_verboten in volume_name:
                if volume_name in mac_verboten:
                    continue

            if sys.platform == 'linux':
                noslash_name = volume_name[1:] if volume_name.startswith('/') else volume_name
                if noslash_name in linux_verboten or root_path == '/':
                    continue

            if sys.platform == 'win32':
                if volume_name in windows_verboten:
                    continue

            # Exclude inaccessible volumes or ones with no root path
            if not root_path or not storage.isReady():
                continue

            # Add the volume name for display, and the root path for navigation
            drives.append((volume_name, root_path))

        # Finally, populate the combo box
        for name, path in drives:
            self.driveSelector.addItem(name, path)

    def changeDrive(self, drive_name):
        """
        Change the root index of the file tree to the selected drive/volume.
        Args: string - name of the selected volume/drive
        """
        # Get the root path from the combo box
        drive_path = self.driveSelector.currentData()
        if drive_path:
            logger.debug(f'Selected drive: {drive_name}, Path: {drive_path}')
            self.model.setRootPath(drive_path)
            new_index = self.model.index(drive_path)
            self.tree.setRootIndex(new_index)

        if new_index.isValid():
            # Update model's root path
            new_index = self.model.setRootPath(drive_path)
            self.tree.setRootIndex(new_index)

    def onFileSelected(self, index):
        """
        Handle the event when a file or directory is selected in the tree view.
        Emits: the selected file or directory.
        Args: (QModelIndex) - index of the selected item in the model.
        """
        # Get the file path from the selected index
        fpname = self.model.filePath(index)
        logger.debug(f'onFileSelected(): Item clicked: {fpname}')
        if Path(fpname).is_file():
            self.fileSelected.emit(str(fpname))
            self.directoryChosen.emit(str(Path(fpname).parent))
            logger.debug(f'onFileSelected emitting File selected(fqfn): {fpname}')

        elif Path(fpname).is_dir():
            logger.debug(f'onFileSelected(): directory selected: {fpname}')
            self.fileSelected.emit(None)
            self.directoryChosen.emit(fpname)
#
