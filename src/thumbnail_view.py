# Thumbnail display
#  Date: 2024 Nov
#
#   This code uses an improved version of the original FlowLayout,
#   ScrollingFlowWidget, to display a dynamically resizable and
#   scrollable grid of generated thumbnails (tn). With this custom
#   layout, tn image grid will automatically reform when the app
#   window is resized.
#
#   Once the grid is displayed, a single click will highlight the
#   tn under the mouse and a double click will open EyeSight, a
#   separate resizable window to view the selected thumbnail at
#   full size. A right click on a tn will show a context menu
#   with 3 options delete, rename and copy path to clipboard.
#
#   The Thumbnails are generated in a threaded multi-step
#   process. This starts with a call from main_window.py
#   to sort_image_files() which generates the list of files and calls
#   load_thumbnails() and triggers the threadWorker.run() to handle
#   the thread-safe part of the tn generation. The final part is with
#   add_thumbnail() handling the adding a tn to a QLabel, mouse click
#   handlers and finally adds it to the flow layout. The add_thumbnail()
#   method is well documented if want more info.
#
#   Dependencies:
#   - PyQt6, pathlib, logging, pathvalidate
#   - Custom modules: main_window, scrollflow, eye_sight, latent_tools.
#
# Author: Greg Moore, AnotherWorkingNerd
# Date: November 2024
# History -- yea, I know git has it. but this is for me.
# May 2025 - changed the way thumbnails are created. less memory intensive. faster? maybe, maybe not.
# May 2025 - since the new thumbnail method doesn't seem much faster. added threading to speed things up.
# Aug 2025 - added context menu to delete, rename, and copy filename to system clipboard
#
####

import sys
import logging
from pathlib import Path, PurePath
from pathvalidate import is_valid_filepath, sanitize_filepath
from PyQt6.QtCore import (pyqtSignal, pyqtSlot, Qt, QSize,
                          QRunnable, QThreadPool, QObject, QFile,
                          QFileInfo, QProcess)
from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout,
                             QProgressBar,QMenu, QMessageBox, QFileDialog)
from PyQt6.QtGui import QAction, QPixmap, QImage, QImageReader
from PyQt6 import sip

# app imports.
from .scrollflow import ScrollingFlowWidget
from .eye_sight import EyeSight
from .latent_tools import show_error_box, Style

# Set up logging
logger = logging.getLogger(__name__)


class ThumbnailWorkerSignals(QObject):
    """
    Thread Signals -
        result: (QImage, str, int): Emitted when a thumbnail is successfully loaded and processed.
        progress: (int, int): Emitted with index and total count to report progress.
        finished: Emitted when all thumbnails have been processed or cancelled.
    """
    finished = pyqtSignal()
    progress = pyqtSignal(int, int)
    result = pyqtSignal(QImage, str, int)       # image, filepath, index


class ThumbnailWorker(QRunnable):
    """
    ThumbnailWorker is a background thread that is used to load and prepare image files
    for thumbnail generation. Since QPixmap is not thread-safe, add_thumbnail() is used
    to complete the process of thumbnail / label creation.
    Args:
        filepaths = (list[str]) List of image file paths to process.
        size = (QSize) Target size for the generated thumbnails.
        cancel_flag = (list[bool]) Mutable flag to allow cancellation of the worker from the main thread.
    """
    def __init__(self, file_paths, size, cancel_flag):
        super().__init__()
        self.filepaths = file_paths
        self.size = size
        self.cancel_flag = cancel_flag
        self.signals = ThumbnailWorkerSignals()

    @pyqtSlot()
    def run(self):
        # This takes care of the scaling of the thumbnail and
        # the result.emit triggers add_thumbnail() to do the
        # non-thread-safe part and add the pixmap thumbnail
        # to a uniquely named QLabel and then flow_layout
        logger.debug(f'entering thread run.')
        for i, filepath in enumerate(self.filepaths):
            if self.cancel_flag[0]:
                logger.debug('ThumbnailWorker canceled.')
                break
            try:
                reader = QImageReader(filepath)
                reader.setAutoTransform(True)
                # reader.setScaledSize(self.size)
                image = reader.read()
                if not image.isNull():
                    self.signals.result.emit(image, filepath, i)
                else:
                    logger.error(f'Image seems empty. Unable to read: {filepath}')
            # Yes, I know exception type should be specified but since this could
            # be a bunch of different exceptions, instead of guessing what it
            # MIGHT be I went for the shotgun approach... covered 'em all.
            except Exception as e:
                show_error_box(f'<strong>Error loading image</strong> {filepath}: <br> {e}', 'warning')
                logger.error(f'Error loading image {filepath}: {e}', exc_info=True)
                continue
            self.signals.progress.emit(i + 1, len(self.filepaths))
        self.signals.finished.emit()


