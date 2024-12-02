import string

from PIL import Image, ImageFilter, ImageOps

from .config import Config, Layout
from .constants import GRAY, NONE_VALUE, TRANSPARENT
from .image_container import ImageContainer
from .utils import (
    Align,
    Axis,
    append_image_by_side,
    concatenate_images,
    padding_image,
    resize_image_with_height,
    resize_image_with_width,
    square_image,
    text_to_image,
)

printable = set(string.printable)

NORMAL_HEIGHT = 1000
SMALL_HORIZONTAL_GAP = Image.new("RGBA", (50, 20), color=TRANSPARENT)
MIDDLE_HORIZONTAL_GAP = Image.new("RGBA", (100, 20), color=TRANSPARENT)
LARGE_HORIZONTAL_GAP = Image.new("RGBA", (200, 20), color=TRANSPARENT)
SMALL_VERTICAL_GAP = Image.new("RGBA", (20, 50), color=TRANSPARENT)
MIDDLE_VERTICAL_GAP = Image.new("RGBA", (20, 100), color=TRANSPARENT)
LARGE_VERTICAL_GAP = Image.new("RGBA", (20, 200), color=TRANSPARENT)
LINE_GRAY = Image.new("RGBA", (20, 1000), color=GRAY)
LINE_TRANSPARENT = Image.new("RGBA", (20, 1000), color=TRANSPARENT)


class ProcessorComponent:
    """
    图片处理器组件
    """

    LAYOUT_ID: Layout | None = None
    LAYOUT_NAME: str | None = None

    def __init__(self, config: Config):
        self.config = config

    def process(self, container: ImageContainer) -> None:
        """
        处理图片容器中的 watermark_img，将处理后的图片放回容器中
        """
        raise NotImplementedError

    def add(self, component):
        raise NotImplementedError


class ProcessorChain(ProcessorComponent):
    def __init__(self, config: Config):
        super().__init__(config)
        self.components = []

    def add(self, component: ProcessorComponent) -> None:
        self.components.append(component)

    def process(self, container: ImageContainer) -> None:
        for component in self.components:
            component.process(container)


class EmptyProcessor(ProcessorComponent):
    def process(self, container: ImageContainer) -> None:
        pass


class ShadowProcessor(ProcessorComponent):
    def process(self, container: ImageContainer) -> None:
        # 加载图像
        image = container.get_watermark_img()

        max_pixel = max(image.width, image.height)
        # 计算阴影边框大小
        radius = int(max_pixel / 512)

        # 创建阴影效果
        shadow = Image.new("RGB", image.size, color="#6B696A")
        shadow = ImageOps.expand(
            shadow,
            border=(radius * 2, radius * 2, radius * 2, radius * 2),
            fill=(255, 255, 255),
        )
        # 模糊阴影
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=radius))

        # 将原始图像放置在阴影图像上方
        shadow.paste(image, (radius, radius))
        container.update_watermark_img(shadow)


class SquareProcessor(ProcessorComponent):
    LAYOUT_ID = Layout.SQUARE
    LAYOUT_NAME = "1:1填充"

    def process(self, container: ImageContainer) -> None:
        image = container.get_watermark_img()
        container.update_watermark_img(square_image(image, auto_close=False))


