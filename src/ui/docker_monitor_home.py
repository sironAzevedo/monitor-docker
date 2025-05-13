from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QTableView
)

from src.models.container_table_model import ContainerTableModel
from src.models.image_table_model import ImageTableModel
from src.services.docker_utils import DockerUtils


class DockerMonitorHome(QWidget):
    def __init__(self, docker_utils: DockerUtils):
        super().__init__()
        self.setWindowTitle("Docker Monitor")
        self.resize(1000, 600)

        layout = QVBoxLayout()
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.docker_utils = docker_utils

        self.init_container_tab()
        self.init_images_tab()

        self.setLayout(layout)

    def init_container_tab(self):
        container_tab = QWidget()
        container_layout = QVBoxLayout()

        self.containers_table = QTableView()
        self.load_containers()

        container_layout.addWidget(self.containers_table)
        container_tab.setLayout(container_layout)

        self.tabs.addTab(container_tab, "Containers")

    def init_images_tab(self):
        image_tab = QWidget()
        image_layout = QVBoxLayout()

        self.images_table = QTableView()
        self.load_images()

        image_layout.addWidget(self.images_table)
        image_tab.setLayout(image_layout)

        self.tabs.addTab(image_tab, "Imagens")

    def load_containers(self):
        headers, data = self.docker_utils.get_running_containers_details()
        self.container_model = ContainerTableModel(headers, data)
        self.containers_table.setModel(self.container_model)

        self.containers_table.resizeColumnsToContents()
        self.containers_table.horizontalHeader().setStretchLastSection(True)
        self.containers_table.setSelectionBehavior(QTableView.SelectRows)

        # Estilo
        self.containers_table.setStyleSheet("""
            QTableView {
                font-family: 'Segoe UI';
                font-size: 13px;
                gridline-color: #6272a4;
            }
            QHeaderView::section {
                background-color: #6272a4;
                padding: 4px;
                border: 1px solid #44475a;
            }
        """)

        # Centraliza as células
        from PyQt5.QtWidgets import QStyledItemDelegate
        from PyQt5.QtCore import Qt

        class CenterDelegate(QStyledItemDelegate):
            def initStyleOption(self, option, index):
                super().initStyleOption(option, index)
                option.displayAlignment = Qt.AlignCenter | Qt.AlignVCenter

        delegate = CenterDelegate()
        for col in range(len(headers)):
            self.containers_table.setItemDelegateForColumn(col, delegate)

        self.containers_table.verticalHeader().setDefaultSectionSize(28)

    def load_images(self):
        headers, data = self.docker_utils.get_docker_images_details()
        self.image_model = ImageTableModel(headers, data)
        self.images_table.setModel(self.image_model)

        self.images_table.resizeColumnsToContents()
        self.images_table.horizontalHeader().setStretchLastSection(True)
        self.images_table.setSelectionBehavior(QTableView.SelectRows)

        self.images_table.setStyleSheet("""
            QTableView {
                font-family: 'Segoe UI';
                font-size: 13px;
                gridline-color: #6272a4;
            }
            QHeaderView::section {
                background-color: #6272a4;
                padding: 4px;
                border: 1px solid #44475a;
            }
        """)

        from PyQt5.QtWidgets import QStyledItemDelegate
        class CenterDelegate(QStyledItemDelegate):
            def initStyleOption(self, option, index):
                super().initStyleOption(option, index)
                option.displayAlignment = Qt.AlignCenter | Qt.AlignVCenter

        delegate = CenterDelegate()
        for col in range(len(headers)):
            self.images_table.setItemDelegateForColumn(col, delegate)

        self.images_table.verticalHeader().setDefaultSectionSize(28)
