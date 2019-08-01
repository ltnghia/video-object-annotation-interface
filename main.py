#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import numpy as np
import os
import platform
import re
import sys
import uuid
import copy

from functools import partial
from collections import defaultdict

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

import resources

from views.create_palette import color_palette

from libs.constants import *
from libs.version import __version__
from libs.settings import Settings
from libs.string_bundle import StringBundle
from libs.utils import *
from views.second_category_list_table_model import SecondCategoryListTableModel
from views.third_category_list_table_model import ThirdCategoryListTableModel

from views.canvas import Canvas
from views.category_list_table_model import CategoryListTableModel
from views.choose_category_dialog import ChooseCategoryDialog
from views.color_dialog import ColorDialog
from views.file_list_table_model import FileListTableModel
from views.label_dialog import LabelDialog
from views.label_list_table_model import LabelListTableComboBoxDelegate, LabelListTableModel
from views.shape import Shape
from views.toolbar import ToolBar
from views.zoom_widget import ZoomWidget

__appname__ = 'Video Object Annotation Interface'
__author__ = 'Trung-Nghia Le'


class MainWindow(QMainWindow):
    FIT_WINDOW, FIT_WIDTH, MANUAL_ZOOM = list(range(3))

    # Category
    category_set_name = None
    names_to_categories_dict = {}
    category_ids_to_names_dict = {}
    category_names = []

    names_to_second_categories_dict = {}
    second_category_ids_to_names_dict = {}
    second_category_names = []

    names_to_third_categories_dict = {}
    third_category_ids_to_names_dict = {}
    third_category_names = []

    # Image paths
    image_paths = []
    images_dict = {}
    current_image = None

    # Shapes
    uid_to_shapes_dict = {}
    shapes_to_uids_dict = {}
    current_uid = None

    # Current paths
    dataset_info_path = None
    dataset_root_path = None
    image_file_path = None
    current_index = -1

    # Zoom
    zoom_level = 100
    fit_window = False

    # Draw colors
    line_color = None
    fill_color = None

    # Current image
    image = QImage()

    # Check data has changed or not
    dirty = False

    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle(__appname__)

        # Load string bundle for i18n
        self.string_bundle = StringBundle.get_bundle()

        def get_string(strId):
            return self.string_bundle.get_string(strId)

        # For loading all image under a directory
        self.dirname = None

        self.data = None

        self.label_coordinates = QLabel('')

        # Initial Zoom
        self.zoom_widget = ZoomWidget()
        self.zoom_widget.setEnabled(False)
        self.zoom_widget.valueChanged.connect(self.paint_canvas)
        self.zoom_mode = self.MANUAL_ZOOM

        # Initial Scalers
        self.scalers = {
            self.FIT_WINDOW: self.scale_fit_window,
            self.FIT_WIDTH: self.scale_fit_width,
            self.MANUAL_ZOOM: lambda: 1,
        }

        self._noSelectionSlot = False

        self.palette = color_palette()

        # region Actions
        action = partial(new_action, self)

        quit_action = action(get_string('quit'), self.close,
                             'Ctrl+Q', 'quit', get_string('quitApp'))

        open_category_file_action = action(get_string('openCategoryFile'), self.open_category_file,
                                           'Ctrl+O', 'open', get_string('openCategoryFile'))

        open_second_category_file_action = action(get_string('openCategoryFile'), self.open_second_category_file,
                                           'Ctrl+O', 'open', get_string('openCategoryFile'))

        open_third_category_file_action = action(get_string('openCategoryFile'), self.open_third_category_file,
                                           'Ctrl+O', 'open', get_string('openCategoryFile'))

        open_image_dataset_action = action(get_string('openDatasetFile'), self.open_dataset_file,
                                           'Ctrl+I', 'open', get_string('openDatasetFile'))

        filter_dataset_action = action(get_string('openDir'), self.filter_dataset_dialog,
                                       'Ctrl+U', 'open', get_string('openDir'))

        open_next_image_action = action(get_string('nextImg'), self.open_next_image,
                                        'd', 'next', get_string('nextImgDetail'))

        open_previous_image_action = action(get_string('prevImg'), self.open_previous_image,
                                            'a', 'prev', get_string('prevImgDetail'))

        save_label_list_action = action(get_string('saveLabelList'), self.save_label_list,
                                        'Ctrl+S', 'save', get_string('saveDetail'), enabled=False)

        save_dataset_action = action(get_string('saveDataset'), self.save_dataset,
                                     'Ctrl+S', 'save', get_string('saveDetail'), enabled=False)

        export_canvas_action = action(get_string('exportCanvas'), self.export_canvas,
                                      'Ctrl+E', 'save', get_string('saveDetail'), enabled=False)

        create_shape_action = action(get_string('crtBox'), self.create_shape,
                                     'w', 'new', get_string('crtBoxDetail'), enabled=False)

        delete_shape_action = action(get_string('delBox'), self.delete_selected_shape,
                                     'Delete', 'delete', get_string('delBoxDetail'), enabled=False)

        copy_shape_action = action(get_string('dupBox'), self.copy_selected_shape,
                                   'Ctrl+D', 'copy', get_string('dupBoxDetail'), enabled=False)

        reset_all_action = action(get_string('resetAll'), self.reset_all,
                                  None, 'resetall', get_string('resetAllDetail'))

        change_line_thickness_action = action(get_string('changeLineThickness'), self.change_line_thickness,
                                              None, None, get_string('changeLineThickness'))

        change_font_size_action = action(get_string('changeFontSize'), self.change_font_size,
                                         None, None, get_string('changeFontSize'))

        choose_color_action = action(get_string('boxLineColor'), self.choose_color,
                                     'Ctrl+L', 'color_line', get_string('boxLineColorDetail'))

        help_action = action(get_string('tutorial'), self.show_tutorial_dialog,
                             None, 'help', get_string('tutorialDetail'))

        show_action = action(get_string('info'), self.show_info_dialog,
                             None, 'help', get_string('info'))

        # Zooms
        zoom_action = QWidgetAction(self)
        zoom_action.setDefaultWidget(self.zoom_widget)

        zoom_in_action = action(get_string('zoomin'), partial(self.add_zoom, 10), 'Ctrl++',
                                'zoom-in', get_string('zoominDetail'), enabled=False)

        zoom_out_action = action(get_string('zoomout'), partial(self.add_zoom, -10), 'Ctrl+-',
                                 'zoom-out', get_string('zoomoutDetail'), enabled=False)

        zoom_original_action = action(get_string('originalsize'), partial(self.set_zoom, 100), 'Ctrl+=',
                                      'zoom', get_string('originalsizeDetail'), enabled=False)

        fit_window_action = action(get_string('fitWin'), self.set_fit_window, 'Ctrl+F',
                                   'fit-window', get_string('fitWinDetail'), checkable=True, enabled=False)

        fit_width_action = action(get_string('fitWidth'), self.set_fit_width, 'Ctrl+Shift+F',
                                  'fit-width', get_string('fitWidthDetail'), checkable=True, enabled=False)

        # Auto saving : Enable auto saving if pressing next
        self.auto_saving_option = action(get_string('autoSaveMode'), None, None, None, None,
                                         checkable=True)

        # Add option to enable/disable labels being displayed at the top of bounding boxes
        self.display_label_option = action(get_string('displayLabel'), self.toggle_display_label,
                                           'Ctrl+Shift+P', None, None, checkable=True)

        # Draw squares/rectangles
        self.draw_squares_option = action('Draw Squares', self.toogle_draw_square, 'Ctrl+Shift+R',
                                          None, None, checkable=True)

        # Store actions for further handling.
        self.actions = struct(save_label_list=save_label_list_action,
                              save_dataset=save_dataset_action,
                              export_canvas=export_canvas_action,
                              reset_all=reset_all_action,
                              create=create_shape_action,
                              delete=delete_shape_action,
                              copy=copy_shape_action,
                              fit_window=fit_window_action,
                              fit_width=fit_width_action,
                              zoom_actions=(self.zoom_widget,
                                            zoom_in_action,
                                            zoom_out_action,
                                            zoom_original_action,
                                            fit_window_action,
                                            fit_width_action))

        # endregion

        # region second_category List
        self.second_category_list_table = QTableView()
        self.second_category_list_table.setModel(SecondCategoryListTableModel())
        # endregion

        # region third_category List
        self.third_category_list_table = QTableView()
        self.third_category_list_table.setModel(ThirdCategoryListTableModel())
        # endregion

        # region Category List
        self.category_list_table = QTableView()
        self.category_list_table.setModel(CategoryListTableModel())
        # endregion

        attribute_list_layout = QHBoxLayout()
        attribute_list_layout.setContentsMargins(0, 0, 0, 0)

        attribute_list_layout.addWidget(self.category_list_table)
        attribute_list_layout.addWidget(self.second_category_list_table)
        attribute_list_layout.addWidget(self.third_category_list_table)

        attribute_list_container = QWidget()
        attribute_list_container.setLayout(attribute_list_layout)

        attribute_list_dock = QDockWidget('Attributes', self)
        attribute_list_dock.setWidget(attribute_list_container)
        attribute_list_dock.setFeatures(QDockWidget.DockWidgetFloatable)

        self.addDockWidget(Qt.RightDockWidgetArea, attribute_list_dock)

        # region Label List
        label_list_layout = QVBoxLayout()
        label_list_layout.setContentsMargins(0, 0, 0, 0)

        # Create and add a widget for showing current label items
        label_list_model = LabelListTableModel()
        label_list_model.dataChanged.connect(self.on_label_list_table_item_data_changed)
        self.label_list_table = QTableView()
        self.label_list_table.setModel(label_list_model)
        self.label_list_table.selectionModel().selectionChanged.connect(self.label_list_table_item_selection_changed)
        self.label_list_table.setContextMenuPolicy(Qt.CustomContextMenu)

        header = self.label_list_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)

        label_list_container = QWidget()
        label_list_container.setLayout(label_list_layout)
        label_list_layout.addWidget(self.label_list_table)

        label_list_dock = QDockWidget(get_string('labels'), self)
        label_list_dock.setWidget(label_list_container)
        label_list_dock.setFeatures(QDockWidget.DockWidgetFloatable)

        self.addDockWidget(Qt.RightDockWidgetArea, label_list_dock)

        # endregion

        # region File List
        file_list_table_model = FileListTableModel()
        file_list_table_model.dataChanged.connect(self.on_file_list_table_item_data_changed)
        self.file_list_table = QTableView()
        self.file_list_table.setModel(file_list_table_model)
        self.file_list_table.doubleClicked.connect(self.on_file_list_table_item_double_clicked)
        self.file_list_table.setContextMenuPolicy(Qt.CustomContextMenu)

        # Create and add a widget for showing current file items
        file_list_layout = QVBoxLayout()
        file_list_layout.setContentsMargins(0, 0, 0, 0)
        file_list_layout.addWidget(self.file_list_table)

        file_list_container = QWidget()
        file_list_container.setLayout(file_list_layout)

        file_list_dock = QDockWidget(get_string('fileList'), self)
        file_list_dock.setWidget(file_list_container)
        file_list_dock.setFeatures(QDockWidget.DockWidgetFloatable)

        self.addDockWidget(Qt.RightDockWidgetArea, file_list_dock)
        # endregion

        # region Canvas

        self.canvas = Canvas(parent=self)
        self.canvas.zoom_request.connect(self.zoom_request)
        self.canvas.scroll_request.connect(self.scroll_request)
        self.canvas.new_shape.connect(self.new_shape)
        self.canvas.shape_moved.connect(self.set_dirty)
        self.canvas.selection_changed.connect(self.shape_selection_changed)
        self.canvas.drawingPolygon.connect(self.toggle_drawing_sensitive)

        # endregion

        # region Scroll
        scroll = QScrollArea()
        scroll.setWidget(self.canvas)
        scroll.setWidgetResizable(True)
        self.scroll_bars = {
            Qt.Vertical: scroll.verticalScrollBar(),
            Qt.Horizontal: scroll.horizontalScrollBar()
        }
        self.scroll_area = scroll
        self.setCentralWidget(scroll)
        # endregion

        # region Main Menus
        add_actions(self.menu('&File'), (open_category_file_action,
                                         open_second_category_file_action,
                                         open_third_category_file_action,
                                         open_image_dataset_action,
                                         # filter_dataset_action,
                                         save_label_list_action,
                                         save_dataset_action,
                                         export_canvas_action,
                                         reset_all_action,
                                         quit_action))

        add_actions(self.menu('&Edit'), (create_shape_action,
                                         copy_shape_action,
                                         delete_shape_action,
                                         None,
                                         change_line_thickness_action,
                                         change_font_size_action,
                                         choose_color_action,
                                         self.draw_squares_option))

        add_actions(self.menu('&View'), (self.auto_saving_option,
                                         self.display_label_option,
                                         None,
                                         zoom_in_action,
                                         zoom_out_action,
                                         zoom_original_action,
                                         None,
                                         fit_window_action,
                                         fit_width_action))

        add_actions(self.menu('&Help'), (help_action,
                                         show_action))
        # endregion

        # region Canvas Menus
        add_actions(self.canvas.menus[0], (create_shape_action,
                                           copy_shape_action,
                                           delete_shape_action))
        # endregion

        # region toolbox

        self.tools = self.toolbar('Tools')

        add_actions(self.tools, (open_category_file_action,
                                 open_second_category_file_action,
                                 open_third_category_file_action,
                                 open_image_dataset_action,
                                 # filter_dataset_action,
                                 None,
                                 open_next_image_action,
                                 open_previous_image_action,
                                 save_label_list_action,
                                 save_dataset_action,
                                 export_canvas_action,
                                 None,
                                 create_shape_action,
                                 copy_shape_action,
                                 delete_shape_action,
                                 None,
                                 zoom_in_action,
                                 zoom_action,
                                 zoom_out_action,
                                 fit_window_action,
                                 fit_width_action))

        # endregion

        # region Settings
        self.settings = None
        self.load_settings()
        # endregion

        # region Status Bar
        self.statusBar().showMessage('%s started.' % __appname__)
        self.statusBar().show()
        self.statusBar().addPermanentWidget(self.label_coordinates)
        # endregion

    # region UI
    def menu(self, title, actions=None):
        menu = self.menuBar().addMenu(title)
        if actions:
            add_actions(menu, actions)
        return menu

    def toolbar(self, title, actions=None):
        toolbar = ToolBar(title)
        toolbar.setObjectName(u'%sToolBar' % title)
        toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        if actions:
            add_actions(toolbar, actions)
        self.addToolBar(Qt.LeftToolBarArea, toolbar)
        return toolbar

    # endregion

    # region help

    def show_tutorial_dialog(self):
        self.information_message('This function haven\'t been supported')

    def show_info_dialog(self):
        msg = u'{0} \nApp Version:{1} \nAuthor: {2}'.format(__appname__, __version__, __author__)
        self.information_message(msg)

    # endregion

    def load_settings(self):
        self.settings = Settings()
        self.settings.load()
        settings = self.settings
        # Canvas and Shape
        Shape.line_color = self.line_color = QColor(settings.get(SETTING_LINE_COLOR,
                                                                 DEFAULT_LINE_COLOR))
        Shape.fill_color = self.fill_color = QColor(settings.get(SETTING_FILL_COLOR,
                                                                 DEFAULT_FILL_COLOR))
        self.canvas.setDrawingShapeToSquare(settings.get(SETTING_DRAW_SQUARE,
                                                         False))
        self.canvas.line_thickness = settings.get(SETTING_LINE_THICKNESS,
                                                  DEFAULT_LINE_THICKNESS)
        self.canvas.font_size = settings.get(SETTING_FONT_SIZE,
                                             DEFAULT_FONT_SIZE)
        self.canvas.setDrawingColor(self.line_color)

        # Window
        size = settings.get(SETTING_WIN_SIZE, QSize(600, 500))
        position = QPoint(0, 0)
        self.resize(size)
        self.move(position)

        # Label
        self.display_label_option.setChecked(settings.get(SETTING_PAINT_LABEL,
                                                          False))

        # Auto Saving
        self.auto_saving_option.setChecked(settings.get(SETTING_AUTO_SAVE,
                                                        False))

        # Draw square
        self.draw_squares_option.setChecked(settings.get(SETTING_DRAW_SQUARE,
                                                         False))

    def no_shapes(self):
        return not self.uid_to_shapes_dict

    def set_dirty(self):
        self.dirty = True
        self.actions.save_label_list.setEnabled(True)

    # region app state

    def set_clean(self):
        self.dirty = False
        self.actions.save_label_list.setEnabled(False)
        self.actions.create.setEnabled(True)
        self.actions.export_canvas.setEnabled(True)

    def may_continue(self):
        if not self.dirty:
            return True
        yes, no = QMessageBox.Yes, QMessageBox.No
        msg = u'You have unsaved changes, proceed anyway?'
        return yes == QMessageBox.warning(self, __appname__, msg, yes | no)

    # endregion

    def toggle_actions(self, value=True):
        """Enable/Disable widgets which depend on an opened image."""
        for z in self.actions.zoom_actions:
            z.setEnabled(value)
        self.actions.create.setEnabled(value)

    def status(self, message, delay=5000):
        self.statusBar().showMessage(message, delay)

    def reset_state(self):
        self.label_list_table.model().clear()
        self.shapes_to_uids_dict.clear()
        self.uid_to_shapes_dict.clear()
        self.canvas.resetState()
        self.label_coordinates.clear()

    ## Callbacks ##

    # Callback functions:

    def togglePolygons(self, value):
        self.label_list_table.model().toggle_visible_all(value)

    def reset_all(self):
        self.settings.reset()
        self.load_settings()
        self.reset_state()

        self.names_to_categories_dict.clear()
        self.category_ids_to_names_dict.clear()
        self.category_list_table.model().clear()

        self.names_to_second_categories_dict.clear()
        self.second_category_ids_to_names_dict.clear()
        self.second_category_names.clear()

        self.names_to_third_categories_dict.clear()
        self.third_category_ids_to_names_dict.clear()
        self.third_category_names.clear()

        self.image_file_path = None
        self.current_index = -1
        self.current_image = None
        self.category_names = []
        self.image_paths = []
        self.images_dict = {}
        self.file_list_table.model().clear()

    # region Override Qt Events
    def resizeEvent(self, event):
        if self.canvas and not self.image.isNull() and self.zoom_mode != self.MANUAL_ZOOM:
            self.adjust_scale()
        super(MainWindow, self).resizeEvent(event)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Control:
            self.canvas.setDrawingShapeToSquare(False)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Control:
            # Draw rectangle if Ctrl is pressed
            self.canvas.setDrawingShapeToSquare(True)

    def closeEvent(self, event):
        if self.auto_saving_option.isChecked() and self.dirty:
            self.save_label_list()
        if self.auto_saving_option.isChecked():
            self.save_dataset()

        if not self.may_continue():
            event.ignore()

        # Save settings
        settings = self.settings
        settings[SETTING_WIN_SIZE] = self.size()
        settings[SETTING_LINE_COLOR] = self.line_color
        settings[SETTING_FILL_COLOR] = self.fill_color
        settings[SETTING_AUTO_SAVE] = self.auto_saving_option.isChecked()
        settings[SETTING_PAINT_LABEL] = self.display_label_option.isChecked()
        settings[SETTING_DRAW_SQUARE] = self.draw_squares_option.isChecked()
        settings[SETTING_LINE_THICKNESS] = self.canvas.line_thickness
        settings[SETTING_FONT_SIZE] = self.canvas.font_size
        settings.save()

    # endregion

    # region Settings

    def choose_color(self):
        color_dialog = ColorDialog(parent=self)
        color = color_dialog.getColor(self.line_color, u'Choose line color',
                                      default=DEFAULT_LINE_COLOR)
        if not color:
            return

        self.line_color = color
        Shape.line_color = color
        self.canvas.setDrawingColor(color)
        self.canvas.update()

    def change_line_thickness(self):
        value, ok_pressed = QInputDialog.getInt(self, 'Change line thickness',
                                                'Thickness value:',
                                                self.canvas.line_thickness, 0, 100, 1)
        if not ok_pressed:
            return
        self.canvas.line_thickness = value
        self.canvas.update()

    def change_font_size(self):
        value, ok_pressed = QInputDialog.getInt(self, 'Change font size',
                                                'Font size value:',
                                                self.canvas.font_size, 0, 100, 1)
        if not ok_pressed:
            return
        self.canvas.font_size = value
        self.canvas.update()

    # endregion

    # region Zoom and Scale
    def set_zoom(self, value):
        self.actions.fit_width.setChecked(False)
        self.actions.fit_window.setChecked(False)
        self.zoom_mode = self.MANUAL_ZOOM
        self.zoom_widget.setValue(value)

    def add_zoom(self, increment=10):
        self.set_zoom(self.zoom_widget.value() + increment)

    def set_fit_window(self, value=True):
        if value:
            self.actions.fit_width.setChecked(False)
        self.zoom_mode = self.FIT_WINDOW if value else self.MANUAL_ZOOM
        self.adjust_scale()

    def set_fit_width(self, value=True):
        if value:
            self.actions.fit_window.setChecked(False)
        self.zoom_mode = self.FIT_WIDTH if value else self.MANUAL_ZOOM
        self.adjust_scale()

    def adjust_scale(self, initial=False):
        value = self.scalers[self.FIT_WINDOW if initial else self.zoom_mode]()
        self.zoom_widget.setValue(int(100 * value))

    def scale_fit_window(self):
        """Figure out the size of the pixmap in order to fit the main widget."""
        e = 2.0  # So that no scrollbars are generated.
        w1 = self.centralWidget().width() - e
        h1 = self.centralWidget().height() - e
        a1 = w1 / h1
        # Calculate a new scale value based on the pixmap's aspect ratio.
        w2 = self.canvas.pixmap.width() - 0.0
        h2 = self.canvas.pixmap.height() - 0.0
        a2 = w2 / h2
        return w1 / w2 if a2 >= a1 else h1 / h2

    def scale_fit_width(self):
        # The epsilon does not seem to work too well here.
        w = self.centralWidget().width() - 2.0
        return w / self.canvas.pixmap.width()

    # endregion

    # region Canvas and Shape
    def zoom_request(self, delta):
        # get the current scrollbar positions
        # calculate the percentages ~ coordinates
        h_bar = self.scroll_bars[Qt.Horizontal]
        v_bar = self.scroll_bars[Qt.Vertical]

        # get the current maximum, to know the difference after zoom_in_actiong
        h_bar_max = h_bar.maximum()
        v_bar_max = v_bar.maximum()

        # get the cursor position and canvas size
        # calculate the desired movement from 0 to 1
        # where 0 = move left
        #       1 = move right
        # up and down analogous
        cursor = QCursor()
        pos = cursor.pos()
        relative_pos = QWidget.mapFromGlobal(self, pos)

        cursor_x = relative_pos.x()
        cursor_y = relative_pos.y()

        w = self.scroll_area.width()
        h = self.scroll_area.height()

        # the scaling from 0 to 1 has some padding
        # you don't have to hit the very leftmost pixel for a maximum-left movement
        margin = 0.1
        move_x = (cursor_x - margin * w) / (w - 2 * margin * w)
        move_y = (cursor_y - margin * h) / (h - 2 * margin * h)

        # clamp the values from 0 to 1
        move_x = min(max(move_x, 0), 1)
        move_y = min(max(move_y, 0), 1)

        # zoom in
        units = delta / (8 * 15)
        scale = 10
        self.add_zoom(scale * units)

        # get the difference in scrollbar values
        # this is how far we can move
        d_h_bar_max = h_bar.maximum() - h_bar_max
        d_v_bar_max = v_bar.maximum() - v_bar_max

        # get the new scrollbar values
        new_h_bar_value = h_bar.value() + move_x * d_h_bar_max
        new_v_bar_value = v_bar.value() + move_y * d_v_bar_max

        h_bar.setValue(new_h_bar_value)
        v_bar.setValue(new_v_bar_value)

    def scroll_request(self, delta, orientation):
        units = - delta / (8 * 15)
        bar = self.scroll_bars[orientation]
        bar.setValue(bar.value() + bar.singleStep() * units)

    def generate_color(self, text):
        if len(self.names_to_categories_dict) > 0:
            id = self.names_to_categories_dict[text]['id']
            if id > np.max(list(self.palette.keys())):
                return generate_color_by_text(text)
            else:
                return QColor(self.palette[id][0], self.palette[id][1], self.palette[id][2], 200)
        else:
            return generate_color_by_text(text)

    def new_shape(self):
        text = None

        if len(self.category_names) > 0:
            choose_category_dialog = ChooseCategoryDialog(parent=self,
                                                          category_names=self.category_names)
            text = choose_category_dialog.popUp()

        # Add Chris
        if text:
            # generate_color = generate_color_by_text(text)
            generate_color = self.generate_color(text)
            shape = self.canvas.set_last_label(generate_color,
                                               generate_color)
            shape.category = text

            self.add_label(shape)
            self.canvas.setEditing(True)
            self.actions.create.setEnabled(True)
            self.set_dirty()
        else:
            self.canvas.resetAllLines()

    # def copy_shape(self):
    #     self.canvas.endMove(copy=True)
    #     self.add_label(self.canvas.selectedShape)
    #     self.set_dirty()

    def copy_selected_shape(self):

        shape = self.canvas.copySelectedShape()
        if not shape:
            return
        shape_data = self.label_list_table.model().get_data(self.current_uid)
        self.add_label(shape, id=shape_data['id'], track_id=shape_data['track_id'],
                       trackable=shape_data['trackable'], second_category=shape_data['second_category'], third_category=shape_data['third_category'])
        self.shape_selection_changed(True)

    def delete_selected_shape(self):
        self.remove_label(self.canvas.deleteSelected())
        self.set_dirty()
        if not self.no_shapes():
            return

    # def move_shape(self):
    #     self.canvas.endMove(copy=False)
    #     self.set_dirty()

    def paint_canvas(self):
        assert not self.image.isNull(), "cannot paint null image"
        self.canvas.scale = 0.01 * self.zoom_widget.value()
        self.canvas.adjustSize()
        self.canvas.update()

    def shape_selection_changed(self, selected=False):
        if self._noSelectionSlot:
            self._noSelectionSlot = False
        self.actions.delete.setEnabled(selected)
        self.actions.copy.setEnabled(selected)

        shape = self.canvas.selectedShape
        if not shape:
            return

        self.current_uid = self.shapes_to_uids_dict[shape]
        row = self.label_list_table.model().get_row(self.current_uid)
        self.label_list_table.model().setCurrentRow(row)

    def create_shape(self):
        self.canvas.setEditing(False)
        self.actions.create.setEnabled(False)

    def toggle_drawing_sensitive(self, drawing=True):
        if drawing:
            return

        self.canvas.setEditing(True)
        self.canvas.restoreCursor()
        self.actions.create.setEnabled(True)

    def toogle_draw_square(self):
        self.canvas.setDrawingShapeToSquare(
            self.draw_squares_option.isChecked())

    # endregion

    # region Labels
    def add_label(self, shape, id=-1, track_id=-1, trackable=True, second_category=None, third_category=None):
        shape.paintLabel = self.display_label_option.isChecked()

        uid = str(uuid.uuid4())
        self.uid_to_shapes_dict[uid] = shape
        self.shapes_to_uids_dict[shape] = uid

        category = self.names_to_categories_dict[shape.category]

        if second_category is None and len(self.second_category_names) > 0:
            second_category = self.second_category_names[0]
            for second_category_name in self.second_category_names:
                if self.names_to_second_categories_dict[second_category_name]["supercategory"] == 'all' or \
                        self.names_to_second_categories_dict[second_category_name]["supercategory"] == category['name'] or \
                        self.names_to_second_categories_dict[second_category_name]["supercategory"] == category['supercategory']:
                    second_category = second_category_name
                    break

        if third_category is None and len(self.third_category_names) > 0:
            third_category = self.third_category_names[0]
            for third_category_name in self.third_category_names:
                if self.names_to_third_categories_dict[third_category_name]["supercategory"] == 'all' or \
                        self.names_to_third_categories_dict[third_category_name]["supercategory"] == category['name'] or \
                        self.names_to_third_categories_dict[third_category_name]["supercategory"] == category['supercategory']:
                    third_category = third_category_name
                    break

        self.label_list_table.model().append(uid, shape.category, id, track_id, trackable=trackable, second_category=second_category,
                                             third_category=third_category)

    def remove_label(self, shape):
        if shape is None:
            return
        uid = self.shapes_to_uids_dict[shape]
        self.label_list_table.model().remove_row(uid)
        del self.shapes_to_uids_dict[shape]
        del self.uid_to_shapes_dict[uid]

    def toggle_display_label(self):
        for shape in self.canvas.shapes:
            shape.paintLabel = self.display_label_option.isChecked()

    # endregion

    # region Open data

    def open_category_file(self):
        formats = ['*.json']
        filters = 'Category files (%s)' % ' '.join(formats)
        file_name = QFileDialog.getOpenFileName(self,
                                                '%s - Choose Json file' % __appname__, '.', filters)
        data = {}
        try:
            if isinstance(file_name, (list, tuple)):
                file_name = file_name[0]
            with open(file_name) as f:
                data = json.load(f)
        except Exception as e:
            self.error_message(
                u'<p><b>%s</b></p><p>Make sure <i>%s</i> is a valid json file.' % (e, file_name))
            self.status('Error reading %s' % file_name)
            return

        if not self.may_continue():
            return

        if self.current_image is not None:
            self.reset_state()

        if 'category' not in data:
            self.error_message('Invalid category file.')
            return

        # type = data['category'][0]['type']
        #
        # if type == 'second_category':
        #     self.set_second_category(data)
        # elif type == 'third_category':
        #     self.set_third_category(data)
        # else:
        #     self.set_category(data)

        self.set_category(data)

        self.information_message(
            'Open file <i>%s</i> successfully.' % file_name)

        if self.image_file_path:
            self.open_image_file(self.current_index, self.image_file_path)

    def open_second_category_file(self):
        formats = ['*.json']
        filters = 'Category files (%s)' % ' '.join(formats)
        file_name = QFileDialog.getOpenFileName(self,
                                                '%s - Choose Json file' % __appname__, '.', filters)
        data = {}
        try:
            if isinstance(file_name, (list, tuple)):
                file_name = file_name[0]
            with open(file_name) as f:
                data = json.load(f)
        except Exception as e:
            self.error_message(
                u'<p><b>%s</b></p><p>Make sure <i>%s</i> is a valid json file.' % (e, file_name))
            self.status('Error reading %s' % file_name)
            return

        if not self.may_continue():
            return

        if self.current_image is not None:
            self.reset_state()

        if 'category' not in data:
            self.error_message('Invalid category file.')
            return

        # type = data['category'][0]['type']
        #
        # if type == 'second_category':
        #     self.set_second_category(data)
        # elif type == 'third_category':
        #     self.set_third_category(data)
        # else:
        #     self.set_category(data)

        self.set_second_category(data)

        self.information_message(
            'Open file <i>%s</i> successfully.' % file_name)

        if self.image_file_path:
            self.open_image_file(self.current_index, self.image_file_path)

    def open_third_category_file(self):
        formats = ['*.json']
        filters = 'Category files (%s)' % ' '.join(formats)
        file_name = QFileDialog.getOpenFileName(self,
                                                '%s - Choose Json file' % __appname__, '.', filters)
        data = {}
        try:
            if isinstance(file_name, (list, tuple)):
                file_name = file_name[0]
            with open(file_name) as f:
                data = json.load(f)
        except Exception as e:
            self.error_message(
                u'<p><b>%s</b></p><p>Make sure <i>%s</i> is a valid json file.' % (e, file_name))
            self.status('Error reading %s' % file_name)
            return

        if not self.may_continue():
            return

        if self.current_image is not None:
            self.reset_state()

        if 'category' not in data:
            self.error_message('Invalid category file.')
            return

        # type = data['category'][0]['type']
        #
        # if type == 'second_category':
        #     self.set_second_category(data)
        # elif type == 'third_category':
        #     self.set_third_category(data)
        # else:
        #     self.set_category(data)

        self.set_third_category(data)

        self.information_message(
            'Open file <i>%s</i> successfully.' % file_name)

        if self.image_file_path:
            self.open_image_file(self.current_index, self.image_file_path)

    def set_category(self, data):
        self.category_set_name = data['name']

        self.category_names = []

        self.names_to_categories_dict.clear()
        self.category_ids_to_names_dict.clear()
        self.category_list_table.model().clear()
        for c in data['category']:
            if c['name'] in self.names_to_categories_dict:
                continue
            self.names_to_categories_dict[c['name']] = c
            self.category_ids_to_names_dict[c['id']] = c['name']
            self.category_names.append(c['name'])
            self.category_list_table.model().append(c['id'], c['name'])

        self.label_list_table.setItemDelegateForColumn(
            4, LabelListTableComboBoxDelegate(self, self.category_names))

    def set_second_category(self, data):
        if not self.category_set_name:
            self.category_set_name = data['name']

        self.second_category_names = []

        self.names_to_second_categories_dict.clear()
        self.second_category_ids_to_names_dict.clear()
        self.second_category_names.clear()

        for c in data['category']:
            if c['name'] in self.names_to_second_categories_dict:
                continue
            self.names_to_second_categories_dict[c['name']] = c
            self.second_category_ids_to_names_dict[c['id']] = c['name']
            self.second_category_names.append(c['name'])
            self.second_category_list_table.model().append(c['id'], c['name'])

        self.label_list_table.setItemDelegateForColumn(
            5, LabelListTableComboBoxDelegate(self, self.second_category_names))

    def set_third_category(self, data):
        if not self.category_set_name:
            self.category_set_name = data['name']

        self.third_category_names = []

        self.names_to_third_categories_dict.clear()
        self.third_category_ids_to_names_dict.clear()
        self.third_category_names.clear()

        for c in data['category']:
            if c['name'] in self.names_to_third_categories_dict:
                continue
            self.names_to_third_categories_dict[c['name']] = c
            self.third_category_ids_to_names_dict[c['id']] = c['name']
            self.third_category_names.append(c['name'])
            self.third_category_list_table.model().append(c['id'], c['name'])

        self.label_list_table.setItemDelegateForColumn(
            6, LabelListTableComboBoxDelegate(self, self.third_category_names))

    def filter_dataset_dialog(self):
        if self.image_file_path is not None:
            path = self.image_file_path
        else:
            path = '.'

        dirpath = QFileDialog.getExistingDirectory(self, 'Open video directory ', path,
                                                   QFileDialog.ShowDirsOnly
                                                   | QFileDialog.DontResolveSymlinks)
        dirpath = dirpath.replace('\\', '/')
        idx_keep = []
        idx_remove = []
        for idx, path in enumerate(self.image_paths):
            dirname = os.path.dirname(path)
            dirname = dirname.replace('\\', '/')
            if dirname == dirpath:
                idx_keep.append(idx)
            else:
                idx_remove.append(idx)

        # clear canvas here
        self.label_list_table.model().clear()
        self.reset_state()

        self.current_image = None
        self.image_file_path = None
        self.image_paths_temp = self.image_paths
        self.image_paths = []
        self.file_list_table.model().clear()

        self.images_dict_temp = self.images_dict
        self.images_dict = {}
        if len(idx_keep) == 0:
            self.image_paths = []
            self.file_list_table.model().clear()
            self.images_dict = {}
        else:
            for idx in idx_keep:
                path = self.image_paths_temp[idx]

                # self.images_dict.append(self.images_dict_temp[path])

                self.images_dict[path] = self.images_dict_temp[path]
                image_dict = self.images_dict[path]

                self.images_dict[path]['index'] = len(self.image_paths)
                self.image_paths.append(path)

                self.file_list_table.model().append(
                    image_dict['id'], image_dict['has_gt'], image_dict['file_name'])
            self.open_next_image()

        self.dataset_info_path = os.path.dirname(self.dataset_info_path)
        if not os.path.exists(self.dataset_info_path):
            os.makedirs(self.dataset_info_path)
        self.dataset_info_path = os.path.join(self.dataset_info_path, os.path.basename(dirpath) + '.json')

    def open_dataset_file(self):
        if not self.may_continue():
            return

        path = os.path.dirname(str(self.image_file_path)
                               ) if self.image_file_path else '.'
        formats = ['*.json']
        filters = 'Video dataset files (%s)' % ' '.join(formats)
        file_name = QFileDialog.getOpenFileName(self,
                                                '%s - Choose Json file' % __appname__,
                                                path, filters)
        if not file_name:
            return

        data = {}
        try:
            if isinstance(file_name, (list, tuple)):
                file_name = file_name[0]
            with open(file_name) as f:
                data = json.load(f)
        except Exception as e:
            self.error_message(
                u'<p><b>%s</b></p><p>Make sure <i>%s</i> is a valid json file.' % (e, file_name))
            self.status('Error reading %s' % file_name)
            return

        if not ('info' in data and 'root_dir' in data['info']):
            self.error_message('Invalid dataset file.')
            return

        dataset_info_path = file_name
        self.data = data

        root_directory_path = data['info']['root_dir']

        if not os.path.exists(root_directory_path):
            self.error_message('Dataset path is not exists.')
            return
        # clear canvas here
        self.shapes_to_uids_dict.clear()
        self.uid_to_shapes_dict.clear()
        self.canvas.resetState()
        self.label_coordinates.clear()

        root_directory_path = root_directory_path.replace('\\', '/')
        file_name = file_name.replace('\\', '/')
        temp_path = os.path.dirname(os.path.dirname(file_name))

        if temp_path != root_directory_path:
            root_directory_path = temp_path
            data['info']['root_dir'] = root_directory_path
            with open(file_name, 'w') as f:
                info = json.dumps(data)
                f.write(info)
                f.close()

        self.dataset_root_path = root_directory_path

        if 'images' not in data:
            self.error_message('Invalid dataset file.')
            return

        if 'videos' in data:
            self.video = data['videos']
        else:
            self.video = None

        self.image_paths = []
        self.images_dict = {}
        self.current_image = None
        self.image_file_path = None

        self.file_list_table.model().clear()

        for data_row in data['images']:
            path = os.path.join(root_directory_path, data_row['file_name'])
            if not os.path.exists(path):
                continue

            data_row['index'] = len(self.image_paths)
            self.images_dict[path] = data_row
            self.image_paths.append(path)

            self.file_list_table.model().append(self.images_dict[path]['id'],
                                                self.images_dict[path]['has_gt'],
                                                self.images_dict[path]['file_name'])

        self.information_message(
            'Open dataset file <i>%s</i> successfully.' % file_name)

        self.dataset_info_path = dataset_info_path
        self.actions.save_dataset.setEnabled(True)
        self.open_next_image()

    def open_image_file(self, current_index, file_path=None):
        """Load the specified file, or the last opened file if None."""
        self.reset_state()
        self.image_file_path = None
        self.current_image = None
        self.canvas.setEnabled(False)

        if file_path is None:
            return False

        if not (file_path and os.path.exists(file_path)):
            return False

        index = self.file_list_table.model().index(current_index, 0)
        self.file_list_table.model().setCurrentRow(current_index)
        self.current_index = current_index

        image_data = read(file_path, None)
        self.canvas.verified = False

        image = QImage.fromData(image_data)
        if image.isNull():
            self.error_message(
                u'<p>Make sure <i>%s</i> is a valid image file.' % file_path)
            self.status('Error reading %s' % file_path)
            return False
        self.status('Loaded %s' % os.path.basename(file_path))
        self.image = image
        self.image_file_path = file_path
        self.current_image = self.images_dict[self.image_file_path]

        # clear data
        self.set_clean()

        # drawing
        self.canvas.loadPixmap(QPixmap.fromImage(image))
        self.paint_canvas()
        self.open_annotation_file()

        # focusing
        self.canvas.setEnabled(True)
        self.canvas.setFocus(True)
        self.adjust_scale(initial=True)

        # enable tools
        self.toggle_actions(True)

        return True

    def open_annotation_file(self):
        annotation_path = self.generate_annotation_path()
        if not (annotation_path and os.path.exists(annotation_path)):
            return

        data = {}
        with open(annotation_path) as in_file:
            data = json.load(in_file)

        if isinstance(data, dict):
            data = data.values()

        shapes = []
        for data_row in data:
            category = self.category_ids_to_names_dict[data_row['category_id']]
            if 'video_ins_id' in data_row.keys():
                data_row['track_id'] = data_row['video_ins_id']
            shape = Shape(category=category,
                          track_id=data_row['track_id'])
            if 'bbox' not in data_row:
                return

            bbox = data_row['bbox']
            x = bbox['x']
            y = bbox['y']
            x_max = x + bbox['w'] - 1
            y_max = y + bbox['h'] - 1

            shape.addPoint(QPointF(x, y))
            shape.addPoint(QPointF(x_max, y))
            shape.addPoint(QPointF(x_max, y_max))
            shape.addPoint(QPointF(x, y_max))
            shape.close()

            # color = generate_color_by_text(category)
            color = self.generate_color(category)
            shape.line_color = color
            shape.fill_color = color

            if 'second_category_id' not in data_row.keys() or len(self.second_category_names) == 0:
                second_category = None
            elif data_row['second_category_id'] is None:
                second_category = None
            else:
                second_category = self.second_category_ids_to_names_dict[data_row['second_category_id']]

            if 'third_category_id' not in data_row.keys() or len(self.third_category_names) == 0:
                third_category = None
            elif data_row['third_category_id'] is None:
                third_category = None
            else:
                third_category = self.third_category_ids_to_names_dict[data_row['third_category_id']]

            if 'trackable' not in data_row.keys():
                data_row['trackable'] = True

            self.add_label(shape,
                           id=data_row['id'],
                           track_id=data_row['track_id'],
                           trackable=data_row['trackable'],
                           second_category=second_category,
                           third_category=third_category)
            shapes.append(shape)

        self.canvas.load_shapes(shapes)

    # endregion

    # region Save data

    def save_label_list(self):
        if not self.category_set_name:
            self.error_message('Error: Category list may not be loaded.')
            return

        if not self.dataset_root_path:
            self.error_message('Error: Dataset may not be loaded.')
            return

        if not self.current_image:
            return

        annotation_path = self.generate_annotation_path()
        if not annotation_path:
            return

        result = []
        for s in self.label_list_table.model().table_data:
            uid = s['uid']
            shape = self.uid_to_shapes_dict[uid]
            x_min = y_min = sys.maxsize
            x_max = y_max = -sys.maxsize - 1
            for p in shape.points:
                x = p.x()
                y = p.y()
                x_min = min(x, x_min)
                y_min = min(y, y_min)
                x_max = max(x, x_max)
                y_max = max(y, y_max)

            if s['second_category'] is None:
                second_category = None
            else:
                second_category = self.names_to_second_categories_dict[s['second_category']]['id']

            if s['third_category'] is None:
                third_category = None
            else:
                third_category = self.names_to_third_categories_dict[s['third_category']]['id']

            result.append({
                'area': 0,
                'id': s['id'],
                'segmentation': [],
                'bbox': {
                    'x': x_min,
                    'y': y_min,
                    'w': x_max - x_min + 1,
                    'h': y_max - y_min + 1
                },
                'iscrowd': 0,
                'image_id': self.current_image['id'],
                'track_id': s['track_id'],
                'trackable': s['trackable'],
                'category_id': self.names_to_categories_dict[s['category']]['id'],
                'second_category_id': second_category,
                'third_category_id': third_category,
            })

        with open(annotation_path, 'w') as out_file:
            json.dump(result, out_file)

        self.set_clean()
        self.statusBar().showMessage('Saved to  %s' % annotation_path)
        self.statusBar().show()

    def save_dataset(self):
        # data = {}
        # with open(self.dataset_info_path, 'r') as f:
        #     data = json.load(f)

        if self.data is None:
            return

        data = self.data
        data['images'] = []
        for path in self.image_paths:
            image_dict = copy.deepcopy(self.images_dict[path])
            index = image_dict['index']
            del image_dict['index']
            has_gt = self.file_list_table.model().table_data[index]['has_gt']
            image_dict['has_gt'] = has_gt
            self.images_dict[path]['has_gt'] = has_gt
            data['images'].append(image_dict)
        with open(self.dataset_info_path, 'w') as out_file:
            json.dump(data, out_file)
        self.statusBar().showMessage('Saved to  %s' % self.dataset_info_path)
        self.statusBar().show()

    def export_canvas(self):
        if not self.category_set_name:
            self.error_message('Error: Category list may not be loaded.')
            return

        if not self.dataset_root_path:
            self.error_message('Error: Dataset may not be loaded.')
            return

        canvases_path = self.generate_canvas_path()

        if not self.current_image:
            return

        image_name, _ = os.path.splitext(
            os.path.basename(self.image_file_path))
        canvas_path = os.path.join(canvases_path, image_name + '.jpg')
        self.canvas.export_image(canvas_path)

        self.statusBar().showMessage('Saved to  %s' % canvas_path)
        self.statusBar().show()

    def generate_canvas_path(self):
        if not self.dataset_root_path:
            return None
        canvas_path = os.path.join(self.dataset_root_path, 'Canvases')
        if not os.path.exists(canvas_path):
            os.makedirs(canvas_path)
        if not self.category_set_name:
            return None
        canvas_path = os.path.join(canvas_path, self.category_set_name)
        if not os.path.exists(canvas_path):
            os.makedirs(canvas_path)
        video_name = None
        if self.video is not None:
            for video in self.video:
                if self.current_image['video_id'] == video['id']:
                    video_name = video['name']
                    break
        if video_name is not None:
            canvas_path = os.path.join(canvas_path, video_name)
            if not os.path.exists(canvas_path):
                os.makedirs(canvas_path)
        return canvas_path

    def generate_annotation_path(self):
        if not self.dataset_root_path:
            return None
        annotation_path = os.path.join(self.dataset_root_path, 'Annotations')
        if not os.path.exists(annotation_path):
            os.makedirs(annotation_path)
        if not self.category_set_name:
            return None
        annotation_path = os.path.join(annotation_path, self.category_set_name)
        if not os.path.exists(annotation_path):
            os.makedirs(annotation_path)
        video_name = None
        if self.video is not None:
            for video in self.video:
                if self.current_image['video_id'] == video['id']:
                    video_name = video['name']
                    break
        if video_name is not None:
            annotation_path = os.path.join(annotation_path, video_name)
            if not os.path.exists(annotation_path):
                os.makedirs(annotation_path)
        if not self.image_file_path:
            return None
        image_name, _ = os.path.splitext(
            os.path.basename(self.image_file_path))
        return os.path.join(annotation_path, image_name + '.json')

    # endregion

    # region Label List Table Events
    def label_list_table_item_selection_changed(self, selected, deselected):
        indexes = self.label_list_table.selectionModel().selectedIndexes()
        if len(indexes) == 0:
            return
        row = indexes[0].row()
        uid = self.label_list_table.model().table_data[row]['uid']
        shape = self.uid_to_shapes_dict[uid]
        self.canvas.selectShape(shape)

    def on_label_list_table_item_data_changed(self, row_index, column_index):
        row = row_index.row()
        column = column_index.column()
        cell_data = self.label_list_table.model().table_data[row]
        shape = self.uid_to_shapes_dict[cell_data['uid']]

        if column == 0:
            shape = self.uid_to_shapes_dict[cell_data['uid']]
            self.canvas.setShapeVisible(shape, cell_data['visible'])
        else:
            # shape.line_color = generate_color_by_text(cell_data['category'])
            shape.line_color = self.generate_color(cell_data['category'])
            shape.category = cell_data['category']
            shape.track_id = cell_data['track_id']
        self.set_dirty()

    # endregion

    # region File List Table Events

    def on_file_list_table_item_double_clicked(self):
        indexes = self.file_list_table.selectionModel().selectedIndexes()
        if len(indexes) == 0:
            return
        current_index = indexes[0].row()
        path = self.image_paths[current_index]
        if self.auto_saving_option.isChecked() and self.dirty:
            self.save_label_list()
        # if self.auto_saving_option.isChecked():
        #     self.save_dataset()
        if not self.may_continue():
            return
        self.open_image_file(current_index, path)

    def on_file_list_table_item_data_changed(self, row_index, column_index):
        if self.auto_saving_option.isChecked():
            self.save_dataset()
        # row = row_index.row()
        # column = column_index.column()
        # cell_data = self.file_list_table.model().table_data[row]
        # has_gt = cell_data['has_gt']
        # if has_gt:
        #     self.export_canvas()



    # endregion

    # region Navigations

    def open_previous_image(self):
        if self.auto_saving_option.isChecked() and self.dirty:
            self.save_label_list()
        # if self.auto_saving_option.isChecked():
        #     self.save_dataset()

        if not self.may_continue():
            return

        if len(self.image_paths) == 0:
            return

        file_path = None

        current_index = -1
        if self.image_file_path is None:
            file_path = self.image_paths[0]
            current_index = 0
        else:
            current_index = self.images_dict[self.image_file_path]['index'] - 1
            if current_index >= 0:
                file_path = self.image_paths[current_index]

        if file_path:
            self.open_image_file(current_index, file_path)

    def open_next_image(self):
        if self.auto_saving_option.isChecked() and self.dirty:
            self.save_label_list()
        # if self.auto_saving_option.isChecked():
        #     self.save_dataset()

        if not self.may_continue():
            return

        if len(self.image_paths) == 0:
            return

        file_path = None

        current_index = -1
        if self.image_file_path is None:
            file_path = self.image_paths[0]
            current_index = 0
        else:
            current_index = self.images_dict[self.image_file_path]['index'] + 1
            if current_index < len(self.image_paths):
                file_path = self.image_paths[current_index]

        if file_path:
            self.open_image_file(current_index, file_path)

    # endregion

    # region Messages

    def error_message(self, message):
        return QMessageBox.critical(self, __appname__, message)

    def information_message(self, message):
        return QMessageBox.information(self, __appname__, message)

    # endregion


def get_main_app(argv=[]):
    """
    Standard boilerplate Qt application code.
    Do everything but app.exec_() -- so that we can test the application in one thread
    """
    app = QApplication(argv)
    app.setApplicationName(__appname__)
    app.setWindowIcon(new_icon("app"))
    win = MainWindow()
    win.show()
    return app, win


def main():
    '''construct main app and run it'''
    app, _win = get_main_app(sys.argv)
    return app.exec_()


if __name__ == '__main__':
    sys.exit(main())
