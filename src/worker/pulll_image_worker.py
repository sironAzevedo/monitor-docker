from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot


class PullImageWorker(QObject):
    progress = pyqtSignal(int)
    log = pyqtSignal(str)  # mensagens de log
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, docker_utils, image_name):
        super().__init__()
        self.docker_utils = docker_utils
        self.image_name = image_name

    @pyqtSlot()
    def run(self):
        try:
            layer_progress = {}

            for line in self.docker_utils.pull_image_with_progress(self.image_name):
                status = line.get("status", "")
                layer_id = line.get("id", "")
                progress_detail = line.get("progressDetail", {})

                if layer_id:
                    self.log.emit(f"{status} {layer_id}".strip())

                # Verifica se há progresso detalhado
                if progress_detail and "current" in progress_detail and "total" in progress_detail:
                    current = progress_detail["current"]
                    total = progress_detail["total"]

                    if total > 0:
                        percentage = int((current / total) * 100)
                        layer_progress[layer_id] = percentage

                        # Calcula média geral de progresso
                        avg_progress = int(sum(layer_progress.values()) / len(layer_progress))
                        self.progress.emit(avg_progress)
        except Exception as e:
            self.error.emit(str(e))
        else:
            self.finished.emit()
