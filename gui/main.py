import traceback

from PyQt5.QtCore import QObject, QThread, QUrl, pyqtSignal
from PyQt5.QtGui import QDesktopServices, QFont
from PyQt5.QtWidgets import QFileDialog, QVBoxLayout, QWidget
from qfluentwidgets import (
    ExpandLayout,
    InfoBar,
    InfoBarPosition,
    PrimaryPushSettingCard,
    ProgressBar,
    PushButton,
    PushSettingCard,
    RangeSettingCard,
    TextBrowser,
)
from qfluentwidgets import FluentIcon as fi

from .config import cfg
from .settings import SettingInterface


class ProcessWorker(QObject):
    finished = pyqtSignal(bool)
    progress = pyqtSignal(int)
    error = pyqtSignal(str)

    def __init__(self, config):
        super().__init__()
        self.config = config

    def run(self):
        from watermarker import build_processor_chain, get_file_list, process_one

        files = get_file_list(cfg.input_directory.value)
        total = len(files)
        success = True

        processor = build_processor_chain(self.config)
        for i, file in enumerate(files):
            try:
                process_one(processor, file, cfg.output_directory.value)
                self.progress.emit(int(i / total * 100))
            except Exception:
                traceback.print_exc()
                self.error.emit(traceback.format_exc())
                success = False
                break
        self.finished.emit(success)


class WatermarkerDialog(QWidget):
    def __init__(self):
        from watermarker import __version__

        super().__init__()
        self.setWindowTitle(f"Watermarker v{__version__}")
        self.vLayout = QVBoxLayout(self)
        self.settingInterface = SettingInterface(self)
        self.vLayout.setContentsMargins(0, 0, 0, 0)
        self.vLayout.addWidget(self.settingInterface)

        parent = QWidget(self)
        layout = ExpandLayout(parent)
        layout.setContentsMargins(10, 0, 10, 0)
        self.inputDir = PushSettingCard(
            "选择目录",
            fi.FOLDER,
            "输入目录",
            content=cfg.get(cfg.input_directory),
            parent=parent,
        )
        self.outputDir = PushSettingCard(
            "选择目录",
            fi.FOLDER,
            "输出目录",
            content=cfg.get(cfg.output_directory),
            parent=parent,
        )
        self.showOutputButton = PushButton("打开输出目录", parent=parent)
        self.outputDir.hBoxLayout.addWidget(self.showOutputButton)
        self.outputDir.hBoxLayout.addSpacing(16)
        layout.addWidget(self.inputDir)
        layout.addWidget(self.outputDir)
        self.quality = RangeSettingCard(cfg.quality, fi.LEAF, "图像质量", parent=parent)
        layout.addWidget(self.quality)
        self.process_button = PrimaryPushSettingCard(
            "开始处理", fi.PLAY, "处理图像", parent=parent
        )
        layout.addWidget(self.process_button)

        self.logBrowser = TextBrowser(parent)
        font = QFont("SF Mono")
        font.setStyleHint(QFont.Monospace)
        self.logBrowser.setFont(font)
        self.logBrowser.setFixedHeight(200)
        self.logBrowser.setReadOnly(True)
        self.logBrowser.hide()
        self.progress_bar = ProgressBar(parent)
        # self.progress_bar.hide()
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.logBrowser)
        self.vLayout.addWidget(parent)
        self.vLayout.addSpacing(10)
        self.setFixedWidth(800)

        self.process_button.clicked.connect(self.__onProcessButtonClicked)
        self.inputDir.clicked.connect(self.__onInputButtonClicked)
        self.outputDir.clicked.connect(self.__onOutputButtonClicked)
        self.showOutputButton.clicked.connect(self.__onShowOutputButtonClicked)

    def __onShowOutputButtonClicked(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(cfg.output_directory.value))

    def __onProgress(self, value):
        self.progress_bar.setValue(value)

    def __onTaskFinished(self, success):
        self.process_button.setEnabled(True)
        self.progress_bar.hide()
        self.worker.deleteLater()
        self.thread.quit()
        if success:
            InfoBar.success(
                title="处理成功",
                content="已完成全部图片的水印添加",
                position=InfoBarPosition.BOTTOM,
                duration=2000,
                parent=self.window(),
            )
        else:
            InfoBar.error(
                "处理失败",
                "请查看日志",
                position=InfoBarPosition.BOTTOM,
                duration=2000,
                parent=self.window(),
            )

    def __onError(self, message):
        self.logBrowser.setText(message)
        self.logBrowser.show()

    def __onProcessButtonClicked(self):
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self.process_button.setEnabled(False)
        self.logBrowser.clear()
        config = cfg.as_core_config()
        self.thread = QThread()
        self.worker = ProcessWorker(config)
        self.worker.moveToThread(self.thread)
        self.worker.finished.connect(self.__onTaskFinished)
        self.worker.progress.connect(self.__onProgress)
        self.worker.error.connect(self.__onError)
        self.thread.started.connect(self.worker.run)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def __onInputButtonClicked(self):
        folder = QFileDialog.getExistingDirectory(self.window(), "选择输入目录")
        if folder:
            self.inputDir.setContent(folder)
            cfg.set(cfg.input_directory, folder)

    def __onOutputButtonClicked(self):
        folder = QFileDialog.getExistingDirectory(self.window(), "选择输出目录")
        if folder:
            self.outputDir.setContent(folder)
            cfg.set(cfg.output_directory, folder)
