from PyQt5.QtCore import Qt, QAbstractTableModel


class ContainerTableModel(QAbstractTableModel):
    def __init__(self, headers, data):
        super().__init__()
        self.headers = headers
        self.data = data

    def rowCount(self, parent=None):
        return len(self.data)

    def columnCount(self, parent=None):
        return len(self.headers)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            row = self.data[index.row()]
            col = self.headers[index.column()]
            return row.get(col, '')
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]
        return None