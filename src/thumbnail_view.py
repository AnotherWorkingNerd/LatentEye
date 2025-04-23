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
#   The thumbnails are generated entirely in load_thumbnails()
#   where the full FQPN of the tn is added as a tooltip. The tooltip
#   is used later to get the metadata. Each tn is assigned 2 lambdas
#   for the mousePressEvent and mouseDoubleClickEvent.
#
#   Just in case, FQPN = Fully Qualified Path Name. What Exactly
#   _that_ means depends on the platform that executes this code.
#   Anything that has a .. or ** or evenb a ~ is a relitive path.
#   On Windows, if is does not have a drive specifier, it's also
#   a relitive path. We all know relitives can be weird. I know
#   mine are.
#
#   Dependencies:
#   - PyQt6, pathlib
#   - Custom modules: main_window, scrollflow, eye_sight, latent_tools.
#
# Author: Greg Moore, AnotherWorkingNerd
# Date: November 2024
####

import os       # like I said... old habits...
import logging
from pathlib import Path, PurePath
from PyQt6.QtCore import pyqtSignal, Qt, QSize
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtGui import QPixmap, QImageReader

# app imports.
from .scrollflow import ScrollingFlowWidget
from .eye_sight import EyeSight
from .latent_tools import show_error_box, ttip_color

# Set up logging
logger = logging.getLogger(__name__)

class ThumbnailView(QWidget):
    """
    Creates a grid of thumbnails using ScrollingFlowWidget that is
    dynamically resizable and scrollable. The thumbnails are generated
    with QLabel and pixmap and have their FQPN as tooltips.
    Actions provided are highligh box around a thumbnails upon single
    click and opening EyeSignt for full-size view of the selected
    thumbnail with a double click on a thumbnail.
    """

    thumbnail_selected = pyqtSignal(str)  # Signal emitted when a thumbnail is clicked

    def __init__(self, parent=None):
        super().__init__(parent)
        logger.debug('entering Thumbnail View')
        self.current_thumbnails = []

        # Apperenetly there is no "Standard" thumbnail size. at least
        # not that I could find in my waaaay toooo long research with
        # various search engines.
        # Right now these are just an arbitrary size but are generally
        # near the size of thumbnails I found. Obviously some larger
        # and some smaller.
        self.tn_sizeX = 200
        self.tn_sizeY = 200
        # Initialize selected_icon - used by hightlighting
        self.selected_thumbnail = None
        # initial dir. need to be a user setting too.
        self.images_directory = Path.cwd()

        self.flow_layout = ScrollingFlowWidget(self)
        self.setLayout(QVBoxLayout(self))
        self.layout().addWidget(self.flow_layout)

    def show_selected(self, thumbnail_widget):
        """
        Shows the thumbnail selected by a single click
        by putting a colored line around it.
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
        # this was needed so that the MD in the table
        # is for selected image not something else.
        existing_thumbnails = [w for w in self.flow_layout.findChildren(QLabel) if w.objectName().startswith("thumbnail-")]
        if not existing_thumbnails:
            # nothing here... move on
            logger.debug("No thumbnails to remove.")
            return

        for tn in existing_thumbnails:
            tn.setParent(None)
            tn.destroy()
        self.flow_layout.update()

    def load_thumbnails(self, directory):
        """Loads thumbnails from the specified directory and displays them."""

        logger.info('Loading thumbnails... ')
        # if there, clear existing thumbnails before adding new ones
        self.clear_thumbnails()
        # after a PyQt 6.8 Update this error started showing up.
        # qt.gui.imageio: QImageIOHandler: Rejecting image as it exceeds the current allocation limit of 128 megabytes
        # this next line fixes it.
        # see https://stackoverflow.com/questions/71458968/pyqt6-how-to-set-allocation-limit-in-qimagereader
        QImageReader.setAllocationLimit(0)

        # well, pathlib not a "drop-in replacement". This took refactoring.
        image_files = [f for f in Path(directory).iterdir() if f.suffix.lower() in {'.png', '.jpg', '.jpeg', '.webp'}]
        logger.info(f'found {len(image_files)} image graphics files in {directory}')

        # create thumbnails from filtered image files. Then set
        # attributes to free memory on label close and to allow
        # styling to enable show_selected()
        label_id_num = 0
        for filename in image_files:
            filepath = str(PurePath(directory).joinpath(filename))
            tn_label = QLabel()
            tn_label.setObjectName(f'thumbnail-{label_id_num}')
            tn_label.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
            tn_label.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            label_id_num += 1
            try:
                pixmap = QPixmap(filepath)
            except Exception as e:
                # Yes, I know exception type should be specified but
                # since this could be a bunch of different exceptions
                # insted of guessing what it MIGHT be I went for the
                # the shotgun approach... covered 'em all.
                logger.error(f'Error loading image {filepath}: {e}', exc_info=True)
                show_error_box(f'<strong>Error loading image</strong> {filepath}: <br> {e}', 'warning')
                continue

            pixmap = pixmap.scaled(QSize(self.tn_sizeX, self.tn_sizeY),
                        aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio,
                        transformMode=Qt.TransformationMode.SmoothTransformation)
            tn_label.setPixmap(pixmap)
            tn_label.setToolTip(filepath)
            tn_label.setStyleSheet(ttip_color('#FAFAFA'))

            # Each thumbnail is associated with a mousePressEvent and mouseDoubleClickEvent lambda
            # ensuring events are processed correctly
            # the seemingly extra unneeded variable in the lambda prevents bad event reporting.
            tn_label.mousePressEvent = lambda event, widget=tn_label: self.show_selected(widget)
            tn_label.mouseDoubleClickEvent = lambda event, widget=tn_label: self.open_EyeSight(widget)
            self.flow_layout.addWidget(tn_label)
            self.flow_layout.update()

    # this needs work. need to understnad sortiing.
    def sort_thumbnails(self, image_paths, sort_by):
        """
        WORK IN PROGRESS
        Sorts the thumbnails based on the given criterion.
        :param image_paths: List of image file paths.
        :param sort_by: Sorting criterion (e.g., 'name', 'date', 'size').
        """
        # as I understand it file date and time still require os.path
        logger.debug('sort thumbnails()')
        if sort_by == 'name':
            return sorted(image_paths, key=lambda x: os.path.basename(x).lower())
            # return sorted(image_paths, key=lambda x: Path(x).name.lower())
        elif sort_by == 'date':
            return sorted(image_paths, key=lambda x: os.path.getctime(x))
        elif sort_by == 'size':
            return sorted(image_paths, key=lambda x: os.path.getsize(x))
        else:
            return image_paths  # Default (no sorting)

    def open_EyeSight(self, thumbnail_widget):
        # pass in the FQPN from the TN tooltip aand then
        # open up new window with the full image.
        filename = thumbnail_widget.toolTip()
        logger.info(f"Opening EyeSight for {filename}")
        self.monocle = EyeSight(filename)
        self.monocle.show()
