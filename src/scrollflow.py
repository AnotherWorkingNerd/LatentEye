#  ScrollingFlowWidget - scrollflow.py
#   Date: 2024 Nov
#   Author: Greg W. Moore, et al.
#
#   This is an improved FlowLayout when used for thumbnails. With
#   this custom layout, thumbnail images grid will automatically reform
#   and scroll when the app window is resized.
#
#   Most of this code was adapted from the example provided by
#   The Qt Company Ltd. and was converted from PySide6 to PyQt6.
#   There were other small textual changes that did not affect the
#   function of the code. This was the easy part. The harder part
#   came from PyQt4 code that contained the scrolling part.
#   This was converted to PyQt6 and further modified. The Original
#   code came from https://github.com/cgdougm/PyQtFlowLayout/blob/master/PyQtFlowLayout.pyw
#   I imagine Doug would be surprised to see his 11 year old code
#   being refactored.
#
#   The original FlowLayout example as of this writing is at:
#   https://doc.qt.io/qtforpython-6/examples/example_widgets_layouts_flowlayout.html
#   Other example Qt code can be found at https://doc.qt.io/qtforpython-6/examples/index.html
#
#   Please see Qt copyright statement below.
#
# Copyright (C) 2013 Riverbank Computing Limited.
# Copyright (C) 2022 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause
#
####

from PyQt6.QtCore import Qt, QMargins, QPoint, QRect, QSize
from PyQt6.QtWidgets import QLayout, QGridLayout, QSizePolicy, QWidget, QScrollArea

class FlowLayout(QLayout):
    """
    A custom layout that arranges child widgets in a dynamically 
    sized scrollable grid, reshaping the grid when the window is 
    resized.
    """

    def __init__(self, parent=None, margin=0, spacing=-1):
        super().__init__(parent)

        if parent is not None:
            self.setContentsMargins(QMargins(margin, margin, margin, margin))

        self.setSpacing(spacing)
        self._item_list = []

    def __del__(self):
        """ Destructor for FlowLayout """
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        """ Add an item to the layout """
        self._item_list.append(item)

    def count(self):
        """ how many items are flowing """
        return len(self._item_list)

    def itemAt(self, index):
        """ Will the Item at INDEX location please stand up """
        if index >= 0 and index < len(self._item_list):
            return self._item_list[index]

        return None

    def takeAt(self, index):
        """  Removes and returns the item at the given index."""
        if index >= 0 and index < len(self._item_list):
            return self._item_list.pop(index)

        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self.doLayout(QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        super(FlowLayout, self).setGeometry(rect)
        self.doLayout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._item_list:
            size = size.expandedTo(item.minimumSize())

        margins = self.contentsMargins()
        # Old: size += QSize(2 * self.contentsMargins().top(), 2 * self.contentsMargins().top())
        # this is basically the same.
        margins.top()
        size += QSize(2 * margins.left(), 2 * margins.top())
        return size

    def doLayout(self, rect, test_only):
        """
        Arranges the items in the layout within the rectangle.
        """
        if self._item_list:
            self.rows = 1
        else:
            self.rows = 0
        self.rows_y = [rect.y()]

        x = rect.x()
        y = rect.y()
        line_height = 0
        spacing = self.spacing()

        for item in self._item_list:
            style = item.widget().style()
            layout_spacing_x = spacing + style.layoutSpacing(
                QSizePolicy.ControlType.PushButton,
                QSizePolicy.ControlType.PushButton,
                Qt.Orientation.Horizontal)
            layout_spacing_y = spacing + style.layoutSpacing(
                QSizePolicy.ControlType.PushButton,
                QSizePolicy.ControlType.PushButton,
                Qt.Orientation.Vertical)
            space_x = spacing + layout_spacing_x
            space_y = spacing + layout_spacing_y
            next_x = x + item.sizeHint().width() + space_x

            # Running out of horizontal space and starting a new line.
            # Calculate x position for the next item.
            if next_x - space_x > rect.right() and line_height > 0:
                x = rect.x()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0

                # Updating added variables.
                self.rows += 1
                self.rows_y.append(y)

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = next_x
            line_height = max(line_height, item.sizeHint().height())

        new_height = y + line_height - rect.y()
        return new_height

class ResizeScrollArea(QScrollArea):
    """A scroll area that updates child FlowLayout dimensions on resize. """

    def __init__(self, parent=None):
        super().__init__(parent)

    def resizeEvent(self, event):
        """ Handle resize event to update FlowLayout size within the scroll area. """
        wrapper = self.findChild(QWidget)
        flow = wrapper.findChild(FlowLayout)

        if wrapper and flow:
            # Set FlowLayout geometry to the current viewport size.
            width = self.viewport().width()
            height = flow.heightForWidth(width)
            size = QSize(width, height)
            point = self.viewport().rect().topLeft()
            flow.setGeometry(QRect(point, size))
            self.viewport().update()

        # Call parent class resizeEvent to maintain default behavior.
        super().resizeEvent(event)

class ScrollingFlowWidget(QWidget):
    """
    A widget that combines a resizable and scrollable FlowLayout.
    Use addWidget() to add items to the layout.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Create main grid layout for the widget.
        grid = QGridLayout(self)

        # Create a scrollable area to contain the flow layout.
        scroll_area = ResizeScrollArea()
        self._wrapper = QWidget(scroll_area)
        self.flowLayout = FlowLayout(self._wrapper)
        self._wrapper.setLayout(self.flowLayout)

        # Configure the scroll area to automatically resize with the flow layout.
        scroll_area.setWidget(self._wrapper)
        scroll_area.setWidgetResizable(True)

        # Add scroll area to the main grid layout.
        grid.addWidget(scroll_area)

    def addWidget(self, widget):
        """Add a widget to the FlowLayout and set its parent to the wrapper widget."""
        self.flowLayout.addWidget(widget)
        widget.setParent(self._wrapper)
