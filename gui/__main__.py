import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from . import icon_rc  # noqa: F401
from .main import WatermarkerDialog


def main():
    # enable dpi scale
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(":/icon/logo.png"))
    w = WatermarkerDialog()
    w.show()
    app.exec_()


if __name__ == "__main__":
    main()
