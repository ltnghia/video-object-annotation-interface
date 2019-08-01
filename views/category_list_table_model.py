from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *


class CategoryListTableModel(QAbstractTableModel):
    def __init__(self, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self.header_labels = ['ID', 'Category']
        self.table_data = []
        # self.table = None

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

    def append(self, id, category):
        self.table_data.append({'id': id,
                                'category': category})
        self.layoutChanged.emit()

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        row = index.row()
        col = index.column()
        data_row = self.table_data[row]
        if role == Qt.DisplayRole:
            content = ''
            if col == 0:
                content = data_row['id']
            elif col == 1:
                content = data_row['category']
            return content
        return QVariant()

    def setData(self, index, value, role):
        return False
