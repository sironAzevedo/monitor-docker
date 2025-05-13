import os
import platform
import subprocess
import sys

from PyQt5.QtCore import Qt, QThread
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QMessageBox, QInputDialog,
    QMainWindow, QAction, QSystemTrayIcon,
    QMenu, QTableView, QListWidget, QTextEdit, QStackedWidget, QListWidgetItem, QHeaderView,
    QTabWidget, QDialog, QProgressDialog
)

from src.dialogs.container_details_dialog import ContainerDetailsDialog
from src.dialogs.create_container_dialog import CreateContainerDialog
from src.dialogs.settings_widget_dialog import SettingsWidgetDialog
from src.models.container_table_model import ContainerTableModel
from src.models.image_table_model import ImageTableModel
from src.services.config_utils import load_config, log_and_notify, save_config, get_config_path, get_log_path
from src.services.docker_utils import DockerUtils
from src.ui.center_delegate import CenterDelegate
from src.ui.status_delegate import StatusDelegate
from src.utils.constantes_utils import ICON_PATH, ICON_HOME_PATH, ICON_SETTINGS_PATH, ICON_REPORT_PATH
from src.worker.pulll_image_worker import PullImageWorker
from src.worker.remove_containers_worker import RemoveContainersWorker
from src.worker.start_containers_worker import StartContainersWorker
from src.worker.stop_containers_worker import StopContainersWorker


