from __future__ import annotations

import logging
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from tqdm import tqdm

from .config import Config, Layout
from .image_container import ImageContainer
from .image_processor import (
    LAYOUT_PROCESSORS,
    MarginProcessor,
    PaddingToOriginalRatioProcessor,
    ProcessorChain,
    ShadowProcessor,
)
from .utils import get_file_list

logger = logging.getLogger(__name__)


def process_one(processor_chain: ProcessorChain, image_file: Path, output: str) -> None:
    config = processor_chain.config
    # 打开图片
    with ImageContainer(image_file) as container:
        # 使用等效焦距
        container.is_use_equivalent_focal_length(
            config.base.focal_length.use_equivalent_focal_length
        )

        # 处理图片
        processor_chain.process(container)
        # 保存图片
        target_path = Path(output).joinpath(image_file.name)
        container.save(target_path, quality=config.base.quality)


def build_processor_chain(config: Config) -> ProcessorChain:
    processor_chain = ProcessorChain(config)

    layout_type = config.layout.type
    # 如果需要添加阴影，则添加阴影处理器，阴影处理器优先级最高，但是正方形布局不需要阴影
    if config.base.shadow.enable and layout_type != Layout.SQUARE:
        processor_chain.add(ShadowProcessor(config))

    # 根据布局添加不同的水印处理器
    if layout_type in LAYOUT_PROCESSORS:
        processor_chain.add(LAYOUT_PROCESSORS[layout_type](config))
    else:
        processor_chain.add(ShadowProcessor(config))

    # 如果需要添加白边，且是水印布局，则添加白边处理器，白边处理器优先级最低
    if config.base.white_margin.enable and layout_type == Layout.STANDARD:
        processor_chain.add(MarginProcessor(config))

    # 如果需要按原有比例填充，且不是正方形布局，则添加填充处理器
    if config.base.padding_with_original_ratio.enable and layout_type != Layout.SQUARE:
        processor_chain.add(PaddingToOriginalRatioProcessor(config))

    return processor_chain


def process(config: Config, input: str, output: str):
    """
    状态100：处理图片
    :return:
    """
    file_list = get_file_list(input)
    logger.info("当前共有 {} 张图片待处理".format(len(file_list)))

    def update(*a):
        # 这个函数将会在每个进程完成后被调用，用来更新进度条
        pbar.update()

    processor_chain = build_processor_chain(config)

    # 初始化tqdm进度条
    pbar = tqdm(total=len(file_list))

    # 设置进程池，最大进程数为5
    with ProcessPoolExecutor(5) as executor:
        for source_path in file_list:
            executor.submit(
                process_one, processor_chain, source_path, output
            ).add_done_callback(update)

    # 完成所有任务后，关闭tqdm进度条
    pbar.close()
