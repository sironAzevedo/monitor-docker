from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

from src.services.config_utils import log_and_notify


class StopContainersWorker(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    progress = pyqtSignal(int)

    def __init__(self, docker_utils, container_names):
        super().__init__()
        self.docker_utils = docker_utils
        self.container_names = container_names

    @pyqtSlot()
    def run(self):
        try:
            for idx, name in enumerate(self.container_names, start=1):
                self.docker_utils.stop_container_by_name_or_id(name)
                log_and_notify(f"Container {name} foi parado.")
                self.progress.emit(idx)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))