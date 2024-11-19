import os
from functools import lru_cache

from PyQt5.QtCore import QStandardPaths
from PyQt5.QtGui import QColor, QFont, QFontDatabase, QGuiApplication
from qfluentwidgets import (
    BoolValidator,
    ColorConfigItem,
    ConfigItem,
    ConfigValidator,
    FolderValidator,
    OptionsConfigItem,
    OptionsValidator,
    QConfig,
    RangeConfigItem,
    RangeValidator,
)
from qfluentwidgets.components.settings import options_setting_card, setting_card

from watermarker.config import Config as CoreConfig
from watermarker.config import Layout, get_font_level, get_font_size
from watermarker.constants import MODELS

MODEL_OPTIONS = list(MODELS.keys())


class FileValidator(ConfigValidator):
    def validate(self, value: str) -> bool:
        return os.path.isfile(value)


class ColorItem(ColorConfigItem):
    def serialize(self):
        return self.value.name(QColor.HexRgb)


class Config(QConfig):
    alternative_bold_font = ConfigItem(
        "base", "alternative_bold_font", "./fonts/Roboto-Medium.ttf"
    )
    alternative_font = ConfigItem(
        "base", "alternative_font", "./fonts/Roboto-Regular.ttf"
    )
    bold_font = ConfigItem("base", "bold_font", "./fonts/AlibabaPuHuiTi-2-85-Bold.otf")
    bold_font_size = OptionsConfigItem(
        "base", "bold_font_size", 1, OptionsValidator([1, 2, 3])
    )
    font = ConfigItem("base", "font", "./fonts/AlibabaPuHuiTi-2-45-Light.otf")
    font_size = ConfigItem("base", "font_size", 1, OptionsValidator([1, 2, 3]))
    quality = RangeConfigItem("base", "quality", 100, RangeValidator(1, 100))
    use_equivalent_focal_length = ConfigItem(
        "base",
        "focal_length.use_equivalent_focal_length",
        False,
        BoolValidator(),
    )
    padding_with_original_ratio = ConfigItem(
        "base",
        "padding_with_original_ratio.enable",
        False,
        BoolValidator(),
    )
    shadow = ConfigItem("base", "shadow.enable", False, BoolValidator())
    white_margin_enable = ConfigItem(
        "base", "white_margin.enable", True, BoolValidator()
    )
    white_margin_width = RangeConfigItem(
        "base", "white_margin.width", 3, RangeValidator(0, 30)
    )
    background_color = ColorItem("layout", "background_color", "#ffffff")
    left_bottom_color = ColorItem("layout.elements.left_bottom", "color", "#757575")
    left_bottom_is_bold = ConfigItem(
        "layout.elements.left_bottom", "is_bold", False, BoolValidator()
    )
    left_bottom_name = OptionsConfigItem(
        "layout.elements.left_bottom",
        "name",
        "Model",
        OptionsValidator(MODEL_OPTIONS),
    )
    left_bottom_value = ConfigItem("layout.elements.left_bottom", "value", "")
    left_top_color = ColorItem("layout.elements.left_top", "color", "#212121")
    left_top_is_bold = ConfigItem(
        "layout.elements.left_top", "is_bold", True, BoolValidator()
    )
    left_top_name = OptionsConfigItem(
        "layout.elements.left_top",
        "name",
        "LensModel",
        OptionsValidator(MODEL_OPTIONS),
    )
    left_top_value = ConfigItem("layout.elements.left_top", "value", "")
    right_bottom_color = ColorItem("layout.elements.right_bottom", "color", "#757575")
    right_bottom_is_bold = ConfigItem(
        "layout.elements.right_bottom", "is_bold", False, BoolValidator()
    )
    right_bottom_name = OptionsConfigItem(
        "layout.elements.right_bottom",
        "name",
        "Datetime",
        OptionsValidator(MODEL_OPTIONS),
    )
    right_bottom_value = ConfigItem("layout.elements.right_bottom", "value", "")
    right_top_color = ColorItem("layout.elements.right_top", "color", "#212121")
    right_top_is_bold = ConfigItem(
        "layout.elements.right_top", "is_bold", True, BoolValidator()
    )
    right_top_name = OptionsConfigItem(
        "layout.elements.right_top",
        "name",
        "Param",
        OptionsValidator(MODEL_OPTIONS),
    )
    right_top_value = ConfigItem("layout.elements.right_top", "value", "")
    layout_type = OptionsConfigItem(
        "layout",
        "type",
        "watermark_left_logo",
        OptionsValidator(l.value for l in Layout),
    )
    logo_enable = ConfigItem("logo", "enable", True, BoolValidator())
    logo_position = OptionsConfigItem(
        "logo", "position", "left", OptionsValidator(["left", "right"])
    )
    logo_default = ConfigItem(
        "logo", "default", "./logos/fujifilm.png", FileValidator()
    )
    logo_directory = ConfigItem("logo", "directory", "./logos/", FolderValidator())
    input_directory = ConfigItem(
        "base", "input_directory", "./input/", FolderValidator()
    )
    output_directory = ConfigItem(
        "base", "output_directory", "./output/", FolderValidator()
    )

    def get_font_path(self, font: str) -> str:
        font_paths = getFontPaths()[1]
        return font_paths.get(font, font)

    def as_core_config(self) -> CoreConfig:
        data = self.toDict()
        for side in ["left_top", "left_bottom", "right_top", "right_bottom"]:
            side_data = data.pop(f"layout.elements.{side}", None)
            data.setdefault("layout", {}).setdefault("elements", {})[side] = side_data
        data["base"]["focal_length"] = {
            "use_equivalent_focal_length": data["base"][
                "focal_length.use_equivalent_focal_length"
            ]
        }
        data["base"]["padding_with_original_ratio"] = {
            "enable": data["base"]["padding_with_original_ratio.enable"]
        }
        data["base"]["shadow"] = {"enable": data["base"]["shadow.enable"]}
        data["base"]["white_margin"] = {
            "enable": data["base"]["white_margin.enable"],
            "width": data["base"]["white_margin.width"],
        }
        for font_key in [
            "font",
            "bold_font",
            "alternative_font",
            "alternative_bold_font",
        ]:
            data["base"][font_key] = self.get_font_path(data["base"][font_key])
        return CoreConfig.model_validate(data)

    @property
    def qfont(self) -> QFont:
        dpi = QGuiApplication.primaryScreen().logicalDotsPerInch()
        font = QFont(self.font.value)
        font.setPixelSize(int(get_font_size(self.font_size.value) * 72 / dpi))
        return font

    @qfont.setter
    def qfont(self, font: QFont):
        self.font.value = font.family()
        self.font_size.value = get_font_level(font.pixelSize())
        self.save()

    @property
    def qbold_font(self) -> QFont:
        dpi = QGuiApplication.primaryScreen().logicalDotsPerInch()
        font = QFont(self.bold_font.value)
        font.setPixelSize(int(get_font_size(self.bold_font_size.value) * 72 / dpi))
        return font

    @qbold_font.setter
    def qbold_font(self, font: QFont):
        self.bold_font.value = font.family()
        self.bold_font_size.value = get_font_level(font.pixelSize())
        self.save()

    @property
    def qalternative_font(self) -> QFont:
        dpi = QGuiApplication.primaryScreen().logicalDotsPerInch()
        font = QFont(self.font.value)
        font.setPixelSize(int(get_font_size(self.font_size.value) * 72 / dpi))
        return font

    @qalternative_font.setter
    def qalternative_font(self, font: QFont):
        self.alternative_font.value = font.family()
        self.save()

    @property
    def qalternative_bold_font(self) -> QFont:
        dpi = QGuiApplication.primaryScreen().logicalDotsPerInch()
        font = QFont(self.bold_font.value)
        font.setPixelSize(int(get_font_size(self.bold_font_size.value) * 72 / dpi))
        return font

    @qalternative_bold_font.setter
    def qalternative_bold_font(self, font: QFont):
        self.alternative_bold_font.value = font.family()
        self.save()


cfg = Config()
cfg.load("config.json")
options_setting_card.qconfig = cfg
setting_card.qconfig = cfg


@lru_cache
def getFontPaths():
    font_paths = QStandardPaths.standardLocations(QStandardPaths.FontsLocation)

    accounted = []
    unloadable = []
    family_to_path = {}

    db = QFontDatabase()
    for fpath in font_paths:  # go through all font paths
        if not os.path.isdir(fpath):
            continue
        for filename in os.listdir(fpath):  # go through all files at each path
            path = os.path.join(fpath, filename)

            idx = db.addApplicationFont(path)  # add font path

            if idx < 0:
                unloadable.append(path)  # font wasn't loaded if idx is -1
            else:
                names = db.applicationFontFamilies(idx)  # load back font family name

                for n in names:
                    if n in family_to_path:
                        accounted.append((n, path))
                    else:
                        family_to_path[n] = path
                # this isn't a 1:1 mapping, for example
                # 'C:/Windows/Fonts/HTOWERT.TTF' (regular) and
                # 'C:/Windows/Fonts/HTOWERTI.TTF' (italic) are different
                # but applicationFontFamilies will return 'High Tower Text' for both
    return unloadable, family_to_path, accounted
