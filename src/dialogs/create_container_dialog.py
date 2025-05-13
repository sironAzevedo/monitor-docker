from PyQt5.QtWidgets import (
    QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QFrame
)


class CreateContainerDialog(QDialog):
    def __init__(self, image_name, available_networks):
        super().__init__()
        self.setWindowTitle("Criar Novo Container")
        self.resize(600, 500)
        self.setStyleSheet("background-color: #282a36; color: #f8f8f2;")
        self.image_name = image_name
        self.available_networks = available_networks
        self.env_vars = []

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)

        # Título da imagem
        image_label = QLabel(f"<b>Imagem selecionada:</b> {self.image_name}")
        layout.addWidget(image_label)

        # Nome do container
        self.container_name_input = QLineEdit()
        self.container_name_input.setPlaceholderText("Nome do container")
        self.style_input(self.container_name_input)
        layout.addWidget(self.container_name_input)

        # Porta
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("Porta (ex: 8080:80)")
        self.style_input(self.port_input)
        layout.addWidget(self.port_input)

        # Rede
        self.network_combo = QComboBox()
        self.network_combo.addItems(self.available_networks)
        self.network_combo.setStyleSheet("""
                    QComboBox {
                        padding: 6px;
                        background-color: #3b3d48;
                        color: #f8f8f2;
                        border: 1px solid #555;
                    }
                    QComboBox QAbstractItemView {
                        background-color: #282a36;
                        color: #f8f8f2;
                        selection-background-color: #44475a;
                        selection-color: #ffffff;
                        font-size: 14px;
                    }
                """)
        layout.addWidget(QLabel("Rede:"))
        layout.addWidget(self.network_combo)

        # Separador visual
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("color: #44475a;")
        layout.addWidget(separator)

        # Variáveis de ambiente
        layout.addWidget(QLabel("Variáveis de Ambiente:"))

        self.env_table = QTableWidget(0, 2)
        self.env_table.setHorizontalHeaderLabels(["Nome", "Valor"])
        self.env_table.horizontalHeader().setStyleSheet("background-color: #44475a; color: #f8f8f2;")
        self.env_table.setStyleSheet("background-color: #3b3d48; color: #f8f8f2;")
        self.env_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.env_table)

        # Inputs para adicionar variável
        env_input_layout = QHBoxLayout()
        self.env_name_input = QLineEdit()
        self.env_name_input.setPlaceholderText("NOME")
        self.style_input(self.env_name_input)

        self.env_value_input = QLineEdit()
        self.env_value_input.setPlaceholderText("VALOR")
        self.style_input(self.env_value_input)

        add_env_btn = QPushButton("Adicionar")
        self.style_button(add_env_btn)
        add_env_btn.clicked.connect(self.add_env_var)

        env_input_layout.addWidget(self.env_name_input)
        env_input_layout.addWidget(self.env_value_input)
        env_input_layout.addWidget(add_env_btn)
        layout.addLayout(env_input_layout)

        # Botão Criar
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        create_btn = QPushButton("Criar Container")
        self.style_button(create_btn)
        create_btn.clicked.connect(self.validate_and_accept)
        button_layout.addWidget(create_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def style_input(self, widget):
        widget.setStyleSheet("""
            QLineEdit {
                padding: 6px;
                background-color: #3b3d48;
                color: #f8f8f2;
                border: 1px solid #44475a;
                border-radius: 4px;
            }
        """)

    def style_button(self, button):
        button.setStyleSheet("""
            QPushButton {
                padding: 6px 12px;
                background-color: #6272a4;
                color: #f8f8f2;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #7085c1;
            }
        """)

    def add_env_var(self):
        name = self.env_name_input.text().strip()
        value = self.env_value_input.text().strip()
        if name and value:
            row_position = self.env_table.rowCount()
            self.env_table.insertRow(row_position)
            self.env_table.setItem(row_position, 0, QTableWidgetItem(name))
            self.env_table.setItem(row_position, 1, QTableWidgetItem(value))
            self.env_name_input.clear()
            self.env_value_input.clear()

    def validate_and_accept(self):
        container_name = self.container_name_input.text().strip()
        port = self.port_input.text().strip()

        if not container_name:
            QMessageBox.warning(self, "Campo obrigatório", "Informe o nome do container.")
            return

        if not port or ':' not in port:
            QMessageBox.warning(self, "Campo obrigatório", "Informe a porta no formato correto (ex: 8080:80).")
            return

        self.accept()

    def get_data(self):
        env_vars = []
        for row in range(self.env_table.rowCount()):
            name = self.env_table.item(row, 0).text()
            value = self.env_table.item(row, 1).text()
            env_vars.append((name, value))
        return (
            self.image_name,
            self.container_name_input.text().strip(),
            self.port_input.text().strip(),
            self.network_combo.currentText(),
            env_vars
        )
