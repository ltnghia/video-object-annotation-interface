from PyQt5.QtGui import *

# region Setting keys
SETTING_WIN_SIZE = 'window/size'
SETTING_WIN_POSE = 'window/position'
SETTING_WIN_GEOMETRY = 'window/geometry'
SETTING_LINE_COLOR = 'line/color'
SETTING_FILL_COLOR = 'fill/color'
SETTING_LINE_THICKNESS = 'draw/lineThickness'
SETTING_ADVANCE_MODE = 'advanced'
SETTING_PAINT_LABEL = 'paintlabel'
SETTING_AUTO_SAVE = 'autosave'
SETTING_SINGLE_CLASS = 'singleclass'
SETTING_DRAW_SQUARE = 'draw/square'
SETTING_FONT_SIZE = 'draw/fontSize'
# endregion

# region default values
DEFAULT_LINE_COLOR = QColor(0, 255, 0, 128)
DEFAULT_FILL_COLOR = QColor(255, 0, 0, 128)
DEFAULT_SELECT_LINE_COLOR = QColor(255, 255, 255)
DEFAULT_SELECT_FILL_COLOR = QColor(0, 128, 255, 155)
DEFAULT_VERTEX_FILL_COLOR = QColor(0, 255, 0, 255)
DEFAULT_HVERTEX_FILL_COLOR = QColor(255, 0, 0)
DEFAULT_LINE_THICKNESS = 1
DEFAULT_FONT_SIZE = 10
# endregion
