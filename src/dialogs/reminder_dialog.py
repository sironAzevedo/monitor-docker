import os
import platform
import subprocess

from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation
from PyQt5.QtGui import QIcon, QCursor
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QCheckBox, QHBoxLayout, QInputDialog, \
    QMessageBox, QScrollArea, QApplication, QGraphicsOpacityEffect, QSystemTrayIcon, QMenu, QAction, QMainWindow

from src.services.config_utils import load_config, log_and_notify
from src.services.docker_utils import DockerUtils
from src.utils.constantes_utils import ICON_PATH


class ReminderPopup(QMainWindow):
    def __init__(self):
        super().__init__()

        self.timer_refresh_checkboxes = None
        self.tray_icon = None
        self.docker_utlis = DockerUtils()
        self.timer_label = None
        self.checkboxes = []

        self.settings = load_config()
        self.timeout_seconds = int(self.settings.get("timeout", 1800))
        self.remaining_time = self.timeout_seconds

        self.setWindowTitle("Monitoramento de Container")
        self.setMinimumSize(600, 400)

        self.setStyleSheet("background-color: #282a36; color: #f8f8f2; font-size: 16px;")

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)

        self.init_ui()
        self.start_timer()
        self.center_on_screen()
        self.init_tray_icon()
        # self.hide()

    def init_ui(self):
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)

        self.label = QLabel("Containers em execução encontrados.\nDeseja manter ou pará-los?")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-weight: bold; font-size: 18px; margin-bottom: 20px;")
        layout.addWidget(self.label)

        self.checkbox_container = QWidget()
        self.checkbox_layout = QVBoxLayout(self.checkbox_container)
        self.checkbox_layout.setContentsMargins(10, 0, 10, 0)

        # Scroll area para lista de checkboxes
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background-color: #282a36; border: none;")
        self.scroll_area.setWidget(self.checkbox_container)

        layout.addWidget(self.scroll_area)
        button_layout = QHBoxLayout()

        self.label_tempo = QLabel()
        self.label_tempo.setAlignment(Qt.AlignCenter)
        self.label_tempo.setStyleSheet("font-size: 36px; font-weight: bold;")
        layout.addWidget(self.label_tempo)

        # Botão Manter
        self.keep_button = QPushButton("Manter")
        self.keep_button.clicked.connect(self.keep_containers)
        self.keep_button.setStyleSheet("""
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
        button_layout.addWidget(self.keep_button)

        # Botão Parar
        self.stop_button = QPushButton("Parar")
        self.stop_button.clicked.connect(self.stop_containers_action)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #ff5555;
                color: #f8f8f2;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
                margin-left: 10px;
            }
        """)
        button_layout.addWidget(self.stop_button)

        # Botão Lembrar
        self.later_button = QPushButton("Lembrar")
        self.later_button.clicked.connect(self.remind_later)
        self.later_button.setStyleSheet("""
            QPushButton {
                background-color: #f1fa8c;
                color: #282a36;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
                margin-left: 10px;
            }
        """)
        button_layout.addWidget(self.later_button)

        # Botão Fechar
        self.exit_button = QPushButton("Fechar")
        self.exit_button.clicked.connect(self.close_app)
        self.exit_button.setStyleSheet("""
            QPushButton {
                background-color: #bd93f9;
                color: #f8f8f2;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
                margin-left: 10px;
            }
        """)
        button_layout.addWidget(self.exit_button)

        layout.addLayout(button_layout)
        # self.setLayout(layout)
        self.setCentralWidget(central_widget)


        # Cria os checkboxes iniciais
        self.update_checkboxes()

        #manter na ultima posição
        self.exec_refresh_checkboxes()
        self.update_timer_display()

    def get_selected_containers(self):
        return [
            cb.text() for cb in self.checkboxes if cb.isChecked()
        ]

    def start_timer(self):
        self.timer.start(1000)

    def update_timer(self):
        self.remaining_time -= 1
        self.update_timer_display()

        if self.remaining_time <= 0:
            self.timer.stop()
            self.auto_stop()
            self.close()

    def update_timer_display(self):
        minutes = 00
        seconds = 00
        if self.exist_containers_running():
            minutes = self.remaining_time // 60
            seconds = self.remaining_time % 60
            time_str = f"{minutes:02}:{seconds:02}"
            self.label_tempo.setText(time_str)

            if self.remaining_time <= 60:
                self.label_tempo.setStyleSheet("font-size: 48px; font-weight: bold; color: #ff5555;")
            elif self.remaining_time <= 300:
                self.label_tempo.setStyleSheet("font-size: 48px; font-weight: bold; color: #ffb86c;")
            else:
                self.label_tempo.setStyleSheet("font-size: 48px; font-weight: bold; color: #f8f8f2;")
        else:
            time_str_zerado = f"{minutes:02}:{seconds:02}"
            self.label_tempo.setText(time_str_zerado)

    def update_checkboxes(self):
        # Armazena os nomes dos checkboxes marcados atualmente
        checked_names = set(cb.text() for cb in self.checkboxes if cb.isChecked())


        # Limpa checkboxes antigos
        for cb in self.checkboxes:
            self.checkbox_layout.removeWidget(cb)
            cb.setParent(None)
        self.checkboxes.clear()

        # Recria checkboxes com containers atuais
        headers, containers = self.get_containers_running()
        for container in containers:
            checkbox = QCheckBox(container['Nome'])

            # Marca checkbox se ele estava marcado anteriormente
            if container['Nome'] in checked_names:
                checkbox.setChecked(True)

            checkbox.setStyleSheet("""
                QCheckBox {
                    color: #f8f8f2;
                    font-weight: bold;
                    margin: 4px;
                    padding-left: 10px;
                }

                QCheckBox::indicator {
                    width: 14px;
                    height: 14px;
                    border: 2px solid #f8f8f2;
                    border-radius: 3px;
                    background-color: #44475a;
                }

                QCheckBox::indicator:hover {
                    border: 2px solid #bd93f9;
                    background-color: #6272a4;
                }

                QCheckBox::indicator:checked {
                    background-color: #50fa7b;
                    border: 2px solid #50fa7b;
                }

                QCheckBox::indicator:checked:hover {
                    background-color: #69ff94;
                    border: 2px solid #69ff94;
                }
            """)
            self.checkbox_layout.addWidget(checkbox)
            self.checkboxes.append(checkbox)

    def auto_stop(self):
        self.docker_utlis.stop_containers()
        log_and_notify("Tempo esgotado. Containers foram parados automaticamente.")

    def keep_containers(self):
        log_and_notify("Usuário optou por manter os containers em execução.")
        self.close_app()

    def stop_containers_action(self):
        selected = self.get_selected_containers()

        if not selected:
            QMessageBox.warning(self, "Aviso", "Selecione pelo menos um container.")
            return

        container_names = []
        for name in selected:
            container_names.append(name)
            self.docker_utlis.stop_container_by_name_or_id(name)

        nome_formatados = ', '.join(container_names)
        msg = f'Os seguintes containers foram parados: \n[{nome_formatados}]'
        QMessageBox.information(self, "Resultado", msg)
        log_and_notify(msg)
        self.verify_containers()

    def remind_later(self):
        minutes, ok = QInputDialog.getInt(
            self, "Lembrar depois", "Em quantos minutos deseja ser lembrado novamente?",
            value=10, min=1, max=1440
        )
        if ok:
            delay_seconds = minutes * 60
            log_and_notify(f"Usuário escolheu ser lembrado em {minutes} minutos.")
            QMessageBox.information(self, "Agendado",
                                    f"Você será lembrado novamente em {minutes} minutos.")
            subprocess.Popen(["bash", "-c",
                              f"sleep {delay_seconds} && python3 {os.path.abspath(__file__)} &"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.close_app()

    def center_on_screen(self):
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        popup_geometry = self.geometry()
        x = (screen_geometry.width() - popup_geometry.width()) // 2
        y = (screen_geometry.height() - popup_geometry.height()) // 2
        self.move(x, y)

    def fade_in_animation(self):
        self.setWindowOpacity(0)
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)

        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(500)  # duração da animação em milissegundos
        self.anim.setStartValue(0)
        self.anim.setEndValue(1)
        self.anim.start()

    def schedule_auto_close(self, seconds=60):
        QTimer.singleShot(seconds * 1000, self.close_app)

    def init_tray_icon(self):
        icon = QIcon(ICON_PATH)
        if icon.isNull():
            print("Erro: ícone inválido.")

        self.tray_icon = QSystemTrayIcon(icon, self)
        self.tray_icon.setToolTip("Lembrete de Processo")

        # Menu do botão direito do ícone na bandeja
        menu = QMenu()

        show_action = QAction("Mostrar")
        show_action.triggered.connect(self.show_popup)

        exit_action = QAction("Sair")
        exit_action.triggered.connect(QApplication.quit)

        menu.addAction(show_action)
        menu.addAction(exit_action)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        self.tray_icon.show()

    def show_popup(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def on_tray_icon_activated(self, reason):
        if reason in (QSystemTrayIcon.DoubleClick, QSystemTrayIcon.MiddleClick, QSystemTrayIcon.Critical):
            self.show_popup()

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self,
            "Sair",
            "Tem certeza que deseja parar o monitoramento?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            log_and_notify("Monitoramento finalizado.")
            self.timer.stop()
            QApplication.quit()
            event.accept()
        else:
            event.ignore()

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

    def exec_refresh_checkboxes(self):
        self.timer_refresh_checkboxes = QTimer()
        self.timer_refresh_checkboxes.timeout.connect(self.update_checkboxes)
        self.timer_refresh_checkboxes.start(5000)  # 5000 ms = 5 segundos

    def verify_containers(self):
        if not self.exist_containers_running():
            QMessageBox.information(self, "Resultado", "Todos os containers foram parados.")
            self.close_app()
        else:
            self.update_checkboxes()

    def exist_containers_running(self):
        headers, containers = self.get_containers_running()
        if len(containers) >= 1:
            return True

        return False

    def get_containers_running(self):
        headers, containers = self.docker_utlis.get_running_containers_details()
        return headers, containers