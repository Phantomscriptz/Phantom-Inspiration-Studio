from PySide6.QtWidgets import QListWidget


class Sidebar(QListWidget):

    def __init__(self):

        super().__init__()

        self.setFixedWidth(240)

        self.addItems([

            "🏠 Dashboard",

            "📁 Projects",

            "🧠 AI Brain",

            "🖼 Assets",

            "🎬 Renderer",

            "📤 Publish",

            "📈 Analytics",

            "⚙ Settings"

        ])