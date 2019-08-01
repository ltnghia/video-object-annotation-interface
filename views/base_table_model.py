from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *


class BaseTableModel(QAbstractTableModel):
    __currentRow = -1
    table_data = []
    header_labels = []

    def __init__(self, parent=None, header_labels=[]):
        QAbstractTableModel.__init__(self, parent)
        self.header_labels = header_labels

    def data(self, index, role=Qt.DisplayRole):
        if index.row() == self.__currentRow:
            if role == Qt.BackgroundColorRole:
                return QVariant(QColor(4, 110, 229))
            elif role == Qt.ForegroundRole:
                return QVariant(QColor(Qt.white))
        return QVariant()

    def setCurrentRow(self, row):
        self.__currentRow = row
        self.layoutChanged.emit()

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.header_labels[section]
        return QAbstractTableModel.headerData(self, section, orientation, role)

    def columnCount(self, parent):
        return len(self.header_labels)

    def rowCount(self, parent):
        return len(self.table_data)

    def clear(self):
        self.table_data = []
        self.layoutChanged.emit()
