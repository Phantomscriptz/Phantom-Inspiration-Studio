"""Application-owned Ollama model download manager.

Keeping this object on the main window means an ``ollama pull`` continues while
the user switches tabs.  Widgets only observe its signals; they never own the
process that is doing the download.
"""

import re

from PySide6.QtCore import QObject, QProcess, Signal


class OllamaModelManager(QObject):
    started = Signal(str)
    output = Signal(str)
    finished = Signal(str, bool, str)
    state_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyReadStandardOutput.connect(self._read_output)
        self.process.finished.connect(self._finished)
        self.process.errorOccurred.connect(self._error)
        self.model = ""
        self.log_lines: list[str] = []

    @property
    def is_running(self) -> bool:
        return self.process.state() != QProcess.NotRunning

    def install(self, model: str) -> bool:
        if self.is_running:
            return False
        self.model = model
        self.log_lines = [f"Starting: ollama pull {model}"]
        self.started.emit(model)
        self.state_changed.emit()
        self.process.start("ollama", ["pull", model])
        return True

    def _read_output(self):
        raw = bytes(self.process.readAllStandardOutput()).decode("utf-8", errors="replace")
        # Ollama redraws progress with CR and ANSI colour codes.  Normalising it
        # produces a readable compact log in the UI.
        clean = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", raw).replace("\r", "\n")
        lines = [line.strip() for line in clean.splitlines() if line.strip()]
        if not lines:
            return
        self.log_lines.extend(lines)
        self.log_lines = self.log_lines[-120:]
        self.output.emit(lines[-1])

    def _error(self, _error):
        if self.process.error() == QProcess.FailedToStart:
            message = "Could not start Ollama. Install and start Ollama, then try again."
            self.log_lines.append(message)
            self.finished.emit(self.model, False, message)
            self.state_changed.emit()

    def _finished(self, exit_code, _exit_status):
        success = exit_code == 0
        message = "Download complete. Verifying installation…" if success else "Ollama exited before the download completed."
        self.log_lines.append(message)
        self.finished.emit(self.model, success, message)
        self.state_changed.emit()
