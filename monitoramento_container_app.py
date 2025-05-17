import sys

from PyQt5.QtWidgets import QApplication

from src.dialogs.reminder_dialog import ReminderPopup

if __name__ == "__main__":
    app = QApplication(sys.argv)
    popup = ReminderPopup()
    popup.show()
    sys.exit(app.exec_())
