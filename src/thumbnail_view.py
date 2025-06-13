# Thumbnail display
#  Date: 2024 Nov
#
#   This code uses an improved version of the original FlowLayout,
#   ScrollingFlowWidget, to display a dynamically resizable and
#   scrollable grid of generated thumbnails (tn). With this custom
#   layout, tn images grid will automatically reform when the app
#   window is resized.
#
#   Once the grid is displayed, a single click will highlight the
#   tn under the mouse and a double click will open EyeSight, a
#   separate resizable window to view the selected thumbnail at
#   full size.
#
#   The Thumbnails are generated in a partly threaded multi-step
#   process. This starts with a call from main_window.py
#   to sort_image_files() which generates the list of files and calls
#   load_thumbnails() and triggers the threadWorker.run() to handle
#   the thread-safe part of the tn generation. The final part is with
#   add_thumbnail() handling the adding a tn to a QLabel, mouse click
#   handlers and finally adds it to the flow layout. The add_thumbnail()
#   method is well documented if want more info.
#
#   Dependencies:
#   - PyQt6, pathlib
#   - Custom modules: main_window, scrollflow, eye_sight, latent_tools.
#
# Author: Greg Moore, AnotherWorkingNerd
# Date: November 2024 revised June 2025
####

# thumbnail_view imports
import os       # like I said... old habits...
import logging
from pathlib import Path
from PyQt6.QtCore import pyqtSignal, pyqtSlot, Qt, QSize, QRunnable, QThreadPool, QObject
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QProgressBar
from PyQt6.QtGui import QPixmap, QImage, QImageReader

# app imports.
from .scrollflow import ScrollingFlowWidget
from .eye_sight import EyeSight
from .latent_tools import show_error_box, ttip_color, Style

# Set up logging
logger = logging.getLogger(__name__)

class ThumbnailWorkerSignals(QObject):
    """Thread Signals -
        result: (QImage, str, int): Emitted when a thumbnail is successfully loaded and processed.
        progress: (int, int): Emitted with index and total count to report progress.
        finished: Emitted when all thumbnails have been processed or cancelled.
    """
    finished = pyqtSignal()
    progress = pyqtSignal(int, int)
    result = pyqtSignal(QImage, str, int)       # image, filepath, index


class ThumbnailWorker(QRunnable):
    """ThumbnailWorker is a background thread that is used to load and prepare image files
       for thumbnail generation. Since QPixmap is not thread-safe, add_thumbnail() is used
       to complete the process of thumbnail / label creation.

        Args:
          filepaths (list[str]): List of image file paths to process.
          size (QSize): Target size for the generated thumbnails.
          cancel_flag (list[bool]): Mutable flag to allow cancellation of the worker from the main thread.
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
        # see latentTools for QSS for the progress bar. quite a bit can be done.
        # self.progress_bar.setStyleSheet("QProgressBar { color: green; }")  # Change progress bar color
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

    def show_selected(self, thumbnail_widget):
        """
        Shows the thumbnail selected by user by putting a colored line around it.
        """

        selected_qss = 'QToolTip { font: 14px; padding: 2px; } QLabel { border: 2px solid cyan; }'
        if self.selected_thumbnail:
            # reset prev. selection
            self.selected_thumbnail.setStyleSheet('border: 2px solid black;')
        # highlight the new one.
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

        logger.debug(f'clear_thumbnails: removing {len(existing_thumbnails)} thumbnails to remove.')
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
          - Add handlers for single and double mouse clicks.
          - Finally adds the label to flow_layout.
        Args:
          image (QImage): The image to be displayed as a thumbnail.
          filepath (str): FQPN of the image file. Used as the tooltip.
          index (int): image index. Used the QLabel object name.
        """
        label = QLabel()
        label.setObjectName(f'thumbnail-{index}')
        label.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        label.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        pixmap = QPixmap.fromImage(image)
        pixmap = pixmap.scaled(QSize(self.tn_sizeX, self.tn_sizeY),
                    aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio,
                    transformMode=Qt.TransformationMode.SmoothTransformation)
        label.setPixmap(pixmap)
        label.setToolTip(filepath)
        label.setStyleSheet(ttip_color('#FAFAFA'))
        # Each thumbnail is associated with a mousePressEvent and mouseDoubleClickEvent lambda
        # ensuring events are processed correctly
        # the seemingly extra unneeded variable in the lambda prevents bad event reporting.
        label.mousePressEvent = lambda event, widget=label: self.show_selected(widget)
        label.mouseDoubleClickEvent = lambda event, widget=label: self.open_EyeSight(widget)
        self.flow_layout.addWidget(label)

    def update_progress(self, current, total):
        """Should be obvious. updates the progress_bar"""
        percent = int((current / total) * 100)
        self.progress_bar.setFormat(f"Loading {current} of {total} ({percent}%)")
        self.progress_bar.setValue(percent)

    def load_thumbnails(self, image_files):
        """Loads thumbnails from the specified directory and displays them using a worker thread.
           This can cancel the thread if needed (e.g directory or drive change).
           Thumbnail generation progress is displayed using a QProgressBar.

           Args:
            directory (str): The path to the directory containing image files.
           """

        logger.info('Loading thumbnails... ')
        # Easier for a camel to go through the eye of a needle than to process threaded thumbnails.
        # Ok, maybe that not exactly how the line goes. threading is a PITA.
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
        WORK IN PROGRESS
        Sorts the thumbnails based on the given criterion.
        :param image_paths: List of image file paths.
        :param sort_by: Sorting criterion (e.g., 'name', 'date', 'size').
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
        logger.info(f'found {len(self.image_files)} graphics files in {directory}')

        if not self.image_files:
            logger.debug('sort_thumbnails: no files found')
            show_error_box(f'No image files in {directory}', 'warning')
        else:
            if sort_by == 'Name':
                self.image_files.sort(key=lambda f: Path(f).name.lower())
            elif sort_by == 'Creation Date':
                self.image_files.sort(key=lambda f: Path(f).stat().st_ctime)
            elif sort_by == 'File Size':
                self.image_files.sort(key=lambda f: Path(f).stat().st_size)
            elif sort_by == 'Extension':
                self.image_files.sort(key=lambda f: Path(f).suffix.lower())
            elif sort_by == 'Default':
                pass        # default is no sort
            logger.debug('load_thumbnails: through sort_by if block')
        self.load_thumbnails(self.image_files)

    def open_EyeSight(self, thumbnail_widget):
        """Upon image double click open the image in EyeSight."""
        # pass in the FQPN from the TN tooltip and then
        # open up new window with the full image.
        filename = thumbnail_widget.toolTip()
        logger.info(f"Opening EyeSight for {filename}")
        self.monocle = EyeSight(filename)
        self.monocle.show()
