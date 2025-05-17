import socket
import sys

from PyQt5.QtWidgets import QApplication

from src.dialogs.reminder_dialog import ReminderPopup

singleton_socket = None

def is_already_running():
    """Evita múltiplas instâncias usando socket local com nome abstrato."""
    global singleton_socket
    singleton_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    try:
        singleton_socket.bind('\0docker_monitor_popup_singleton')
        return False
    except socket.error:
        return True

if __name__ == "__main__":

    if is_already_running():
        print("Já existe uma instância do popup em execução.")
        sys.exit(0)

    app = QApplication(sys.argv)
    popup = ReminderPopup()
    popup.show()
    sys.exit(app.exec_())
