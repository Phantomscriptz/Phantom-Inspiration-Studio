from PySide6.QtWidgets import (
    QLabel,
    QPushButton,
    QFrame,
    QVBoxLayout,
    QGridLayout,
    QWidget,
)


class Dashboard(QWidget):

    def __init__(self):

        super().__init__()

        layout = QVBoxLayout(self)

        title = QLabel("Welcome to Phantom Inspiration Studio")

        title.setStyleSheet("""

            font-size:28px;
            font-weight:bold;

        """)

        layout.addWidget(title)

        grid = QGridLayout()

        layout.addLayout(grid)

        cards = [

            ("Projects", "0"),

            ("Videos Rendered", "0"),

            ("Scheduled", "0"),

            ("Published", "0"),

        ]

        row = 0

        col = 0

        for name, value in cards:

            frame = QFrame()

            frame.setStyleSheet("""

                QFrame{

                    border-radius:12px;

                    padding:18px;

                    background:#2D2D30;

                }

            """)

            card = QVBoxLayout(frame)

            label = QLabel(name)

            label.setStyleSheet("font-size:16px;")

            number = QLabel(value)

            number.setStyleSheet("""

                font-size:32px;

                font-weight:bold;

            """)

            card.addWidget(label)

            card.addWidget(number)

            grid.addWidget(frame, row, col)

            col += 1

            if col == 2:

                row += 1

                col = 0

        layout.addSpacing(20)

        generate = QPushButton("🚀 Generate New Project")

        generate.setMinimumHeight(50)

        layout.addWidget(generate)

        layout.addStretch()