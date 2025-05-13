from PyQt5.QtCore import QAbstractTableModel, Qt, QVariant


class ImageTableModel(QAbstractTableModel):
    def __init__(self, headers, data):
        super().__init__()
        self.headers = headers
        self.data_list = data

    def rowCount(self, parent=None):
        return len(self.data_list)

    def columnCount(self, parent=None):
        return len(self.headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()

        if role == Qt.DisplayRole:
            return str(self.data_list[index.row()][index.column()])

        return QVariant()

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return QVariant()

        if orientation == Qt.Horizontal:
            return self.headers[section]
        else:
            return str(section + 1)

    def get_image_name(self, row):
        """Retorna o nome da imagem (coluna 'Name') da linha especificada"""
        if 0 <= row < len(self.data_list):
            try:
                col_index = self.headers.index('Repository')  # ou 'Imagem', conforme o nome correto
                return self.data_list[row][col_index]
            except ValueError:
                return None
        return None

    def get_image_id(self, row):
        """Retorna o ID da imagem (coluna 'ID') da linha especificada"""
        if 0 <= row < len(self.data_list):
            try:
                col_index = self.headers.index('ID')
                return self.data_list[row][col_index]
            except ValueError:
                return None
        return None
