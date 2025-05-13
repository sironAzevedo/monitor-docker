from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QWidget, QFormLayout, QPushButton, QCheckBox, QSpinBox


class SettingsWidgetDialog(QWidget):
    settings_changed = pyqtSignal(bool, int)  # sinal emitido com: ativado, timeout

    def __init__(self, monitor_enabled=False, timeout_minutes=5):
        super().__init__()

        self.monitor_enabled_checkbox = QCheckBox("Ativar monitoramento de containers")
        self.monitor_enabled_checkbox.setChecked(monitor_enabled)
        self.monitor_enabled_checkbox.stateChanged.connect(self.toggle_monitoring_fields)

        self.timeout_input = QSpinBox()
        self.timeout_input.setRange(1, 6440)  # minutos
        self.timeout_input.setSuffix(" min")
        self.timeout_input.setValue(timeout_minutes // 60)
        self.timeout_input.setVisible(monitor_enabled)

        self.save_button = QPushButton("Salvar")
        self.save_button.clicked.connect(self.emit_settings)

        layout = QFormLayout()
        layout.addRow(self.monitor_enabled_checkbox)
        layout.addRow("Tempo para verificar (min):", self.timeout_input)
        layout.addRow(self.save_button)

        self.setLayout(layout)

    def emit_settings(self):
        monitor_ativo = self.monitor_enabled_checkbox.isChecked()
        try:
            timeout = self.timeout_input.value()
        except ValueError:
            timeout = 5  # fallback padrão

        self.settings_changed.emit(monitor_ativo, timeout)

    def toggle_monitoring_fields(self, state):
        self.timeout_input.setVisible(state == Qt.Checked)