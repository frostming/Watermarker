import enum
from pathlib import Path
from typing import Annotated, Literal

from PIL import Image, ImageFont
from pydantic import (
    AfterValidator,
    BaseModel,
    Field,
    PositiveInt,
    model_validator,
)


def _validate_hex_color(value: str) -> str:
    if not value.startswith("#") or len(value) != 7:
        raise ValueError("Invalid hex color")
    return value


def _fix_width(value: int) -> int:
    if value > 30:
        return 30
    if value < 0:
        return 0
    return value


HexColor = Annotated[str, AfterValidator(_validate_hex_color)]


class FocalLengthConfig(BaseModel):
    use_equivalent_focal_length: bool = False


class SwitchConfig(BaseModel):
    enable: bool = False


class WhiteMarginConfig(SwitchConfig):
    width: Annotated[int, AfterValidator(_fix_width)] = 3


class BaseConfig(BaseModel):
    bold_font: str
    font: str
    bold_font_size: PositiveInt = 1
    font_size: PositiveInt = 1
    quality: PositiveInt = 100
    focal_length: FocalLengthConfig = Field(default_factory=FocalLengthConfig)
    padding_with_original_ratio: SwitchConfig = Field(default_factory=SwitchConfig)
    shadow: SwitchConfig = Field(default_factory=SwitchConfig)
    white_margin: WhiteMarginConfig = Field(default_factory=WhiteMarginConfig)


class Element(BaseModel):
    color: HexColor
    is_bold: bool
    name: str
    value: str = ""

    @model_validator(mode="after")
    def validate_custom_value(self) -> None:
        if self.name == "Custom" and not self.value:
            raise ValueError("Custom value must not be empty")
        return self


class Elements(BaseModel):
    left_bottom: Element
    left_top: Element
    right_bottom: Element
    right_top: Element


class Layout(enum.Enum):
    SQUARE = "square"
    WATERMARK_RIGHT_LOGO = "watermark_right_logo"
    WATERMARK_LEFT_LOGO = "watermark_left_logo"
    DARK_WATERMARK_RIGHT_LOGO = "dark_watermark_right_logo"
    DARK_WATERMARK_LEFT_LOGO = "dark_watermark_left_logo"
    CUSTOM = "custom"
    SIMPLE = "simple"
    BACKGROUND_BLUR = "background_blur"
    BACKGROUND_BLUR_WHITE_BORDER = "background_blur_white_border"
    PURE_WHITE_MARGIN = "pure_white_margin"


class LayoutConfig(BaseModel):
    background_color: HexColor
    elements: Elements
    type: Layout = Layout.WATERMARK_LEFT_LOGO


class LogoConfig(BaseModel):
    directory: Path
    default: Path
    enable: bool = True
    position: Literal["left", "right"] = "left"


class Config(BaseModel, extra="allow"):
    base: BaseConfig
    layout: LayoutConfig
    logo: LogoConfig

    def model_post_init(self, _context) -> None:
        self.bg_color = self.layout.background_color
        self._logos = {}

    @classmethod
    def load(cls, path: str | Path) -> "Config":
        path = Path(path)
        if path.suffix in (".json"):
            return cls.model_validate_json(path.read_bytes())

        import yaml

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls.model_validate(data)

    def save(self, path: str | Path) -> None:
        import yaml

        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(self.model_dump(), f)

    def get_font_padding_level(self):
        bold_font_size = (
            self.base.bold_font_size if 1 <= self.base.bold_font_size <= 3 else 1
        )
        font_size = self.base.font_size if 1 <= self.base.font_size <= 3 else 1
        return bold_font_size + font_size

    def get_font_size(self):
        return get_font_size(self.base.font_size)

    def get_bold_font_size(self):
        return get_bold_font_size(self.base.bold_font_size)

    def get_font(self):
        return ImageFont.truetype(self.base.font, self.get_font_size())

    def get_bold_font(self):
        return ImageFont.truetype(self.base.bold_font, self.get_bold_font_size())

    def load_logo(self, make: str) -> Image.Image:
        """
        根据厂商获取 logo
        :param make: 厂商
        :return: logo
        """
        if make in self._logos:
            return self._logos[make]

        logo_path = next(
            self.logo.directory.glob(f"{make.lower()}.*"), self.logo.default
        )

        logo = Image.open(logo_path)
        self._logos[make] = logo
        return logo


def get_font_size(level: int) -> int:
    if level < 1:
        return 240
    if level > 3:
        return 300
    return [240, 250, 300][level - 1]


def get_font_level(size: int) -> int:
    if size <= 240:
        return 1
    elif size <= 300:
        return 2
    return 3


def get_bold_font_level(size: int) -> int:
    if size <= 260:
        return 1
    elif size <= 290:
        return 2
    return 3


def get_bold_font_size(level: int) -> int:
    if level < 1:
        return 260
    if level > 3:
        return 320
    return [260, 290, 320][level - 1]
