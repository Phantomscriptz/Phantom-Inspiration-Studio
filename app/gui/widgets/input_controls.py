"""Small, shared input controls with safe desktop interaction defaults."""

from PySide6.QtWidgets import QComboBox


class NoWheelComboBox(QComboBox):
    """Never alter a selected value merely because the user is scrolling a page.

    The popup list itself still scrolls normally after it has been opened.
    """

    def wheelEvent(self, event):  # noqa: N802 - Qt API spelling
        event.ignore()
