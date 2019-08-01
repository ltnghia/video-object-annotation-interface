import sys

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from libs.utils import *

BB = QDialogButtonBox


class ChooseCategoryDialog(QDialog):

    def __init__(self, text='Choose object category', parent=None, category_names=None):
        super(ChooseCategoryDialog, self).__init__(parent)

        self.result = ''

        layout = QVBoxLayout()
        self.buttonBox = bb = BB(BB.Ok | BB.Cancel, Qt.Horizontal, self)
        bb.button(BB.Ok).setIcon(new_icon('done'))
        bb.button(BB.Cancel).setIcon(new_icon('undo'))
        bb.accepted.connect(self.validate)
        bb.rejected.connect(self.reject)
        layout.addWidget(bb)

        if category_names and len(category_names) > 0:
            self.list_widget = QListWidget(self)
            for item in category_names:
                self.list_widget.addItem(item)
            self.list_widget.itemClicked.connect(self.list_item_click)
            self.list_widget.itemDoubleClicked.connect(
                self.list_item_double_click)
            layout.addWidget(self.list_widget)

        self.setLayout(layout)

    def validate(self):
        if self.result.strip():
            self.accept()

    def postProcess(self):
        self.result = self.result.strip()

    def popUp(self, text='', move=True):
        if move:
            self.move(QCursor.pos())
        return self.result if self.exec_() else None

    def list_item_click(self, item):
        self.result = item.text().strip()

    def list_item_double_click(self, item):
        self.list_item_click(item)
        self.validate()
