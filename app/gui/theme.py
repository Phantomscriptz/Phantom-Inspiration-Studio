from PySide6.QtWidgets import QApplication


def load_dark_theme(app: QApplication):

    app.setStyleSheet("""
QMainWindow{
    background:#202124;
}

QWidget{
    background:#202124;
    color:white;
    font-size:10pt;
    font-family:"Segoe UI";
}

QToolBar{
    background:#2B2B2B;
    spacing:8px;
    border:none;
}

QStatusBar{
    background:#2B2B2B;
}

QListWidget{
    background:#2B2B2B;
    border:none;
    padding:10px;
}

QListWidget::item{
    padding:10px;
    border-radius:6px;
}

QListWidget::item:selected{
    background:#3B82F6;
}

QPushButton{
    background:#3B82F6;
    border:none;
    border-radius:8px;
    padding:12px;
    font-size:12pt;
}

QPushButton:hover{
    background:#2563EB;
}

QFrame{
    background:#2D2D30;
    border-radius:12px;
}

QLabel{
    color:white;
}
""")