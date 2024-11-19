import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from .main import WatermarkerDialog


def main():
    # enable dpi scale
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    w = WatermarkerDialog()
    w.show()
    app.exec_()


if __name__ == "__main__":
    main()
