from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
)


class NewProjectDialog(QDialog):

    def __init__(self):

        super().__init__()

        self.setWindowTitle("New Project")

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Project Name"))

        self.name = QLineEdit()

        layout.addWidget(self.name)

        self.ok = QPushButton("Create")

        layout.addWidget(self.ok)

        self.ok.clicked.connect(self.accept)

    def project_name(self):

        return self.name.text()