# LatentEye
# Author: Greg Moore - https://github.com/AnotherWorkingNerd
# LatentEye is a tool for viewing and analyzing metadata in AI-generated images 
# from ComfyUI and Stable Diffusion based tools. 
#
# Features:
# - File tree for selecting directories.
# - Thumbnail view for displaying image previews of png, jpeg, and webp
# - Metadata panel for displaying image metadata for png and jpeg images
# - Customizable splitter layout for resizing panels.
# - SOON: Sorting options for thumbnails by name, creation date, or file size.
# - EyeSight for viewing selected images full size.
#
# Dependencies:
# - Python 3.12
# - PyQt6.8
# - Custom modules: main_window, file_tree, info_view, latent_tools, thumbnail_view.
#
# Author: Greg M.
# Date: November 2024

# lets get this party started
import logging
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QScreen
from src.main_window import MainWindow

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(module)s:%(lineno)s | %(message)s')
    # logging.basicConfig(filemode='w', filename='logging-output.log',
    #                     level=logging.DEBUG, datefmt='%H:%M:%S',
    #                     format='%(asctime)s - %(levelname)s - %(module)s:%(lineno)s | %(message)s'
    #                     )

    logger = logging.getLogger(__name__)
    logger.debug('Starting')
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    center = QScreen.availableGeometry(QApplication.primaryScreen()).center()
    primary_frame = window.frameGeometry()
    primary_frame.moveCenter(center)
    window.move(primary_frame.topLeft())
    sys.exit(app.exec())
