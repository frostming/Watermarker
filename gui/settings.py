from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLabel, QWidget
from qfluentwidgets import (
    BodyLabel,
    CheckBox,
    ColorPickerButton,
    ComboBox,
    ComboBoxSettingCard,
    ExpandGroupSettingCard,
    ExpandLayout,
    ExpandSettingCard,
    LineEdit,
    OptionsSettingCard,
    PushButton,
    PushSettingCard,
    ScrollArea,
    SettingCard,
    SettingCardGroup,
    SpinBox,
    SwitchButton,
    SwitchSettingCard,
)
from qfluentwidgets import FluentIcon as fi
from qfluentwidgets.common.icon import FluentIconBase

from .config import cfg


class LayoutElement(QWidget):
    def __init__(self, position, label, parent=None) -> None:
        from watermarker.constants import MODELS

        super().__init__(parent)
        self.name_config = getattr(cfg, f"{position}_name")
        self.is_bold_config = getattr(cfg, f"{position}_is_bold")
        self.color_config = getattr(cfg, f"{position}_color")
        self.value_config = getattr(cfg, f"{position}_value")

        layout = QHBoxLayout(self)
        self.nameSelect = ComboBox(self)
        for option in self.name_config.options:
            self.nameSelect.addItem(MODELS[option], userData=option)
        self.valueInput = LineEdit(self)
        self.isBoldSwitch = CheckBox("加粗", parent=self)
        self.colorSelect = ColorPickerButton(self.color_config.value, "颜色", self)
        layout.addWidget(BodyLabel(label))
        layout.addStretch(1)
        layout.addWidget(self.nameSelect)
        layout.addWidget(self.valueInput)
        layout.addWidget(self.isBoldSwitch)
        layout.addWidget(self.colorSelect)

        self.setName(self.name_config.value)
        self.setValue(self.value_config.value)
        self.setIsBold(self.is_bold_config.value)
        self.setColor(self.color_config.value)

        self.nameSelect.currentIndexChanged.connect(self.__onNameSelectChanged)
        self.valueInput.textChanged.connect(self.setValue)
        self.isBoldSwitch.stateChanged.connect(self.setIsBold)
        self.colorSelect.colorChanged.connect(self.setColor)

    def __onNameSelectChanged(self, index):
        data = self.nameSelect.itemData(index)
        if data is not None:
            self.setName(data)

    def setName(self, value):
        from watermarker.constants import CUSTOM_VALUE

        self.nameSelect.setCurrentIndex(self.nameSelect.findData(value))
        cfg.set(self.name_config, value)
        if value == CUSTOM_VALUE:
            self.valueInput.show()
        else:
            self.valueInput.hide()

    def setValue(self, value):
        self.valueInput.setText(value)
        cfg.set(self.value_config, value)

    def setIsBold(self, value):
        self.isBoldSwitch.setChecked(value)
        cfg.set(self.is_bold_config, value)

    def setColor(self, value: QColor):
        self.colorSelect.setColor(value)
        cfg.set(self.color_config, value)

    def hideCustom(self):
        self.isBoldSwitch.hide()
        self.colorSelect.hide()

    def showCustom(self):
        self.isBoldSwitch.show()
        self.colorSelect.show()


class LayoutElementsSettingCard(ExpandSettingCard):
    def __init__(
        self, icon: str | QIcon | fi, title: str, content: str = None, parent=None
    ):
        super().__init__(icon, title, content, parent)
        self.leftTop = LayoutElement("left_top", "左上", parent=self)
        self.leftBottom = LayoutElement("left_bottom", "左下", parent=self)
        self.rightTop = LayoutElement("right_top", "右上", parent=self)
        self.rightBottom = LayoutElement("right_bottom", "右下", parent=self)
        self.viewLayout.addWidget(self.leftTop)
        self.viewLayout.addWidget(self.leftBottom)
        self.viewLayout.addWidget(self.rightTop)
        self.viewLayout.addWidget(self.rightBottom)

        self._adjustViewSize()

    def hideCustom(self):
        self.leftTop.hideCustom()
        self.leftBottom.hideCustom()
        self.rightTop.hideCustom()
        self.rightBottom.hideCustom()

    def showCustom(self):
        self.leftTop.showCustom()
        self.leftBottom.showCustom()
        self.rightTop.showCustom()
        self.rightBottom.showCustom()


class MarginSettingCard(SettingCard):
    def __init__(self, icon: str | QIcon | FluentIconBase, title, parent=None):
        super().__init__(icon, title, parent=parent)
        self.hBoxLayout.addStretch(1)
        self.marginSwitch = SwitchButton(self)
        self.marginValueInput = SpinBox(self)
        self.marginValueInput.setRange(0, 30)
        self.hBoxLayout.addWidget(self.marginSwitch)
        self.hBoxLayout.addSpacing(12)
        self.hBoxLayout.addWidget(QLabel("宽度"))
        self.hBoxLayout.addSpacing(12)
        self.hBoxLayout.addWidget(self.marginValueInput)
        self.hBoxLayout.addSpacing(16)
        self.setSwitchValue(cfg.get(cfg.white_margin_enable))
        self.setValue(cfg.get(cfg.white_margin_width))
        self.marginSwitch.checkedChanged.connect(self.setSwitchValue)
        self.marginValueInput.valueChanged.connect(self.setValue)

    def setSwitchValue(self, value):
        cfg.set(cfg.white_margin_enable, value)
        self.marginSwitch.setChecked(value)

    def setValue(self, value):
        cfg.set(cfg.white_margin_width, value)
        self.marginValueInput.setValue(value)


