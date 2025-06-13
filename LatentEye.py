# LatentEye
# Author: Greg Moore - https://github.com/AnotherWorkingNerd
# I spy with my LatentEye, metadata!

import logging
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QScreen
from src.main_window import MainWindow

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(module)s:%(lineno)s | %(message)s' )
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
