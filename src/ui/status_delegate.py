from PyQt5.QtWidgets import QStyledItemDelegate
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtCore import Qt


class StatusDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)

        option.displayAlignment = Qt.AlignHCenter | Qt.AlignVCenter
        value = index.data()

        if value is not None:
            status = str(value).lower()
            option.text = str(value)

            if status == "running":
                option.backgroundBrush = QBrush(QColor("#50fa7b"))
                option.palette.setColor(option.palette.Text, QColor("#282a36"))
            elif status == "stopped":
                option.backgroundBrush = QBrush(QColor("#ff5555"))
                option.palette.setColor(option.palette.Text, QColor("#f8f8f2"))
        else:
            option.text = ""
