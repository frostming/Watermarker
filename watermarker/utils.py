from __future__ import annotations

import enum
import logging
import os
import platform
import re
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Iterable, Literal, Sequence, Tuple, Union, overload

from PIL import Image, ImageDraw, ImageOps

from .constants import TRANSPARENT

if TYPE_CHECKING:
    from PIL.ImageFont import FreeTypeFont


Color = Union[Tuple[float, ...], str]
Side = Literal["left", "right"]

MAC_BUNDLE_IDENTIFIER = "dev.fming.watermarker"


def get_base_path():
    if sys.platform == "darwin":
        from AppKit import NSBundle

        bundle = NSBundle.mainBundle()
        if bundle.bundleIdentifier() == MAC_BUNDLE_IDENTIFIER:
            bundle_path = bundle.bundlePath()
            return os.path.join(bundle_path, "Contents", "Resources")
    return os.curdir


BASE_PATH = get_base_path()
if platform.system() == "Windows":
    EXIFTOOL_PATH = Path(BASE_PATH, "exiftool/exiftool.exe")
else:
    EXIFTOOL_PATH = Path(BASE_PATH, "exiftool/exiftool")


class Align(enum.IntEnum):
    CENTER = 0
    END = 1
    START = 2


class Axis(enum.IntEnum):
    HORIZONTAL = 0
    VERTICAL = 1


logger = logging.getLogger(__name__)


def get_file_list(path: str) -> list[Path]:
    """
    获取 jpg 文件列表
    :param path: 路径
    :return: 文件名
    """
    path = Path(path)
    if not path.exists():
        return []
    return [
        file_path
        for file_path in path.iterdir()
        if file_path.is_file()
        and file_path.suffix in [".jpg", ".jpeg", ".JPG", ".JPEG", ".png", ".PNG"]
    ]


def get_exif(path: str | Path) -> dict[str, str]:
    """
    获取exif信息
    :param path: 照片路径
    :return: exif信息
    """
    exif_dict = {}
    try:
        output_bytes = subprocess.check_output(
            [EXIFTOOL_PATH, "-d", "%Y-%m-%d %H:%M:%S%3f%z", str(path)]
        )
        output = output_bytes.decode("utf-8", errors="ignore")

        lines = output.splitlines()
        utf8_lines = [line for line in lines]

        for line in utf8_lines:
            # 将每一行按冒号分隔成键值对
            kv_pair = line.split(":", 1)
            if len(kv_pair) < 2:
                continue
            key = kv_pair[0].strip()
            value = kv_pair[1].strip()
            # 将键中的空格移除
            key = re.sub(r"\s+", "", key)
            key = re.sub(r"/", "", key)
            # 将键值对添加到字典中
            exif_dict[key] = value
        for key, value in exif_dict.items():
            # 过滤非 ASCII 字符
            value_clean = "".join(c for c in value if ord(c) < 128)
            # 将处理后的值更新到 exif_dict 中
            exif_dict[key] = value_clean
    except Exception as e:
        logger.error(f"get_exif error: {path} : {e}")

    return exif_dict


def insert_exif(source_path: Path, target_path: Path) -> None:
    """
    复制照片的 exif 信息
    :param source_path: 源照片路径
    :param target_path: 目的照片路径
    """
    try:
        # 将 exif 信息转换为字节串
        subprocess.check_output(
            [
                EXIFTOOL_PATH,
                "-tagsfromfile",
                source_path,
                "-overwrite_original",
                target_path,
            ]
        )
    except ValueError as e:
        logger.exception(f"ValueError: {source_path}: cannot insert exif {str(e)}")


def remove_white_edge(image: Image.Image) -> Image.Image:
    """
    移除图片白边
    :param image: 图片对象
    :return: 移除白边后的图片对象
    """
    # 获取像素信息
    pixels = image.load()

    # 获取图像大小
    width, height = image.size

    # 计算最小的 X、Y、最大的 X、Y 坐标
    min_x, min_y = width - 1, height - 1
    max_x, max_y = 0, 0
    for y in range(height):
        for x in range(width):
            if pixels[x, y] != (255, 255, 255):
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)

    # 裁剪图像
    new_image = image.crop((min_x, min_y, max_x + 1, max_y + 1))
    return new_image


