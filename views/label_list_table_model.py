from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from views.base_table_model import BaseTableModel


class LabelListTableModel(BaseTableModel):
    def __init__(self, parent=None):
        BaseTableModel.__init__(self, parent,
                                ['', 'ID', 'Tracking ID', 'Trackable', 'Category', 'Second Category', 'Third Category'])

    def append(self, uid, label, id=-1, track_id=-1, trackable=True, second_category=None, third_category=None):
        self.table_data.append({'uid': uid,
                                'category': str(label),  # 4
                                'id': id,
                                'track_id': track_id,  # 2
                                'trackable': trackable,  # 3 check box, mặc định là True
                                'second_category': second_category,  # 5 combo box, mặc định là dòng đầu
                                'third_category': third_category,  # 6 combo box, mặc định là dòng đầu
                                'visible': True,
                                'checked': False})
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
            if col == 1:
                content = data_row['id']
            elif col == 2:
                content = data_row['track_id']
            elif col == 4:
                content = data_row['category']
            elif col == 5:
                content = data_row['second_category']
            elif col == 6:
                content = data_row['third_category']
            return content
        if role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        return super(LabelListTableModel, self).data(index, role)

    def setData(self, index, value, role):
        if not index.isValid():
            return False
        row = index.row()
        column = index.column()
        if role == Qt.CheckStateRole:
            if column == 0:
                self.table_data[row]['visible'] = value == Qt.Checked
            if column == 3:
                self.table_data[row]['trackable'] = value == Qt.Checked
            self.dataChanged.emit(index, index)
            return True
        elif role == Qt.EditRole:
            if column == 1:
                self.table_data[row]['id'] = str(value)
            elif column == 2:
                self.table_data[row]['track_id'] = str(value)
            elif column == 4:
                self.table_data[row]['category'] = str(value)
            elif column == 5:
                self.table_data[row]['second_category'] = str(value)
            elif column == 6:
                self.table_data[row]['third_category'] = str(value)
            self.dataChanged.emit(index, index)
            return True
        return False

    def checkState(self, index):
        row = index.row()
        column = index.column()
        data_row = self.table_data[row]
        if column == 0:
            return Qt.Checked if data_row['visible'] else Qt.Unchecked
        elif column == 3:
            return Qt.Checked if data_row['trackable'] else Qt.Unchecked
        return None

    def flags(self, index):
        fl = QAbstractTableModel.flags(self, index)
        column = index.column()
        if column in [0, 3]:
            fl |= Qt.ItemIsUserCheckable
        elif column in [1, 2]:
            fl |= Qt.ItemIsEditable
        elif column in [4, 5, 6]:
            fl |= Qt.ItemIsSelectable | Qt.ItemIsEditable
        return fl

    def remove_row(self, uid):
        row = self.get_row(uid)
        if row == -1:
            return
        del self.table_data[row]
        self.layoutChanged.emit()

    def toggle_visible_all(self, visible):
        for row in range(0, len(self.table_data)):
            index = self.index(row, 0)
            self.setData(index,
                         Qt.Checked if visible else Qt.Unchecked,
                         Qt.EditRole)

    def get_row(self, uid):
        row = 0
        for r in self.table_data:
            if r['uid'] == uid:
                break
            row += 1
        return -1 if row == len(self.table_data) else row

    def get_data(self, uid):
        for r in self.table_data:
            if r['uid'] == uid:
                return r
        return None


class LabelListTableComboBoxDelegate(QItemDelegate):

    def __init__(self, owner, item_list):
        QItemDelegate.__init__(self, owner)
        self.item_list = item_list

    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        editor.addItems(self.item_list)
        editor.setCurrentIndex(0)
        editor.installEventFilter(self)
        return editor

    def setEditorData(self, editor, index):
        value = index.data(Qt.DisplayRole)
        i = 0
        for item in self.item_list:
            if item == value:
                editor.setCurrentIndex(i)
            i += 1

    def setModelData(self, editor, model, index):
        model.setData(
            index, self.item_list[editor.currentIndex()], role=Qt.EditRole)