class DockerMonitor(QMainWindow):
    def __init__(self, dockerUtils: DockerUtils):
        super().__init__()
        self.progress_dialog = None
        self.dockerUtils = dockerUtils
        self.report_widget = None
        self.home_widget = None
        self.menu_list = None
        self.timer_label = None
        self.model = None
        self.later_button = None
        self.containers_table = None
        self.details_tabs = None
        self.setWindowTitle("Docker Monitor")
        self.setMinimumSize(1200, 600)
        self.setStyleSheet("background-color: #282a36; color: #f8f8f2;")

        self.center_delegate = CenterDelegate()
        self.composite_delegate = StatusDelegate()

        self.settings = load_config()
        self.timeout_seconds = int(self.settings.get("timeout", 1800))
        self.monitoring_enabled = self.settings.get("monitoring_enabled", False)

        self.tray_icon = None
        self.container_data = []
        self.container_headers = []

        self.init_icon()
        # self.init_tray_icon()
        self.init_menu()

        # Estilos ativos
        self.start_button_active_style = """
            QPushButton {
                background-color: #50fa7b;
                color: #282a36;
                font-weight: bold;
                padding: 10px 30px;
                border-radius: 5px;
                margin-left: 10px;
            }
            QPushButton:hover {
                background-color: #69ff94;
            }
        """

        self.stop_button_active_style = """
            QPushButton {
                background-color: #ff5555;
                color: #f8f8f2;
                font-weight: bold;
                padding: 10px 30px;
                border-radius: 5px;
                margin-left: 10px;
            }
            QPushButton:hover {
                background-color: #ff6666;
            }
        """

        self.remove_button_active_style = """
            QPushButton {
                background-color: #bd93f9;
                color: #f8f8f2;
                font-weight: bold;
                padding: 10px 30px;
                border-radius: 5px;
                margin-left: 10px;
            }
            QPushButton:hover {
                background-color: #caa5ff;
            }
        """

        self.create_container_button_active_style = """
            QPushButton {
                background-color: #ffb86c;
                color: #282a36;
                font-weight: bold;
                padding: 10px 30px;
                border-radius: 5px;
                margin-left: 10px;
            }
            QPushButton:hover {
                background-color: #ffc87d;
            }
        """

        self.remove_image_button_active_style = """
                    QPushButton {
                        background-color: #ff5555;
                        color: #f8f8f2;
                        font-weight: bold;
                        padding: 10px 30px;
                        border-radius: 5px;
                        margin-left: 10px;
                    }
                    QPushButton:hover {
                        background-color: #ff6666;
                    }
                """

        # Estilo cinza para botões desabilitados
        self.disabled_button_style = """
            QPushButton {
                background-color: #888888;
                color: #cccccc;
                font-weight: bold;
                padding: 10px 30px;
                border-radius: 5px;
                margin-left: 10px;
            }
        """

        self.init_ui()
        self.load_containers()
        self.load_imagens()

    def init_icon(self):
        if os.path.exists(ICON_PATH):
            self.setWindowIcon(QIcon(ICON_PATH))
        else:
            self.setWindowIcon(QIcon.fromTheme("application-default"))

    def init_tray_icon(self):
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self.windowIcon(), self)

            self.tray_menu = QMenu()

            restore_action = QAction("Restaurar", self)
            restore_action.triggered.connect(self.showNormal)

            quit_action = QAction("Sair", self)
            quit_action.triggered.connect(QApplication.quit)

            self.tray_menu.addAction(restore_action)
            self.tray_menu.addAction(quit_action)

            self.tray_icon.setContextMenu(self.tray_menu)
            self.tray_icon.activated.connect(self.tray_activated)
            self.tray_icon.show()
        else:
            self.tray_icon = None

    def tray_activated(self, reason):
        if reason in (QSystemTrayIcon.DoubleClick, QSystemTrayIcon.MiddleClick):
            self.showNormal()
            self.activateWindow()

    def init_menu(self):
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #44475a;
                color: #f8f8f2;
                border-bottom: 1px solid #6272a4;
            }
            QMenuBar::item {
                background: transparent;
                padding: 8px 12px;
            }
            QMenuBar::item:selected {
                background-color: #6272a4;
            }
            QMenu {
                background-color: #44475a;
                color: #f8f8f2;
                border: 1px solid #6272a4;
            }
            QMenu::item {
                padding: 8px 20px;
            }
            QMenu::item:selected {
                background-color: #6272a4;
            }
        """)
        settings_menu = menubar.addMenu("Configurações")

        change_timer_action = QAction("Alterar tempo", self)
        change_timer_action.triggered.connect(self.change_timer)
        settings_menu.addAction(change_timer_action)

    def init_ui(self):
        central_widget = QWidget()
        main_layout = QHBoxLayout()

        # === Menu lateral ===
        menu_widget = QWidget()
        menu_widget.setFixedWidth(180)
        menu_widget.setStyleSheet("background-color: #282a36;")
        menu_layout = QVBoxLayout(menu_widget)
        menu_layout.setContentsMargins(0, 0, 0, 0)
        menu_layout.setSpacing(0)

        self.menu_list = QListWidget()
        self.menu_list.setStyleSheet("""
                QListWidget {
                    background-color: #282a36;
                    color: #f8f8f2;
                    font-size: 16px;
                    border: none;
                    padding-top: 10px;
                }
                QListWidget::item {
                    padding: 12px 20px;
                    height: 40px;
                }
                QListWidget::item:selected {
                    background-color: #44475a;
                    border-left: 4px solid #bd93f9;
                    font-weight: bold;
                }
                QListWidget::item:hover {
                    background-color: #383c4a;
                }
            """)
        self.menu_list.setFixedWidth(180)
        self.menu_list.setSpacing(2)

        home_item = QListWidgetItem(QIcon(ICON_HOME_PATH), "  Home")
        report_item = QListWidgetItem(QIcon(ICON_REPORT_PATH), "  Report")
        self.menu_list.addItem(home_item)
        self.menu_list.addItem(report_item)
        self.menu_list.currentRowChanged.connect(self.carrega_info_logs)

        self.settings_button = QPushButton(" Settings")
        self.settings_button.setStyleSheet("""
                QPushButton {
                    background-color: #282a36;
                    color: #f8f8f2;
                    font-size: 16px;
                    padding: 12px 20px;
                    border: none;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #383c4a;
                }
            """)
        self.settings_button.setFixedHeight(50)
        self.settings_button.setIcon(QIcon(ICON_SETTINGS_PATH))
        self.settings_button.clicked.connect(lambda: self.stack_widget.setCurrentIndex(2))

        menu_layout.addWidget(self.menu_list)
        menu_layout.addStretch()
        menu_layout.addWidget(self.settings_button)

        # === QStackedWidget ===
        self.stack_widget = QStackedWidget()

        # === Tela Home com abas ===
        self.home_widget = QWidget()
        home_layout = QVBoxLayout()

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
                QTabWidget::pane {
                    border: 1px solid #6272a4;
                }
                QTabBar::tab {
                    background: #44475a;
                    color: #f8f8f2;
                    padding: 10px 16px;
                    font-size: 14px;
                    border-top-left-radius: 8px;
                    border-top-right-radius: 8px;
                }
                QTabBar::tab:selected {
                    background: #bd93f9;
                    color: #282a36;
                }
            """)

        # === Aba Containers ===
        containers_tab = QWidget()
        containers_layout = QVBoxLayout()

        self.containers_table = QTableView()
        self.containers_table.setStyleSheet(
            "background-color: #44475a; border: 1px solid #6272a4; color: #f8f8f2; selection-background-color: #6272a4;")
        self.containers_table.doubleClicked.connect(self.show_container_details)
        containers_layout.addWidget(self.containers_table)

        # === Botões de controle por container selecionado ===
        controls_layout = QHBoxLayout()
        controls_layout.setAlignment(Qt.AlignLeft)

        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_selected_container)
        self.start_button.setStyleSheet(self.disabled_button_style)
        self.start_button.setEnabled(False)
        controls_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_selected_container)
        self.stop_button.setStyleSheet(self.disabled_button_style)
        self.stop_button.setEnabled(False)
        controls_layout.addWidget(self.stop_button)

        self.remove_button = QPushButton("Remove")
        self.remove_button.clicked.connect(self.remove_selected_containers)
        self.remove_button.setStyleSheet(self.disabled_button_style)
        self.remove_button.setEnabled(False)
        controls_layout.addWidget(self.remove_button)

        containers_layout.addLayout(controls_layout)
        containers_tab.setLayout(containers_layout)
        self.tabs.addTab(containers_tab, QIcon(ICON_HOME_PATH), "Containers")

        # === Aba Imagens ===
        images_tab = QWidget()
        images_layout = QVBoxLayout()

        self.images_table = QTableView()
        self.images_table.setStyleSheet(
            "background-color: #44475a; border: 1px solid #6272a4; color: #f8f8f2; selection-background-color: #6272a4;")
        images_layout.addWidget(self.images_table)

        # === Botões para ações de imagem ===
        image_controls_layout = QHBoxLayout()
        image_controls_layout.setAlignment(Qt.AlignLeft)

        self.pull_image_button = QPushButton("Baixar imagem")
        self.pull_image_button.setStyleSheet("""
                QPushButton {
                    background-color: #50fa7b;
                    color: #282a36;
                    font-weight: bold;
                    padding: 10px 20px;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #69ff94;
                }
            """)
        self.pull_image_button.clicked.connect(self.pull_image)
        image_controls_layout.addWidget(self.pull_image_button)

        self.create_container_button = QPushButton("Criar container")
        self.create_container_button.setStyleSheet(self.disabled_button_style)
        self.create_container_button.clicked.connect(self.create_container_from_image)
        self.create_container_button.setEnabled(False)
        image_controls_layout.addWidget(self.create_container_button)

        self.remove_image_button = QPushButton("Remover imagem")
        self.remove_image_button.setStyleSheet(self.disabled_button_style)
        self.remove_image_button.clicked.connect(self.remove_selected_image)
        self.remove_image_button.setEnabled(False)
        image_controls_layout.addWidget(self.remove_image_button)

        images_layout.addLayout(image_controls_layout)
        images_tab.setLayout(images_layout)
        self.tabs.addTab(images_tab, QIcon(ICON_REPORT_PATH), "Imagens")

        home_layout.addWidget(self.tabs)
        self.home_widget.setLayout(home_layout)

        # === Tela Report ===
        self.report_widget = QWidget()
        report_layout = QVBoxLayout()
        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        report_layout.addWidget(self.report_text)
        self.report_widget.setLayout(report_layout)

        # === Tela Settings ===
        self.settings_widget = SettingsWidgetDialog(self.monitoring_enabled, self.timeout_seconds)
        self.settings_widget.settings_changed.connect(self.save_monitoring_settings)
        self.stack_widget.addWidget(self.settings_widget)

        self.stack_widget.addWidget(self.home_widget)
        self.stack_widget.addWidget(self.report_widget)
        self.stack_widget.addWidget(self.settings_widget)

        # Finalizando layout principal
        main_layout.addWidget(menu_widget)
        main_layout.addWidget(self.stack_widget)
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def load_imagens(self):
        image_headers, image_data = self.dockerUtils.get_docker_images_details()
        image_model = ImageTableModel(image_headers, image_data)
        self.images_table.setModel(image_model)
        self.images_table.selectionModel().selectionChanged.connect(self.update_imagens_buttons)

        # Seleciona a linha inteira ao clicar em uma célula
        self.images_table.setSelectionBehavior(QTableView.SelectRows)

        # Impede seleção múltipla — apenas uma linha pode ser selecionada por vez
        # self.images_table.setSelectionMode(QAbstractItemView.SingleSelection)

        # Define que todas as colunas terão tamanho igual
        header = self.images_table.horizontalHeader()
        header.setStyleSheet("color: #f8f8f2; background-color: #6272a4; font-weight: bold;")
        header.setSectionResizeMode(QHeaderView.Stretch)

        # Centraliza o texto nas células
        self.images_table.setAlternatingRowColors(True)
        self.images_table.setStyleSheet("""
                QTableView {
                    background-color: #44475a;
                    alternate-background-color: #383c4a;
                    color: #f8f8f2;
                    selection-background-color: #bd93f9;
                    selection-color: #282a36;
                }
                QHeaderView::section {
                    background-color: #6272a4;
                    padding: 4px;
                    border: 1px solid #44475a;
                }
            """)

        # Centraliza o conteúdo das células via delegate
        from PyQt5.QtWidgets import QStyledItemDelegate
        class CenterDelegate(QStyledItemDelegate):
            def initStyleOption(self, option, index):
                super().initStyleOption(option, index)
                option.displayAlignment = Qt.AlignCenter | Qt.AlignVCenter

        delegate = CenterDelegate()
        for i in range(len(image_headers)):
            self.images_table.setItemDelegateForColumn(i, delegate)

        # Define altura padrão das linhas
        self.images_table.verticalHeader().setDefaultSectionSize(30)

    def load_containers(self):
        self.container_headers, self.container_data = self.dockerUtils.get_all_containers_details_subprocess()
        self.model = ContainerTableModel(self.container_headers, self.container_data)
        self.containers_table.setModel(self.model)
        self.containers_table.selectionModel().selectionChanged.connect(self.update_container_buttons)

        # Seleciona a linha inteira ao clicar em uma célula
        self.containers_table.setSelectionBehavior(QTableView.SelectRows)

        # Define que todas as colunas terão tamanho igual
        header = self.containers_table.horizontalHeader()
        header.setStyleSheet("color: #f8f8f2; background-color: #6272a4; font-weight: bold;")
        header.setSectionResizeMode(QHeaderView.Stretch)

        # Centraliza o texto nas células
        self.containers_table.setAlternatingRowColors(True)
        self.containers_table.setStyleSheet("""
                QTableView {
                    background-color: #44475a;
                    alternate-background-color: #383c4a;
                    color: #f8f8f2;
                    selection-background-color: #bd93f9;
                    selection-color: #282a36;
                }
                QHeaderView::section {
                    background-color: #6272a4;
                    padding: 4px;
                    border: 1px solid #44475a;
                }
            """)

        for i, column_name in enumerate(self.container_headers):
            if column_name.lower() == "status":
                self.containers_table.setItemDelegateForColumn(i, self.composite_delegate)
            else:
                self.containers_table.setItemDelegateForColumn(i, self.center_delegate)

        # Define altura padrão das linhas
        self.containers_table.verticalHeader().setDefaultSectionSize(30)

    def show_container_details(self, index):
        if not index.isValid():
            return

        row = index.row()
        container_id = self.container_data[row].get("ID")
        if container_id:
            dialog = ContainerDetailsDialog(self.dockerUtils, container_id, self)
            dialog.exec_()

    def keep_containers(self):
        self.timer.stop()
        log_and_notify("Usuário optou por manter os containers em execução.")
        QMessageBox.information(self, "Resultado", "Containers mantidos em execução.")
        self.close_app()

    def stop_containers_action(self):
        self.timer.stop()
        self.dockerUtils.stop_containers()
        log_and_notify("Usuário optou por parar os containers.")
        QMessageBox.information(self, "Resultado", "Todos os containers foram parados.")
        self.close_app()

    def auto_stop(self):
        self.dockerUtils.stop_containers()
        log_and_notify("Tempo esgotado. Containers foram parados automaticamente.")
        QMessageBox.warning(self, "Tempo esgotado", "Tempo esgotado. Containers foram parados.")
        self.close_app()

    def change_timer(self):
        new_value, ok = QInputDialog.getInt(
            self, "Configurar Tempo", "Digite o tempo limite em minutos:",
            value=self.timeout_seconds // 60, min=1, max=1440
        )
        if ok:
            self.timeout_seconds = new_value * 60
            save_config(self.timeout_seconds)
            QMessageBox.information(self, "Configuração Salva",
                                    f"Novo tempo: {new_value} minutos. A mudança terá efeito no próximo monitoramento.")

    def carrega_info_logs(self, index):
        self.stack_widget.setCurrentIndex(index)
        if index == 1:
            try:
                with open(get_log_path(), "r") as f:
                    self.report_text.setText(f.read())
            except Exception as e:
                self.report_text.setText(f"Erro ao carregar relatório: {e}")

    def close_app(self):
        if self.tray_icon and platform.system() in ["Linux", "Windows"]:
            self.hide()
            self.tray_icon.showMessage(
                "Docker Monitor",
                "O monitor está rodando minimizado na bandeja.",
                QSystemTrayIcon.Information,
                2000
            )
        else:
            QApplication.quit()

    def update_tables(self):
        # Containers
        container_headers, container_data = self.dockerUtils.get_all_containers_details()
        container_model = ContainerTableModel(container_headers, container_data)
        self.containers_table.setModel(container_model)

        # Imagens
        image_headers, image_data = self.dockerUtils.get_docker_images_details()
        image_model = ImageTableModel(image_headers, image_data)
        self.images_table.setModel(image_model)

    def update_controls_visibility(self):
        is_containers_tab = self.tabs.currentIndex() == 0
        self.container_controls_widget.setVisible(is_containers_tab)

    def get_selected_container_names(self):
        selected_indexes = self.containers_table.selectionModel().selectedRows()
        if not selected_indexes:
            QMessageBox.warning(self, "Aviso", "Nenhum container selecionado.")
            return []

        model = self.containers_table.model()
        container_names = []

        for index in selected_indexes:
            row = index.row()
            name = model.index(row, 1).data()  # Coluna 0 = nome do container
            container_names.append(name)

        return container_names

    def get_selected_images_names(self):
        selected_indexes = self.images_table.selectionModel().selectedRows()
        if not selected_indexes:
            return []

        model = self.images_table.model()
        images_names = []

        for index in selected_indexes:
            row = index.row()
            name = model.get_image_name(row)
            images_names.append(name)

        return images_names

    def start_selected_container(self):
        container_names = self.get_selected_container_names()
        if not container_names:
            return

        nome_formatados = ', '.join(container_names)

        # Mostra diálogo de progresso
        self.progress_dialog = self.show_progress_dialog(title="Iniciando containers",
                                                         text="Aguarde enquanto os container(s) são iniciados...",
                                                         maximum=len(container_names))

        # Cria thread e worker
        self.thread_start_container = QThread()
        self.worker_start_container = StartContainersWorker(self.dockerUtils, container_names)
        self.worker_start_container.moveToThread(self.thread_start_container)

        # Conecta sinais
        self.thread_start_container.started.connect(self.worker_start_container.run)
        self.worker_start_container.finished.connect(self.thread_start_container.quit)
        self.worker_start_container.finished.connect(self.worker_start_container.deleteLater)
        self.thread_start_container.finished.connect(self.thread_start_container.deleteLater)
        self.worker_start_container.progress.connect(self.progress_dialog.setValue)

        # Conecta sinais para feedback
        def on_finished():
            self.progress_dialog.close()
            QMessageBox.information(self, "Iniciando containers", f"Container(s) '{nome_formatados}' iniciado com sucesso.")
            self.load_containers()

        def on_error(message):
            self.progress_dialog.close()
            QMessageBox.critical(self, "Erro", f"Erro ao iniciar container:\n{message}")
            self.load_containers()

        self.worker_start_container.finished.connect(on_finished)
        self.worker_start_container.error.connect(on_error)

        # Inicia thread
        self.thread_start_container.start()

    def stop_selected_container(self):
        container_names = self.get_selected_container_names()
        if not container_names:
            return

        nome_formatados = ', '.join(container_names)
        confirm = QMessageBox.question(
            self,
            "Parar container(s)",
            f"Tem certeza que deseja parar o(s) containers \n[{nome_formatados}]?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.No:
            return

        # Mostra diálogo de progresso
        self.progress_dialog = self.show_progress_dialog(title="Parando containers",
                                                         text="Aguarde enquanto os container(s) são parados...",
                                                         maximum=len(container_names))

        # Cria thread e worker
        self.thread_stop_container = QThread()
        self.worker_stop_container = StopContainersWorker(self.dockerUtils, container_names)
        self.worker_stop_container.moveToThread(self.thread_stop_container)

        # Conecta sinais
        self.thread_stop_container.started.connect(self.worker_stop_container.run)
        self.worker_stop_container.finished.connect(self.thread_stop_container.quit)
        self.worker_stop_container.finished.connect(self.worker_stop_container.deleteLater)
        self.thread_stop_container.finished.connect(self.thread_stop_container.deleteLater)
        self.worker_stop_container.progress.connect(self.progress_dialog.setValue)

        # Conecta sinais para feedback
        def on_finished():
            self.progress_dialog.close()
            QMessageBox.information(self, "Parando containers", f"Container(s) '{nome_formatados}' parado com sucesso.")
            self.load_containers()

        def on_error(message):
            self.progress_dialog.close()
            QMessageBox.critical(self, "Erro", f"Erro ao parar container:\n{message}")
            self.load_containers()

        self.worker_stop_container.finished.connect(on_finished)
        self.worker_stop_container.error.connect(on_error)

        # Inicia thread
        self.thread_stop_container.start()

    def remove_selected_containers(self):
        container_names = self.get_selected_container_names()
        if not container_names:
            return

        nome_formatados = ', '.join(container_names)
        confirm = QMessageBox.question(
            self,
            "Remover container(s)",
            f"Tem certeza que deseja remover o(s) containers \n[{nome_formatados}]?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.No:
            return

        # Mostra diálogo de progresso
        self.progress_dialog = self.show_progress_dialog(title="Remover containers",
                                                         text="Aguarde enquanto os container(s) são removidos...",
                                                         maximum=len(container_names))

        # Cria thread e worker
        self.thread_remove_container = QThread()
        self.worker_remove_container = RemoveContainersWorker(self.dockerUtils, container_names)
        self.worker_remove_container.moveToThread(self.thread_remove_container)

        # Conecta sinais
        self.thread_remove_container.started.connect(self.worker_remove_container.run)
        self.worker_remove_container.finished.connect(self.thread_remove_container.quit)
        self.worker_remove_container.finished.connect(self.worker_remove_container.deleteLater)
        self.thread_remove_container.finished.connect(self.thread_remove_container.deleteLater)
        self.worker_remove_container.progress.connect(self.progress_dialog.setValue)

        # Conecta sinais para feedback
        def on_finished():
            self.progress_dialog.close()
            QMessageBox.information(self, "Parando containers", f"Container(s) '{nome_formatados}' parado com sucesso.")
            self.load_containers()

        def on_error(message):
            self.progress_dialog.close()
            QMessageBox.critical(self, "Erro", f"Erro ao remover container:\n{message}")
            self.load_containers()

        self.worker_remove_container.finished.connect(on_finished)
        self.worker_remove_container.error.connect(on_error)

        # Inicia thread
        self.thread_remove_container.start()

    def pull_image(self):
        image_name, ok = QInputDialog.getText(self, "Baixar imagem", "Informe o nome da imagem (ex: nginx:latest):")
        if not (ok and image_name):
            return

            # Cria diálogo de progresso indeterminado
        self.progress_dialog = self.show_progress_dialog(
            title="Baixando imagem",
            text=f"Baixando imagem '{image_name}'...",
            cancellable=False,
            maximum=0  # progresso indeterminado
        )

        # Cria thread e worker
        self.thread_pull_image = QThread()
        self.worker_pull_image = PullImageWorker(self.dockerUtils, image_name)
        self.worker_pull_image.moveToThread(self.thread_pull_image)

        # Conecta sinais
        self.thread_pull_image.started.connect(self.worker_pull_image.run)
        self.worker_pull_image.finished.connect(self.thread_pull_image.quit)
        self.worker_pull_image.finished.connect(self.worker_pull_image.deleteLater)
        self.thread_pull_image.finished.connect(self.thread_pull_image.deleteLater)

        # Recebe o progresso real por camada
        def on_progress(avg_percent):
            self.progress_dialog.setLabelText(f"Baixando imagem... {avg_percent}%")
            self.progress_dialog.setValue(avg_percent)

        def on_log(msg):
            self.progress_dialog.setLabelText(msg)

        def on_finished():
            self.progress_dialog.close()
            self.load_imagens()
            log_and_notify(f"Imagem '{image_name}' baixada com sucesso.")
            QMessageBox.information(self, "Sucesso", f"Imagem '{image_name}' baixada com sucesso.")

        def on_error(err):
            self.progress_dialog.close()
            log_and_notify(f"Erro ao baixar imagem: {err}")
            QMessageBox.critical(self, "Erro", f"Erro ao baixar imagem:\n{err}")

        # Conexões
        self.worker_pull_image.progress.connect(on_progress)
        self.worker_pull_image.log.connect(on_log)
        self.worker_pull_image.finished.connect(on_finished)
        self.worker_pull_image.error.connect(on_error)

        # Inicia thread
        self.thread_pull_image.start()

    def create_container_from_image(self):
        index = self.images_table.currentIndex()
        if not index.isValid():
            QMessageBox.warning(self, "Aviso", "Selecione uma imagem na tabela.")
            return

        model = self.images_table.model()
        image_name = model.get_image_name(index.row())

        # Obter redes disponíveis
        try:
            networks = self.dockerUtils.get_available_networks()
        except Exception as e:
            log_and_notify(f"Erro ao listar redes: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao listar redes:\n{e}")
            return

        # Abrir diálogo personalizado
        dialog = CreateContainerDialog(image_name, networks)
        if dialog.exec_() == QDialog.Accepted:
            image_selected, container_name, port, network, env_vars = dialog.get_data()
            if not container_name or not port:
                QMessageBox.warning(self, "Aviso", "Nome do container e porta são obrigatórios.")
                return
            try:
                self.dockerUtils.build_container(image_selected, container_name, port, network, env_vars)
                self.load_containers()
                QMessageBox.information(self, "Sucesso", f"Container '{container_name}' criado com sucesso.")
            except Exception as e:
                log_and_notify(f"Erro ao criar container: {e}")
                QMessageBox.critical(self, "Erro", f"Erro ao criar container:\n{e}")

    def remove_selected_image(self):
        images_names = self.get_selected_images_names()
        if not images_names:
            return

        nome_formatados = ', '.join(images_names)
        confirm = QMessageBox.question(
            self,
            "Remover container(s)",
            f"Tem certeza que deseja remover a(s) images \n[{nome_formatados}]?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.No:
            return

        for name in images_names:
            try:
                self.dockerUtils.remove_image(name)
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao remover image:\n{str(e)}")

        QMessageBox.information(self, "Removido", f"image(s) '{nome_formatados}' removidos com sucesso.")
        self.load_imagens()

    #Captura o evento do botão fechar da tela
    def closeEvent(self, event):
        reply = QMessageBox.question(
            self,
            "Sair",
            "Tem certeza que deseja sair?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            log_and_notify("Aplicação Finalizada")
            self.close_app()
            event.accept()
        else:
            event.ignore()

    def update_container_buttons(self):
        selection_model = self.containers_table.selectionModel()
        has_selection = selection_model is not None and selection_model.hasSelection()

        self.start_button.setEnabled(has_selection)
        self.start_button.setStyleSheet(self.start_button_active_style if has_selection else self.disabled_button_style)

        self.stop_button.setEnabled(has_selection)
        self.stop_button.setStyleSheet(self.stop_button_active_style if has_selection else self.disabled_button_style)

        self.remove_button.setEnabled(has_selection)
        self.remove_button.setStyleSheet(self.remove_button_active_style if has_selection else self.disabled_button_style)

    def update_imagens_buttons(self):
        selection_model = self.images_table.selectionModel()
        has_selection = selection_model is not None and selection_model.hasSelection()
        self.remove_image_button.setEnabled(has_selection)
        self.remove_image_button.setStyleSheet(
            self.remove_image_button_active_style if has_selection else self.disabled_button_style)

        container_names = self.get_selected_images_names()
        if len(container_names) > 1:
            self.create_container_button.setEnabled(False)
            self.create_container_button.setStyleSheet(self.disabled_button_style)
        else:
            self.create_container_button.setEnabled(has_selection)
            self.create_container_button.setStyleSheet(self.create_container_button_active_style if has_selection else self.disabled_button_style)

    def toggle_monitoring_fields(self, state):
        self.timeout_input.setVisible(state == Qt.Checked)

    def save_monitoring_settings(self, monitor_enabled, timeout_minutes):
        self.timeout_seconds = timeout_minutes * 60  # converte de minutos para segundos

        save_config(self.timeout_seconds, monitor_enabled, get_config_path())

        QMessageBox.information(self, "Configurações salvas", "Configurações atualizadas com sucesso!")

        monitoramet_msg = 'ativado' if monitor_enabled else 'desativado'

        log_and_notify(f"O monitoramento foi {monitoramet_msg}.")

        # Reinicia o monitoramento se estiver ativo
        if monitor_enabled:
            subprocess.Popen([sys.executable, "reminder_popup_app.py"])

    # Método reutilizável para exibir progresso
    def show_progress_dialog(parent=None, title="", text="", maximum=0, cancellable=False):
        dialog = QProgressDialog(text, "Cancelar" if cancellable else None, 0, maximum, parent)
        dialog.setWindowTitle(title if isinstance(title, str) else "Progresso")
        dialog.setMinimumSize(500, 100)
        dialog.setWindowModality(Qt.ApplicationModal)
        dialog.setCancelButton(None if not cancellable else dialog.cancelButton())
        dialog.setMinimumDuration(0)
        dialog.setAutoClose(True)
        dialog.setAutoReset(True)
        dialog.show()
        QApplication.processEvents()
        return dialog