def concatenate_image(
    images: Iterable[Image.Image], align: Align = Align.START
) -> Image.Image:
    """
    将多张图片拼接成一列
    :param images: 图片对象列表
    :param align: 对齐方向，left/center/right
    :return: 拼接后的图片对象
    """
    widths, heights = zip(*(i.size for i in images))

    sum_height = sum(heights)
    max_width = max(widths)

    new_img = Image.new("RGBA", (max_width, sum_height), color=TRANSPARENT)

    x_offset = 0
    y_offset = 0
    if align == Align.START:
        for img in images:
            new_img.paste(img, (0, y_offset))
            y_offset += img.height
    elif align == Align.CENTER:
        for img in images:
            x_offset = int((max_width - img.width) / 2)
            new_img.paste(img, (x_offset, y_offset))
            y_offset += img.height
    else:
        for img in images:
            x_offset = max_width - img.width  # 右对齐
            new_img.paste(img, (x_offset, y_offset))
            y_offset += img.height
    return new_img


@overload
def padding_image(
    image: None, padding_size: int, padding_location: str = ..., color: Color = ...
) -> None: ...


@overload
def padding_image(
    image: Image.Image,
    padding_size: int,
    padding_location: str = ...,
    color: Color = ...,
) -> Image.Image: ...


def padding_image(
    image: Image.Image | None,
    padding_size: int,
    padding_location: str = "tb",
    color: Color = TRANSPARENT,
) -> Image.Image | None:
    """
    在图片四周填充白色像素
    :param image: 图片对象
    :param padding_size: 填充像素大小
    :param padding_location: 填充位置，top/bottom/left/right
    :return: 填充白色像素后的图片对象
    """
    if image is None:
        return None

    total_width, total_height = image.size
    x_offset, y_offset = 0, 0
    if "t" in padding_location:
        total_height += padding_size
        y_offset += padding_size
    if "b" in padding_location:
        total_height += padding_size
    if "l" in padding_location:
        total_width += padding_size
        x_offset += padding_size
    if "r" in padding_location:
        total_width += padding_size

    padding_img = Image.new("RGBA", (total_width, total_height), color=color)
    padding_img.paste(image, (x_offset, y_offset))
    return padding_img