class BasicSettingCard(SettingCardGroup):
    def __init__(self, parent=None):
        super().__init__("基础设置", parent=parent)
        self.focalSwitch = SwitchSettingCard(
            fi.TRANSPARENT,
            "显示 35mm 等效焦距",
            configItem=cfg.use_equivalent_focal_length,
            parent=self,
        )
        self.paddingSwitch = SwitchSettingCard(
            fi.TRANSPARENT,
            "填充到原始比例",
            configItem=cfg.padding_with_original_ratio,
            parent=self,
        )
        self.shadowSwitch = SwitchSettingCard(
            fi.TRANSPARENT, "添加阴影", configItem=cfg.shadow, parent=self
        )
        self.marginCard = MarginSettingCard(fi.TRANSPARENT, "白边设置", parent=self)
        self.fontCard = FontSettingCard(parent=self)
        self.addSettingCards(
            [
                self.focalSwitch,
                self.paddingSwitch,
                self.shadowSwitch,
                self.marginCard,
                self.fontCard,
            ]
        )


class FontSettingItem(QWidget):
    def __init__(self, cfg_item, title, parent=None) -> None:
        super().__init__(parent)
        self.cfg_item = cfg_item
        title = BodyLabel(title, self)
        hLayout = QHBoxLayout(self)
        hLayout.addWidget(title)
        hLayout.addStretch(1)
        self.fontLabel = QLabel(self)
        self.fontLabel.setText(cfg_item.value)
        hLayout.addWidget(self.fontLabel)
        self.button = PushButton("选择字体", parent=self)
        hLayout.addWidget(self.button)

        self.button.clicked.connect(self.__onClicked)

    def __onClicked(self):
        font, ok = QFileDialog.getOpenFileName(
            self.window(), "选择字体文件", filter="字体文件 (*.ttf *.otf)"
        )
        if ok:
            self.fontLabel.setText(font)
            cfg.set(self.cfg_item, font)


class FontSettingCard(ExpandGroupSettingCard):
    def __init__(self, parent=None):
        super().__init__(fi.FONT, "字体设置", parent=parent)
        self.fontButton = FontSettingItem(cfg.font, "普通文字", parent=self)
        self.boldFontButton = FontSettingItem(cfg.bold_font, "突出文字", parent=self)
        self.alternateFontButton = FontSettingItem(
            cfg.alternative_font, "备用文字", parent=self
        )
        self.alternateBoldFontButton = FontSettingItem(
            cfg.alternative_bold_font, "备用突出文字", parent=self
        )
        self.addGroupWidget(self.fontButton)
        self.addGroupWidget(self.boldFontButton)
        self.addGroupWidget(self.alternateFontButton)
        self.addGroupWidget(self.alternateBoldFontButton)

        # self._adjustViewSize()


class LayoutSettingCard(SettingCardGroup):
    def __init__(self, parent=None):
        from watermarker.image_processor import LAYOUT_PROCESSORS, Layout

        layout_texts = [LAYOUT_PROCESSORS[layout].LAYOUT_NAME for layout in Layout]
        super().__init__("布局设置", parent=parent)
        self.layoutTypeSelect = ComboBoxSettingCard(
            cfg.layout_type, fi.LAYOUT, "布局类型", texts=layout_texts, parent=self
        )
        self.logoSwitch = SwitchSettingCard(
            fi.PHOTO, "添加 Logo", configItem=cfg.logo_enable, parent=self
        )
        self.logoPosition = OptionsSettingCard(
            cfg.logo_position,
            fi.PHOTO,
            "Logo 位置",
            texts=["居左", "居右"],
            parent=self,
        )
        self.logoDirectory = PushSettingCard(
            "选择目录",
            fi.FOLDER,
            "Logo 目录",
            content=cfg.get(cfg.logo_directory),
            parent=self,
        )
        self.defaultLogo = PushSettingCard(
            "选择文件",
            fi.PHOTO,
            "默认 Logo",
            content=cfg.get(cfg.logo_default),
            parent=self,
        )
        self.layoutElements = LayoutElementsSettingCard(
            fi.LAYOUT, "布局元素", parent=self
        )

        self.addSettingCards(
            [
                self.layoutTypeSelect,
                self.logoSwitch,
                self.logoPosition,
                self.logoDirectory,
                self.defaultLogo,
                self.layoutElements,
            ]
        )

        self.logoDirectory.clicked.connect(self.__onLogoDirectoryClicked)
        self.defaultLogo.clicked.connect(self.__onDefaultLogoClicked)
        cfg.layout_type.valueChanged.connect(self.__onLayoutTypeChanged)
        self.__onLayoutTypeChanged(cfg.get(cfg.layout_type))

    def __onLayoutTypeChanged(self, value):
        from watermarker.config import Layout

        if value == Layout.CUSTOM.value:
            self.layoutElements.showCustom()
            self.logoSwitch.show()
            self.logoPosition.show()
        else:
            self.layoutElements.hideCustom()
            self.logoSwitch.hide()
            self.logoPosition.hide()

    def __onLogoDirectoryClicked(self):
        directory = QFileDialog.getExistingDirectory(
            self, "选择 Logo 目录", cfg.logo_directory.value
        )
        if directory:
            cfg.set(cfg.logo_directory, directory)
            self.logoDirectory.setContent(directory)

    def __onDefaultLogoClicked(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "选择默认 Logo", cfg.logo_default.value
        )
        if file:
            cfg.set(cfg.logo_default, file)
            self.defaultLogo.setContent(file)


class SettingInterface(ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        parent = self.scroll_widget = QWidget()
        self.layout = ExpandLayout(parent)
        self.layout.addWidget(BasicSettingCard(parent))
        self.layout.addWidget(LayoutSettingCard(parent))

        self.__init_widget()

    def __init_widget(self):
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidget(self.scroll_widget)
        self.setWidgetResizable(True)