class ThumbnailView(QWidget):
    """
    Creates a grid of thumbnails using ScrollingFlowWidget that is
    dynamically resizable and scrollable. The thumbnails are generated
    with QLabel and pixmap and have their FQPN as tooltips.
    Actions provided are highlight box around a thumbnails upon single
    click and opening EyeSight for full-size view of the selected
    thumbnail with a double click on a thumbnail.
    """
    thumbnail_selected = pyqtSignal(str)  # Signal emitted when a thumbnail is clicked

    def __init__(self, parent=None):
        super().__init__(parent)
        logger.debug('Entering Thumbnail View')
        self.current_thumbnails = []

        # At some point convert some of these to values be defined in settings.
        # Apparently there is no "Standard" thumbnail size. at least
        # not that I could find in my waaaay toooo long research with
        # various search engines.
        # Right now these are just an arbitrary size but are generally
        # near the size of thumbnails I found. Obviously some of the
        # Thumbnails were larger and some were smaller.
        # if you are reading this and don't like the current size than
        # stop whining and do something about it.
        self.tn_sizeX = 200
        self.tn_sizeY = 200
        # Initialize selected_icon - used by highlighting
        self.selected_thumbnail = None
        # initial dir. need to be a user setting too.
        self.images_directory = Path.cwd()

        self.flow_layout = ScrollingFlowWidget(self)
        self.setLayout(QVBoxLayout(self))
        self.layout().addWidget(self.flow_layout)

        # add threading and progress bar
        self.thread_pool = QThreadPool()
        self.cancel_flag = [False]  # Mutable flag to cancel ongoing worker
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setStyleSheet(Style.PROGRESSBAR_QSS)
        self.progress_bar.setFormat("Loading...")
        self.progress_bar.setVisible(False)

        self.layout().addWidget(self.progress_bar)
        self.layout().addWidget(self.flow_layout)

    def create_click_handler(self, img_path):
        def handler(event):
            self.thumbnail_selected.emit(img_path)  # Emit the selected thumbnail's path
            logger.debug(f'create_click_handler(): emitting img_path: {img_path}')
        return handler

    def show_thumbnail_context_menu(self, widget, pos):
        """
        Context menu for the created thumbnails. The context menu is
        actually added to each Thumbnail/QLabel.
        Args:
            img_path = string. FQPN for selected file.
            widget = QLabel that we are dealing with. Remember all
                        the thumbnails are actually QLabels.
        """
        # IDK if there is a better way. considering how the tn's are created.
        # if anyone ever reads this and knows of a better way, please let me
        # know too. thx.

        logging.debug('Entering show_thumbnail_context_menu')
        img_path = widget.toolTip()
        # menu = QMenu(widget)
        tn_contextm = QMenu(self)
        trash_action = QAction('Move to Trash', widget)
        trash_action.triggered.connect(lambda: self.move_thumbnail_to_trash(img_path, widget))
        rename_action = QAction('Rename File', widget)
        rename_action.triggered.connect(lambda: self.rename_thumbnail_file(img_path, widget))

        # figure out what the current OS is so the context menu
        # will have the correct verbiage.
        match sys.platform:
            case 'darwin':
                fm_name = 'Show in Finder'
            case 'linux':
                fm_name = 'Show in File Manager'
            case 'win32':
                fm_name = 'Show in Explorer'
            case 'cygwin':
                fm_name = 'Show in Exploder'        # one has to have a sense of humor
            case _:
                fm_name = 'Show file manager'
        fm_action = QAction(fm_name, widget)
        fm_action.triggered.connect(lambda: self.open_file_manager(img_path))

        clip_action = QAction('Filename to Clipboard', widget)
        clip_action.triggered.connect(lambda: self.filename_to_clipboard(img_path))
        tn_contextm.addAction(trash_action)
        tn_contextm.addAction(rename_action)
        tn_contextm.addAction(fm_action)
        tn_contextm.addAction(clip_action)
        tn_contextm.exec(widget.mapToGlobal(pos))
        logging.debug('Exiting show_thumbnail_context_menu')

    def move_thumbnail_to_trash(self, img_path, widget):
        """
        Moving on up to a deluxe trash can...
        Args:
            img_path = string. FQPN for selected file.
            widget = QLabel that we are dealing with because we need
                     remove it and anything associated with it.
        """
        logger.info(f'Moving {img_path} to trash')
        file = QFile(img_path)
        if file.exists():
            if file.moveToTrash():
                logger.info(f'Successfully moved {img_path} to trash')
                widget.setObjectName(None)
                widget.setStyleSheet('')
                widget.setParent(None)
                widget.deleteLater()
                if self.selected_thumbnail is widget:
                    self.selected_thumbnail = None
                self.flow_layout.update()
            else:
                logger.error(f'Failed to move {img_path} to trash')
                QMessageBox.warning(self, 'Error', f'Failed to move {img_path} to trash.')
        else:
            logger.warning(f'File {img_path} does not appear to exist.')
            show_error_box(f"Does {img_path} exist? I can't see it or find it.", 'critical')

    def rename_thumbnail_file(self, img_path, widget):
        """
        Rename the image file associate wth the currently
        selected thumbnail.
        Args:
            img_path = string. FQPN for selected file.
        """
        # Well this started with a much longer custom rename dialog box
        # then I found the QFileDialog convenience static function
        # getSaveFileName. This does the job but the dialog box is not as pretty
        # as the one I wrote but going native is probably a better idea.

        logger.debug(f'renaming {img_path}')
        path = img_path
        # On macOS, with its native file dialog, the filter argument is ignored.
        # this Returns a tuple of filename and filter. _ is used to discard the filter.
        newname, _ = QFileDialog.getSaveFileName(self, "New filename only.", path, "Images (*.png *.jpg *.webp)")

        if newname:
            if not is_valid_filepath(newname):
                sanitized = sanitize_filepath(newname)
                show_error_box(f'Sanitizing invalid filename of {newname}. \n\nThis has been sanitized name is: {sanitized}', 'info')
                logger.info(f'sanitizing invalid filename of {newname}. This has been sanitized and cleaned up to {sanitized}')
                newname = sanitized
            try:
                if QFile.rename(path, newname):
                    logger.info(f" File renamed to {newname}")
                else:
                    show_error_box(f"Error while renaming {path}", 'critical')
            except IOError as e:
                show_error_box(f'Unable to rename file.\n\n{e} ', 'critical')
                logger.debug(f'rename_thumbnail_file: QFile.rename returned: {e}', exc_info=True)
        else:
            print("Renaming cancelled or name not changed ")
        # need to update the grid due to the file changes.
        self.flow_layout.update()

    def filename_to_clipboard(self, img_path):
        """
        Copy FQFN to system clipboard
        Args:
            img_path = string. FQFN for selected file.

        """
        logger.debug(f'copying {img_path} to clipboard')
        clipy = QApplication.clipboard()
        clipy.clear()
        clipy.setText(img_path)
        if clipy.text() == img_path:
            logger.debug("successfully copied FQPN to clipboard.")

    def open_file_manager(self, img_path):
        """
        Open an OS specific file manager with the currently selected
        image selected.
        Args:
            img_path = string. FQFN for selected file.
        """
        # this highlights the image file in the appropriate file mgr.
        # From what I've read xdg-open has only does directories. no highlight.
        running_os = sys.platform

        # Darwin, is of course, macOS.
        if running_os.startswith('darwin'):
            QProcess.startDetached('open', ['-R', img_path])
        # Linux of any flavor
        elif running_os.startswith('linux'):
            QProcess.startDetached('xdg-open', [f'{QFileInfo(img_path).absolutePath()}'])
        # windows or cygwin
        elif running_os.startswith('win') or running_os.startswith('cyg'):
            QProcess.startDetached('explorer', [f'/select, {QFileInfo(img_path).absoluteFilePath()}'])
        else:
            show_error_box(f'{running_os} is not currently supported or there was an error launching the file manager', 'critical')
            logger.info(f'{running_os} is not currently supported or there was an error launching the file manager')

    def show_selected(self, thumbnail_widget):
        """
        Shows the thumbnail selected by user by putting a
        colored line around it.
        Args:
            thumbnail_widget - the QLabel created by add_thumbnail()
        """
        # thumbnail_widget is the QLabel created by add_thumbnail()
        selected_qss = 'QToolTip { font: 14px; padding: 2px; } QLabel { border: 2px solid cyan; }'
        if sip.isdeleted(thumbnail_widget):
            self.selected_thumbnail = None
            return  # thumbnail deleted. No reason to hang around

        if self.selected_thumbnail:
            # reset prev. selection
            self.selected_thumbnail.setStyleSheet('border: 2px solid black;')  # Add highlight

        # # highlight the new one.
        thumbnail_widget.setStyleSheet(selected_qss)
        self.selected_thumbnail = thumbnail_widget
        logger.debug('show_selected()')
        img_path = thumbnail_widget.toolTip()
        self.thumbnail_selected.emit(img_path)  # Emit the selected thumbnail's path

    def get_selected_images(self):
        """Returns the paths of the selected images."""
        selected_items = self.selectedItems()
        return [item.data(Qt.ItemDataRole.UserRole) for item in selected_items]

    def clear_thumbnails(self):
        """Removes all QLabel thumbnails whose object names start with 'thumbnail-'."""
        # needed so that the correct MD is shown for the image selected
        # when changing directories or drives.
        self.cancel_flag[0] = True  # cancel previous loading
        existing_thumbnails = [w for w in self.flow_layout.findChildren(QLabel) if w.objectName().startswith("thumbnail-")]
        if not existing_thumbnails:
            # nothing to see here... move on
            logger.debug('clear_thumbnails: No thumbnails to remove.')
            return

        logger.debug(f'clear_thumbnails: removing {len(existing_thumbnails)} thumbnails from flowLayout.')
        for tn in existing_thumbnails:
            tn.setParent(None)
            tn.destroy()
        self.flow_layout.update()
        logger.debug(f"Removed {len(existing_thumbnails)} thumbnails.")

    def add_thumbnail(self, image, filepath, index):
        """
        Adds a thumbnail to the flow layout. used by load_thumbnails & threads
        This handles the final part of thumbnail creation since
        QPixmap isn't thread-safe:
          - Creates a uniquely name QLabel.
          - Adds attributes and styling the label.
          - Converts the the QImage to a QPixmap for display in the a QLabel.
          - Adds handlers for single and double mouse clicks.
          - Adds handler for right click context menu.
          - Finally adds the label to flow_layout.
        Args:
          image = QImage. The image to be displayed as a thumbnail.
          filepath = str. FQPN of the image file. Used as the tooltip.
          index = int. image index. Used the QLabel object name.
        """
        tnLabel = QLabel()
        tnLabel.setObjectName(f'thumbnail-{index}')
        tnLabel.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        tnLabel.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        pixmap = QPixmap.fromImage(image)
        pixmap = pixmap.scaled(QSize(self.tn_sizeX, self.tn_sizeY),
                    aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio,
                    transformMode=Qt.TransformationMode.SmoothTransformation)
        tnLabel.setPixmap(pixmap)
        tnLabel.setToolTip(filepath)
        tnLabel.setStyleSheet(Style.TOOLTIPCOLOR_QSS)
        # Each thumbnail is associated with a mousePressEvent and mouseDoubleClickEvent lambda
        # ensuring events are processed correctly.
        # The seemingly extra unneeded variable in the lambda prevents bad event reporting.
        tnLabel.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        tnLabel.customContextMenuRequested.connect(lambda pos, widget=tnLabel: self.show_thumbnail_context_menu(widget, pos))
        tnLabel.mousePressEvent = lambda event, widget=tnLabel: self.show_selected(widget)
        tnLabel.mouseDoubleClickEvent = lambda event, widget=tnLabel: self.open_EyeSight(widget)
        self.flow_layout.addWidget(tnLabel)

    def update_progress(self, current, total):
        """Should be obvious. updates the progress_bar"""
        percent = int((current / total) * 100)
        self.progress_bar.setFormat(f"Creating Thumbnail {current} of {total} ({percent}%)")
        self.progress_bar.setValue(percent)

    def load_thumbnails(self, image_files):
        """Loads thumbnails from the specified directory and displays them using a worker thread.
           This can cancel the thread if needed (e.g directory or drive change).
           Thumbnail generation progress is displayed using a QProgressBar.
           Args:
               directory = str. The path to the directory containing image files.
           """

        logger.info('Loading thumbnails... ')
        # Easier for a camel to go through the eye of a needle than to process threaded thumbnails.
        # Ok, maybe that not exactly how the line goes. threading is kind of a PITA.
        worker = ThumbnailWorker(self.image_files, QSize(self.tn_sizeX, self.tn_sizeY), self.cancel_flag)
        worker.signals.result.connect(self.add_thumbnail)
        worker.signals.progress.connect(self.update_progress)
        worker.signals.finished.connect(lambda: self.progress_bar.setVisible(False))

        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.thread_pool.start(worker)
        self.flow_layout.update()

    def sort_image_files(self, directory, sort_by='Name'):
        """
        Sorts the thumbnails based on the given criterion.
        Args:
            directory: List of image file paths.
            sort_by: Sorting criterion (e.g., 'name', 'date', 'size').
        """
        logger.info(f' sorting / Resorting thumbnails by: {sort_by} - Dir: {directory}')
        # if there, clear existing thumbnails before adding new ones
        self.clear_thumbnails()
        # after a PyQt 6.8 Update this error started showing up.
        # qt.gui.imageio: QImageIOHandler: Rejecting image as it exceeds the current allocation limit of 128 megabytes
        # this next line fixes it.
        # see https://stackoverflow.com/questions/71458968/pyqt6-how-to-set-allocation-limit-in-qimagereader
        QImageReader.setAllocationLimit(0)
        self.cancel_flag[0] = False

        # well, pathlib not a "drop-in replacement". This took refactoring.
        # image_files = [f for f in os.listdir(directory) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
        # failed with AttributeError: 'PosixPath' object has no attribute 'lower'. Did you mean: 'owner'?
        self.image_files = [str(f) for f in Path(directory).iterdir() if f.suffix.lower() in {'.png', '.jpg', '.jpeg', '.webp'}]
        logger.info(f'found {len(self.image_files)} image files in {directory}')

        if not self.image_files:
            logger.debug('sort_thumbnails: no files found')
            show_error_box(f'No image files in {directory}', 'warning')
            # TODO: FV++ - convert show_error_box to Notification with # and sort type
        else:
            if sort_by == 'Name':
                self.image_files.sort(key=lambda f: Path(f).name.lower())
            elif sort_by == 'Creation Date':
                self.image_files.sort(key=lambda f: Path(f).stat().st_mtime)
            elif sort_by == 'File Size':
                self.image_files.sort(key=lambda f: Path(f).stat().st_size)
            elif sort_by == 'Extension':
                self.image_files.sort(key=lambda f: Path(f).suffix.lower())
            elif sort_by == 'Default':
                pass        # default is no sort
            logger.debug(f'load_thumbnails: through sort_by if block. Sort by {sort_by}')
        self.load_thumbnails(self.image_files)

    def open_EyeSight(self, thumbnail_widget):
        """Upon image double click open the image in EyeSight."""
        # I can see clearly now that the double-click has gone...
        #
        # pass in the FQPN from the TN tooltip and then
        # open up EyeSight in a new window with the full image.
        filename = thumbnail_widget.toolTip()
        logger.info(f"Opening EyeSight for {filename}")
        self.monocle = EyeSight(filename)
        self.monocle.show()