def square_image(image: Image.Image, auto_close: bool = True) -> Image.Image:
    """
    将图片按照正方形进行填充
    :param auto_close: 是否自动关闭图片对象
    :param image: 图片对象
    :return: 填充后的图片对象
    """
    # 计算图片的宽度和高度
    width, height = image.size
    if width == height:
        return image

    # 计算需要填充的白色区域大小
    delta_w = abs(width - height)
    padding = (delta_w // 2, 0) if width < height else (0, delta_w // 2)

    square_img = ImageOps.expand(image, padding, fill="white")

    if auto_close:
        image.close()

    # 返回正方形图片对象
    return square_img


def resize_image_with_height(
    image: Image.Image, height: int, auto_close: bool = True
) -> Image.Image:
    """
    按照高度对图片进行缩放
    :param image: 图片对象
    :param height: 指定高度
    :return: 按照高度缩放后的图片对象
    """
    # 获取原始图片的宽度和高度
    width, old_height = image.size

    # 计算缩放后的宽度
    scale = height / old_height
    new_width = round(width * scale)

    # 进行等比缩放
    resized_image = image.resize((new_width, height), Image.LANCZOS)

    # 关闭图片对象
    if auto_close:
        image.close()

    # 返回缩放后的图片对象
    return resized_image


def resize_image_with_width(
    image: Image.Image, width: int, auto_close: bool = True
) -> Image.Image:
    """
    按照宽度对图片进行缩放
    :param image: 图片对象
    :param width: 指定宽度
    :return: 按照宽度缩放后的图片对象
    """
    # 获取原始图片的宽度和高度
    old_width, height = image.size

    # 计算缩放后的宽度
    scale = width / old_width
    new_height = round(height * scale)

    # 进行等比缩放
    resized_image = image.resize((width, new_height), Image.LANCZOS)

    # 关闭图片对象
    if auto_close:
        image.close()

    # 返回缩放后的图片对象
    return resized_image


def append_image_by_side(
    background: Image.Image,
    images: Sequence[Image.Image],
    side: Side = "left",
    padding: int = 200,
    is_start: bool = False,
) -> None:
    """
    将图片横向拼接到背景图片中
    :param background: 背景图片对象
    :param images: 图片对象列表
    :param side: 拼接方向，left/right
    :param padding: 图片之间的间距
    :param is_start: 是否在最左侧添加 padding
    :return: 拼接后的图片对象
    """
    if side == "right":
        if is_start:
            x_offset = background.width - padding
        else:
            x_offset = background.width
        for i in reversed(images):
            if i is None:
                continue
            i = resize_image_with_height(i, background.height, auto_close=False)
            x_offset -= i.width
            x_offset -= padding
            background.paste(i, (x_offset, 0))
    else:
        if is_start:
            x_offset = padding
        else:
            x_offset = 0
        for i in images:
            if i is None:
                continue
            i = resize_image_with_height(i, background.height, auto_close=False)
            background.paste(i, (x_offset, 0))
            x_offset += i.width
            x_offset += padding


def text_to_image(
    content: str,
    font: FreeTypeFont,
    bold_font: FreeTypeFont,
    is_bold: bool = False,
    fill: str = "black",
) -> Image.Image:
    """
    将文字内容转换为图片
    """
    if is_bold:
        font = bold_font
    if content == "":
        content = "   "
    _, _, text_width, text_height = font.getbbox(content)
    image = Image.new("RGBA", (text_width, text_height), color=TRANSPARENT)
    draw = ImageDraw.Draw(image)
    draw.text((0, 0), content, fill=fill, font=font)
    return image


def merge_images(
    images: Iterable[Image.Image],
    axis: Axis = Axis.HORIZONTAL,
    align: Align = Align.CENTER,
) -> Image.Image:
    """
    拼接多张图片
    :param images: 图片对象列表
    :param axis: 0 水平拼接，1 垂直拼接
    :param align: 0 居中对齐，1 底部/右对齐，2 顶部/左对齐
    :return: 拼接后的图片对象
    """
    # 获取每张图像的 size
    widths, heights = zip(*(img.size for img in images))

    # 计算输出图像的尺寸
    if axis == Axis.HORIZONTAL:  # 水平拼接
        total_width = sum(widths)
        max_height = max(heights)
    else:  # 垂直拼接
        total_width = max(widths)
        max_height = sum(heights)

    # 创建输出图像
    output_image = Image.new("RGBA", (total_width, max_height), color=TRANSPARENT)

    # 拼接图像
    x_offset, y_offset = 0, 0
    for img in images:
        if axis == Axis.HORIZONTAL:  # 水平拼接
            if align == Align.END:  # 底部对齐
                y_offset = max_height - img.size[1]
            elif align == Align.START:  # 顶部对齐
                y_offset = 0
            else:  # 居中排列
                y_offset = (max_height - img.size[1]) // 2
            output_image.paste(img, (x_offset, y_offset))
            x_offset += img.size[0]
        else:  # 垂直拼接
            if align == Align.END:  # 右对齐
                x_offset = total_width - img.size[0]
            elif align == Align.START:  # 左对齐
                x_offset = 0
            else:  # 居中排列
                x_offset = (total_width - img.size[0]) // 2
            output_image.paste(img, (x_offset, y_offset))
            y_offset += img.size[1]

    return output_image


def calculate_pixel_count(width: int, height: int) -> str:
    # 计算像素总数
    pixel_count = width * height
    # 计算百万像素数
    megapixel_count = pixel_count / 1000000.0
    # 返回结果字符串
    return f"{megapixel_count:.2f} MP"


def extract_attribute(
    data_dict: dict[str, str],
    *keys: str,
    default_value: str = "",
    prefix: str = "",
    suffix: str = "",
) -> str:
    """
    从字典中提取对应键的属性值

    :param data_dict: 包含属性值的字典
    :param keys: 一个或多个键
    :param default_value: 默认值，默认为空字符串
    :return: 对应的属性值或空字符串
    """
    for key in keys:
        if key in data_dict:
            return prefix + data_dict[key] + suffix
    return default_value


def extract_gps_lat_and_long(lat: str, long: str) -> tuple[str, str]:
    # 提取出纬度和经度主要部分
    lat_deg, _, lat_min = re.findall(r"(\d+ deg \d+)", lat)[0].split()
    long_deg, _, long_min = re.findall(r"(\d+ deg \d+)", long)[0].split()

    # 提取出方向（北 / 南 / 东 / 西）
    lat_dir = re.findall(r"([NS])", lat)[0]
    long_dir = re.findall(r"([EW])", long)[0]

    latitude = f"{lat_deg}°{lat_min}'{lat_dir}"
    longitude = f"{long_deg}°{long_min}'{long_dir}"

    return latitude, longitude


def extract_gps_info(gps_info: str) -> tuple[str, str]:
    lat, long = gps_info.split(", ")
    return extract_gps_lat_and_long(lat, long)
