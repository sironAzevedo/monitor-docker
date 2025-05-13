import subprocess
import time
from PyQt5.QtCore import QThread, pyqtSignal


class LogUpdaterThread(QThread):
    new_logs = pyqtSignal(str)

    def __init__(self, container_id, line_count):
        super().__init__()
        self.container_id = container_id
        self.line_count = line_count
        self.running = True

    def run(self):
        while self.running:
            try:
                result = subprocess.run(
                    ["docker", "logs", "--tail", str(self.line_count), self.container_id],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                )
                logs = result.stdout if result.returncode == 0 else result.stderr
                self.new_logs.emit(logs)  # <-- Aqui o sinal é emitido corretamente
            except Exception as e:
                self.new_logs.emit(f"Erro ao obter logs: {str(e)}")
            self.msleep(2000)

    def stop(self):
        self.running = False
        self.wait()