class StandardProcessor(ProcessorComponent):
    LAYOUT_ID = Layout.STANDARD
    LAYOUT_NAME = "标准"

    def __init__(self, config: Config):
        super().__init__(config)
        # 默认值
        self.logo_position = config.logo.position
        self.logo_enable = config.logo.enable
        self.bg_color = config.layout.background_color
        self.font_color_lt = config.layout.foreground_color
        self.bold_font_lt = config.layout.elements.left_top.is_bold
        self.font_color_lb = config.layout.foreground_color
        self.bold_font_lb = config.layout.elements.left_bottom.is_bold
        self.font_color_rt = config.layout.foreground_color
        self.bold_font_rt = config.layout.elements.right_top.is_bold
        self.font_color_rb = config.layout.foreground_color
        self.bold_font_rb = config.layout.elements.right_bottom.is_bold

    def is_logo_left(self):
        return self.logo_position == "left"

    def process(self, container: ImageContainer) -> None:
        """
        生成一个默认布局的水印图片
        :param container: 图片对象
        :return: 添加水印后的图片对象
        """
        config = self.config
        config.bg_color = self.bg_color

        # 下方水印的占比
        ratio = (
            0.07 if container.get_ratio() >= 1 else 0.1
        ) + 0.02 * config.get_font_padding_level()

        # 创建一个空白的水印图片
        watermark = Image.new(
            "RGBA", (int(NORMAL_HEIGHT / ratio), NORMAL_HEIGHT), color=self.bg_color
        )

        with Image.new("RGBA", (10, 100), color=self.bg_color) as empty_padding:
            # 填充左边的文字内容
            left_parts = []
            if config.layout.elements.left_top.name != NONE_VALUE:
                left_parts.append(
                    text_to_image(
                        container.get_attribute_str(config.layout.elements.left_top),
                        config.get_font(),
                        config.get_bold_font(),
                        is_bold=self.bold_font_lt,
                        fill=self.font_color_lt,
                    )
                )
            if config.layout.elements.left_bottom.name != NONE_VALUE:
                if left_parts:
                    left_parts.append(empty_padding)
                left_parts.append(
                    text_to_image(
                        container.get_attribute_str(config.layout.elements.left_bottom),
                        config.get_font(),
                        config.get_bold_font(),
                        is_bold=self.bold_font_lb,
                        fill=self.font_color_lb,
                    )
                )
            left = concatenate_images(left_parts, Axis.VERTICAL, Align.START)
            # 填充右边的文字内容
            right_parts = []
            if config.layout.elements.right_top.name != NONE_VALUE:
                right_parts.append(
                    text_to_image(
                        container.get_attribute_str(config.layout.elements.right_top),
                        config.get_font(),
                        config.get_bold_font(),
                        is_bold=self.bold_font_rt,
                        fill=self.font_color_rt,
                    )
                )
            if config.layout.elements.right_bottom.name != NONE_VALUE:
                if right_parts:
                    right_parts.append(empty_padding)
                right_parts.append(
                    text_to_image(
                        container.get_attribute_str(
                            config.layout.elements.right_bottom
                        ),
                        config.get_font(),
                        config.get_bold_font(),
                        is_bold=self.bold_font_rb,
                        fill=self.font_color_rb,
                    )
                )
            right = concatenate_images(right_parts, Axis.VERTICAL, Align.START)

        logo = config.load_logo(container.make)
        if self.logo_enable:
            if self.is_logo_left():
                # 如果 logo 在左边
                append_image_by_side(watermark, [logo, left], padding=(300, 200))
                append_image_by_side(
                    watermark, [right], side="right", padding=(300, 200)
                )
            else:
                # 如果 logo 在右边
                if logo is not None:
                    # 插入一根线条用于分割 logo 和文字
                    height = max(logo.height, left.height, right.height)
                    line = Image.new("RGBA", (20, height), color=GRAY)
                else:
                    line = LINE_TRANSPARENT.copy()
                append_image_by_side(watermark, [left], padding=(300, 200))
                append_image_by_side(
                    watermark, [logo, line, right], side="right", padding=(300, 200)
                )
                line.close()
        else:
            append_image_by_side(watermark, [left], padding=(300, 200))
            append_image_by_side(watermark, [right], side="right", padding=(300, 200))
        left.close()
        right.close()

        # 缩放水印的大小
        watermark = resize_image_with_width(watermark, container.get_width())
        # 将水印图片放置在原始图片的下方
        bg = ImageOps.expand(
            container.get_watermark_img().convert("RGBA"),
            border=(0, 0, 0, watermark.height),
            fill=self.bg_color,
        )
        fg = ImageOps.expand(
            watermark, border=(0, container.get_height(), 0, 0), fill=TRANSPARENT
        )
        result = Image.alpha_composite(bg, fg)
        watermark.close()
        # 更新图片对象
        result = ImageOps.exif_transpose(result).convert("RGB")
        container.update_watermark_img(result)


class MarginProcessor(ProcessorComponent):
    def process(self, container: ImageContainer) -> None:
        config = self.config
        padding_size = int(
            config.base.white_margin.width
            * min(container.get_width(), container.get_height())
            / 100
        )
        padding_img = padding_image(
            container.get_watermark_img(), padding_size, "tlr", color=config.bg_color
        )
        container.update_watermark_img(padding_img)


class SimpleProcessor(ProcessorComponent):
    LAYOUT_ID = Layout.SIMPLE
    LAYOUT_NAME = "简洁"

    def process(self, container: ImageContainer) -> None:
        ratio = 0.16 if container.get_ratio() >= 1 else 0.1
        padding_ratio = 0.5 if container.get_ratio() >= 1 else 0.5

        first_text = text_to_image(
            "Shot on",
            self.config.get_font(),
            self.config.get_bold_font(),
            is_bold=False,
            fill="#212121",
        )
        model = text_to_image(
            container.get_model().replace(r"/", " ").replace(r"_", " "),
            self.config.get_font(),
            self.config.get_bold_font(),
            is_bold=True,
            fill="#D32F2F",
        )
        make = text_to_image(
            container.get_make().split(" ")[0],
            self.config.get_font(),
            self.config.get_bold_font(),
            is_bold=True,
            fill="#212121",
        )
        first_line = concatenate_images(
            [first_text, MIDDLE_HORIZONTAL_GAP, model, MIDDLE_HORIZONTAL_GAP, make],
            Axis.HORIZONTAL,
            Align.END,
        )
        second_line_text = container.get_param_str()
        second_line = text_to_image(
            second_line_text,
            self.config.get_font(),
            self.config.get_bold_font(),
            is_bold=False,
            fill="#9E9E9E",
        )
        image = concatenate_images(
            [first_line, MIDDLE_VERTICAL_GAP, second_line], Axis.VERTICAL, Align.CENTER
        )
        height = container.get_height() * ratio * padding_ratio
        image = resize_image_with_height(image, int(height))
        horizontal_padding = int((container.get_width() - image.width) / 2)
        vertical_padding = int((container.get_height() * ratio - image.height) / 2)

        watermark = ImageOps.expand(
            image, (horizontal_padding, vertical_padding), fill=TRANSPARENT
        )
        bg = Image.new("RGBA", watermark.size, color="white")
        bg = Image.alpha_composite(bg, watermark)

        watermark_img = concatenate_images(
            [container.get_watermark_img(), bg], Axis.VERTICAL, Align.END
        )
        container.update_watermark_img(watermark_img)


