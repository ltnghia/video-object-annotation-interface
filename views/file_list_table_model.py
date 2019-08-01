from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from views.base_table_model import BaseTableModel


class FileListTableModel(BaseTableModel):

    def __init__(self, parent=None):
        BaseTableModel.__init__(self, parent, ['ID', 'Has GT', 'File name'])

    def append(self, id, has_gt, file_name):
        self.table_data.append({'id': id,
                                'has_gt': has_gt,
                                'file_name': file_name})
        self.layoutChanged.emit()

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        row = index.row()
        col = index.column()
        data_row = self.table_data[row]
        if role == Qt.CheckStateRole:
            return self.checkState(QPersistentModelIndex(index))
        if role == Qt.DisplayRole:
            content = ''
            if col == 0:
                content = data_row['id']
            elif col == 2:
                content = data_row['file_name']
            return content
        return super(FileListTableModel, self).data(index, role)

    def setData(self, index, value, role):
        if not index.isValid():
            return False
        row = index.row()
        column = index.column()
        if role == Qt.CheckStateRole and column == 1:
            self.table_data[row]['has_gt'] = value == Qt.Checked
            self.dataChanged.emit(index, index)
            return True
        elif role == Qt.EditRole:
            self.dataChanged.emit(index, index)
            return True
        return False

    def checkState(self, index):
        row = index.row()
        column = index.column()
        data_row = self.table_data[row]
        if column == 1:
            return Qt.Checked if data_row['has_gt'] else Qt.Unchecked
        return None

    def flags(self, index):
        fl = QAbstractTableModel.flags(self, index)
        column = index.column()
        if column == 1:
            fl |= Qt.ItemIsUserCheckable | Qt.ItemIsEditable
        return fl