class PaddingToOriginalRatioProcessor(ProcessorComponent):
    def process(self, container: ImageContainer) -> None:
        original_ratio = container.get_original_ratio()
        ratio = container.get_ratio()
        if original_ratio > ratio:
            # 如果原始比例大于当前比例，说明宽度大于高度，需要填充高度
            padding_size = int(
                container.get_width() / original_ratio - container.get_height()
            )
            padding_img = ImageOps.expand(
                container.get_watermark_img(), (0, padding_size), fill="white"
            )
        else:
            # 如果原始比例小于当前比例，说明高度大于宽度，需要填充宽度
            padding_size = int(
                container.get_height() * original_ratio - container.get_width()
            )
            padding_img = ImageOps.expand(
                container.get_watermark_img(), (padding_size, 0), fill="white"
            )
        container.update_watermark_img(padding_img)


PADDING_PERCENT_IN_BACKGROUND = 0.18
GAUSSIAN_KERNEL_RADIUS = 35


class BackgroundBlurProcessor(ProcessorComponent):
    LAYOUT_ID = Layout.BACKGROUND_BLUR
    LAYOUT_NAME = "背景模糊"

    def process(self, container: ImageContainer) -> None:
        background = container.get_watermark_img()
        background = background.filter(
            ImageFilter.GaussianBlur(radius=GAUSSIAN_KERNEL_RADIUS)
        )
        fg = Image.new("RGB", background.size, color=(255, 255, 255))
        background = Image.blend(background, fg, 0.1)
        background = background.resize(
            (
                int(container.get_width() * (1 + PADDING_PERCENT_IN_BACKGROUND)),
                int(container.get_height() * (1 + PADDING_PERCENT_IN_BACKGROUND)),
            )
        )
        background.paste(
            container.get_watermark_img(),
            (
                int(container.get_width() * PADDING_PERCENT_IN_BACKGROUND / 2),
                int(container.get_height() * PADDING_PERCENT_IN_BACKGROUND / 2),
            ),
        )
        container.update_watermark_img(background)


class BackgroundBlurWithWhiteBorderProcessor(ProcessorComponent):
    LAYOUT_ID = Layout.BACKGROUND_BLUR_WHITE_BORDER
    LAYOUT_NAME = "背景模糊+白框"

    def process(self, container: ImageContainer) -> None:
        padding_size = int(
            self.config.base.white_margin.width
            * min(container.get_width(), container.get_height())
            / 256
        )
        padding_img = padding_image(
            container.get_watermark_img(), padding_size, "tblr", color="white"
        )

        background = container.get_img()
        background = background.filter(
            ImageFilter.GaussianBlur(radius=GAUSSIAN_KERNEL_RADIUS)
        )
        background = background.resize(
            (
                int(padding_img.width * (1 + PADDING_PERCENT_IN_BACKGROUND)),
                int(padding_img.height * (1 + PADDING_PERCENT_IN_BACKGROUND)),
            )
        )
        fg = Image.new("RGB", background.size, color=(255, 255, 255))
        background = Image.blend(background, fg, 0.1)
        background.paste(
            padding_img,
            (
                int(padding_img.width * PADDING_PERCENT_IN_BACKGROUND / 2),
                int(padding_img.height * PADDING_PERCENT_IN_BACKGROUND / 2),
            ),
        )
        container.update_watermark_img(background)


class PureWhiteMarginProcessor(ProcessorComponent):
    LAYOUT_ID = Layout.PURE_WHITE_MARGIN
    LAYOUT_NAME = "白色边框"

    def process(self, container: ImageContainer) -> None:
        config = self.config
        padding_size = int(
            config.base.white_margin.width
            * min(container.get_width(), container.get_height())
            / 100
        )
        padding_img = padding_image(
            container.get_watermark_img(), padding_size, "tlrb", color=config.bg_color
        )
        container.update_watermark_img(padding_img)


LAYOUT_PROCESSORS = {
    p.LAYOUT_ID: p
    for p in globals().values()
    if isinstance(p, type) and issubclass(p, ProcessorComponent)
    if p.LAYOUT_ID is not None
}
