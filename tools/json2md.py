#!/usr/bin/env python3
"""json2md.py — 将 stt JSON 转录导出文件转换为 Markdown 演讲稿文章。

用法:
    python tools/json2md.py <input> [options]

将 stt 导出的 JSON 音频转录文件转换为结构化的 Markdown 文章（第一章：原文）。
支持单文件转换和批量目录转换。
"""

import argparse
import json
import logging
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# T008: logging 模块配置
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# T005: SRT 时间戳解析器
# ---------------------------------------------------------------------------
_SRT_PATTERN = re.compile(r"^(\d{2}):(\d{2}):(\d{2}),(\d{3})$")


def parse_srt_time(time_str: str) -> float:
    """将 SRT 格式时间戳 'HH:MM:SS,mmm' 转换为秒数（float）。

    Args:
        time_str: SRT 格式时间字符串，例如 '00:01:23,456'

    Returns:
        对应的秒数，例如 83.456

    Raises:
        ValueError: 时间字符串格式不正确时抛出
    """
    match = _SRT_PATTERN.match(time_str.strip())
    if not match:
        raise ValueError(f"无效的 SRT 时间戳格式: '{time_str}'")
    hours, minutes, seconds, millis = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(millis) / 1000.0


# ---------------------------------------------------------------------------
# T007: UTF-8 编码验证（文件读取）
# ---------------------------------------------------------------------------
def read_file_utf8(file_path: Path) -> str:
    """以严格 UTF-8 编码读取文件内容。

    Args:
        file_path: 要读取的文件路径

    Returns:
        文件的文本内容

    Raises:
        SystemExit: 文件包含无效 UTF-8 编码时，输出错误信息并以退出码 2 退出
        FileNotFoundError: 文件不存在时抛出
    """
    try:
        return file_path.read_text(encoding="utf-8", errors="strict")
    except UnicodeDecodeError:
        logger.error("Error: %s contains invalid UTF-8 encoding", file_path)
        sys.exit(2)


# ---------------------------------------------------------------------------
# T006: JSON 验证函数
# ---------------------------------------------------------------------------
_REQUIRED_FIELDS = {"line", "start_time", "end_time", "text"}


def validate_stt_export(raw_text: str, file_path: Path) -> list[dict]:
    """验证输入文本是合法的 stt JSON 导出格式，并返回解析后的段落列表。

    验证规则（参考 data-model.md TranscriptionExport）：
    - 根元素必须是 JSON 数组
    - 数组至少包含 1 个元素
    - 每个元素必须包含 line(int)、start_time(str)、end_time(str)、text(str) 字段
    - text 字段去除空白后不能为空

    Args:
        raw_text: JSON 文件的原始文本内容
        file_path: 文件路径（仅用于错误消息）

    Returns:
        解析后的 segment 字典列表

    Raises:
        SystemExit: JSON 格式无效或不符合 stt 导出格式时，以退出码 2 退出
    """
    # 解析 JSON
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as e:
        logger.error("Error: Invalid JSON in %s: %s", file_path, e)
        sys.exit(2)

    # 根元素必须是数组
    if not isinstance(data, list):
        logger.error(
            "Error: %s is not a valid stt JSON export (missing required fields)",
            file_path,
        )
        sys.exit(2)

    # 数组不能为空
    if len(data) == 0:
        logger.error(
            "Error: %s is not a valid stt JSON export (missing required fields)",
            file_path,
        )
        sys.exit(2)

    # 逐个验证每个 segment
    for i, segment in enumerate(data):
        if not isinstance(segment, dict):
            logger.error(
                "Error: %s is not a valid stt JSON export (missing required fields)",
                file_path,
            )
            sys.exit(2)

        missing = _REQUIRED_FIELDS - segment.keys()
        if missing:
            logger.error(
                "Error: %s is not a valid stt JSON export (missing required fields)",
                file_path,
            )
            sys.exit(2)

        # 类型检查
        if not isinstance(segment["line"], int) or segment["line"] <= 0:
            logger.error(
                "Error: %s is not a valid stt JSON export (missing required fields)",
                file_path,
            )
            sys.exit(2)

        if not isinstance(segment["text"], str) or not segment["text"].strip():
            logger.error(
                "Error: %s is not a valid stt JSON export (missing required fields)",
                file_path,
            )
            sys.exit(2)

        # 验证时间戳格式（调用 parse_srt_time 确认格式正确）
        for time_field in ("start_time", "end_time"):
            if not isinstance(segment[time_field], str):
                logger.error(
                    "Error: %s is not a valid stt JSON export (missing required fields)",
                    file_path,
                )
                sys.exit(2)
            try:
                parse_srt_time(segment[time_field])
            except ValueError:
                logger.error(
                    "Error: %s is not a valid stt JSON export (missing required fields)",
                    file_path,
                )
                sys.exit(2)

    return data


# ---------------------------------------------------------------------------
# T010: 段落合并算法
# ---------------------------------------------------------------------------

# 句末标点符号集合 — 遇到这些标点时断开段落
_SENTENCE_ENDINGS = set("。！？.!?")

# 子句标点 — 段落较长时可在这些标点处断开
_CLAUSE_ENDINGS = set(",，;；、：:")

# 所有可断开标点（句末 + 子句）
_ALL_BREAK_PUNCTS = _SENTENCE_ENDINGS | _CLAUSE_ENDINGS

# 合并阈值常量
_GAP_THRESHOLD = 2.0       # 秒 — 相邻 segment 时间间隔（硬断开）
_TARGET_PARA_LEN = 100     # 字符 — 段落目标长度（遇到标点时断开）
_MAX_PARAGRAPH_LEN = 200   # 字符 — 段落最大长度（遇到任何标点即断开）
_HARD_MAX_LEN = 250        # 字符 — 段落绝对上限（强制在 segment 边界断开）


def _find_break_point(text: str, start: int, min_pos: int) -> int:
    """在文本中从 start 位置开始，向后查找最佳断开点。

    优先在句末标点后断开，其次在子句标点后断开。
    返回断开位置（断开点之后的字符索引），如果找不到返回 -1。
    """
    # 从 min_pos 开始搜索（确保段落不会太短）
    search_start = max(start, min_pos)
    best = -1
    for i in range(search_start, len(text)):
        if text[i] in _SENTENCE_ENDINGS:
            return i + 1  # 句末标点：立即断开
        if text[i] in _CLAUSE_ENDINGS and best == -1:
            best = i + 1  # 子句标点：记录但继续找句末标点
            # 但不要找太远，最多再看 50 个字符
    return best


def merge_segments(segments: list[dict]) -> list[dict]:
    """将碎片化的转录 segment 合并为自然段落。

    采用两阶段策略（针对口语转录中标点稀少的特点）：

    阶段 1 — 粗合并：基于时间间隔将 segment 合并为粗段落
      - 相邻 segment 时间间隔 ≥ 2 秒时断开

    阶段 2 — 精分段：在粗段落内部基于标点和长度进行智能分段
      - 段落长度 ≥ 150 字符时，在句末标点（。！？）处断开
      - 段落长度 ≥ 300 字符时，在子句标点（,，;；、）处断开
      - 段落长度 ≥ 500 字符时，强制断开

    参考：research.md §R2、FR-004、data-model.md Paragraph

    Args:
        segments: 经过验证的 segment 字典列表，每个包含
                  line, start_time, end_time, text 字段

    Returns:
        段落字典列表，每个包含:
        - text (str): 合并后的文本
        - start_time (str): 段落首个 segment 的 start_time
        - end_time (str): 段落末个 segment 的 end_time
        - segment_count (int): 合并的原始 segment 数量
    """
    if not segments:
        return []

    # ── 阶段 1：基于时间间隔粗合并 ──
    # 构建字符偏移量到 segment 索引的映射，用于阶段 2 回溯时间戳
    coarse_groups: list[list[int]] = []  # 每组是 segment 索引列表
    current_group = [0]

    for i in range(1, len(segments)):
        gap = (parse_srt_time(segments[i]["start_time"])
               - parse_srt_time(segments[i - 1]["end_time"]))
        if gap >= _GAP_THRESHOLD:
            coarse_groups.append(current_group)
            current_group = [i]
        else:
            current_group.append(i)
    coarse_groups.append(current_group)

    # ── 阶段 2：在每个粗组内基于标点和长度精分段 ──
    paragraphs: list[dict] = []

    for group in coarse_groups:
        # 合并组内所有 segment 文本，同时记录每个字符对应的 segment 索引
        full_text = ""
        char_to_seg: list[int] = []  # char_to_seg[i] = segment 索引
        for seg_idx in group:
            seg_text = segments[seg_idx]["text"].strip()
            char_to_seg.extend([seg_idx] * len(seg_text))
            full_text += seg_text

        if not full_text.strip():
            continue

        # 在 full_text 中寻找断开点
        para_start = 0
        while para_start < len(full_text):
            remaining = len(full_text) - para_start

            # 如果剩余文本不长，直接作为最后一段
            if remaining <= _TARGET_PARA_LEN:
                break

            # 尝试在目标长度附近找句末标点
            search_end = min(para_start + _HARD_MAX_LEN, len(full_text))
            break_pos = -1

            # 优先：在 [TARGET, MAX] 范围内找句末标点
            for i in range(para_start + _TARGET_PARA_LEN, search_end):
                if full_text[i] in _SENTENCE_ENDINGS:
                    break_pos = i + 1
                    break

            # 次选：在 [MAX, HARD_MAX] 范围内找子句标点
            if break_pos == -1:
                for i in range(para_start + _TARGET_PARA_LEN, search_end):
                    if full_text[i] in _CLAUSE_ENDINGS:
                        break_pos = i + 1
                        break

            # 兜底：在 segment 边界处断开（比在字符中间断开更自然）
            if break_pos == -1:
                target_pos = para_start + _HARD_MAX_LEN
                # 从目标位置向前找最近的 segment 边界
                best_seg_break = -1
                if target_pos < len(char_to_seg):
                    for j in range(target_pos, para_start + _TARGET_PARA_LEN, -1):
                        if j < len(char_to_seg) and j > 0 and char_to_seg[j] != char_to_seg[j - 1]:
                            best_seg_break = j
                            break
                if best_seg_break > para_start:
                    break_pos = best_seg_break
                else:
                    break_pos = min(para_start + _HARD_MAX_LEN, len(full_text))

            # 提取段落文本
            para_text = full_text[para_start:break_pos].strip()
            if para_text:
                # 回溯时间戳：段落首字符和末字符对应的 segment
                first_seg_idx = char_to_seg[para_start]
                last_seg_idx = char_to_seg[min(break_pos - 1, len(char_to_seg) - 1)]
                # 计算段落包含的 segment 数量
                seg_indices = set(char_to_seg[para_start:break_pos])
                paragraphs.append({
                    "text": para_text,
                    "start_time": segments[first_seg_idx]["start_time"],
                    "end_time": segments[last_seg_idx]["end_time"],
                    "segment_count": len(seg_indices),
                })

            para_start = break_pos

        # 处理最后一段
        if para_start < len(full_text):
            para_text = full_text[para_start:].strip()
            if para_text:
                first_seg_idx = char_to_seg[para_start]
                last_seg_idx = char_to_seg[-1]
                seg_indices = set(char_to_seg[para_start:])
                paragraphs.append({
                    "text": para_text,
                    "start_time": segments[first_seg_idx]["start_time"],
                    "end_time": segments[last_seg_idx]["end_time"],
                    "segment_count": len(seg_indices),
                })

    return paragraphs


# ---------------------------------------------------------------------------
# T011: Markdown 格式化函数
# ---------------------------------------------------------------------------


def format_article(
    filename: str,
    segments: list[dict],
    paragraphs: list[dict],
) -> str:
    """将合并后的段落格式化为完整的 Chapter 1 Markdown 文档。

    输出结构（参考 research.md §R3、cli-contract.md Output Format）：
    - H1 标题: {filename} — 演讲稿与内容分析
    - 元数据块: Source, Segments, Duration
    - --- 分隔线
    - H2 第一章：原文
    - 段落正文（段落间空行分隔）

    Args:
        filename: 源 JSON 文件名（不含路径，含扩展名）
        segments: 原始 segment 列表（用于统计信息）
        paragraphs: merge_segments 返回的段落列表

    Returns:
        完整的 Markdown 文档字符串
    """
    stem = Path(filename).stem
    total_segments = len(segments)
    total_paragraphs = len(paragraphs)

    # 计算时长范围
    if segments:
        first_start = segments[0]["start_time"]
        last_end = segments[-1]["end_time"]
    else:
        first_start = "00:00:00,000"
        last_end = "00:00:00,000"

    # 时间戳格式化：去掉毫秒部分用于显示 (HH:MM:SS,mmm → HH:MM:SS)
    duration_start = first_start.split(",")[0]
    duration_end = last_end.split(",")[0]

    lines: list[str] = []

    # H1 标题
    lines.append(f"# {stem} — 演讲稿与内容分析")
    lines.append("")

    # 元数据块
    lines.append(f"**Source**: {filename}")
    lines.append(
        f"**Segments**: {total_segments} (merged into ~{total_paragraphs} paragraphs)"
    )
    lines.append(f"**Duration**: {duration_start} → {duration_end}")
    lines.append("")

    # 分隔线
    lines.append("---")
    lines.append("")

    # H2 第一章
    lines.append("## 第一章：原文")
    lines.append("")

    # 段落正文
    for para in paragraphs:
        lines.append(para["text"])
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# T012: 输出文件写入与冲突解决
# ---------------------------------------------------------------------------


def resolve_output_path(
    input_path: Path,
    output_dir: Path | None,
    overwrite: bool,
) -> Path | None:
    """计算输出文件路径，处理文件名冲突。

    规则（参考 cli-contract.md、FR-009、FR-010）：
    - 输出文件名 = 输入文件 stem + .md
    - 如果指定了 output_dir，则输出到该目录；否则与输入文件同目录
    - 如果文件已存在且 overwrite=False：追加数字后缀 _1, _2, ...
    - 如果文件已存在且 overwrite=True：直接覆盖

    Args:
        input_path: 输入 JSON 文件路径
        output_dir: 用户指定的输出目录（None 表示与输入同目录）
        overwrite: 是否覆盖已存在的文件

    Returns:
        最终的输出文件路径；如果文件已存在且跳过则返回 None
    """
    stem = input_path.stem
    target_dir = output_dir if output_dir else input_path.parent
    output_path = target_dir / f"{stem}.md"

    if not output_path.exists():
        return output_path

    if overwrite:
        return output_path

    # 文件已存在且不覆盖 — 追加数字后缀
    counter = 1
    while True:
        candidate = target_dir / f"{stem}_{counter}.md"
        if not candidate.exists():
            logger.warning(
                "Warning: %s already exists, writing to %s",
                output_path,
                candidate,
            )
            return candidate
        counter += 1


def write_output(content: str, output_path: Path) -> None:
    """将 Markdown 内容写入输出文件。

    Args:
        content: 完整的 Markdown 文档字符串
        output_path: 输出文件路径
    """
    # 确保输出目录存在
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    logger.info("Output: %s", output_path)


# ---------------------------------------------------------------------------
# T013: 单文件转换编排器
# ---------------------------------------------------------------------------


def convert_single(
    input_path: Path,
    output_dir: Path | None = None,
    overwrite: bool = False,
) -> int:
    """将单个 JSON 转录文件转换为 Markdown 文章（Chapter 1）。

    编排流程：读取文件(UTF-8) → 验证 JSON → 合并段落 → 格式化文章 → 写入输出。

    Args:
        input_path: 输入 JSON 文件路径
        output_dir: 输出目录（None 表示与输入同目录）
        overwrite: 是否覆盖已存在的输出文件

    Returns:
        退出码：0=成功，2=致命错误
    """
    logger.info("Converting: %s", input_path.name)

    # 1. 读取文件（UTF-8 严格模式）
    try:
        raw_text = read_file_utf8(input_path)
    except FileNotFoundError:
        logger.error("Error: File not found: %s", input_path)
        return 2

    # 2. 验证 JSON 格式
    segments = validate_stt_export(raw_text, input_path)

    # 3. 合并段落
    paragraphs = merge_segments(segments)
    logger.info(
        "Merged %d segments into %d paragraphs",
        len(segments),
        len(paragraphs),
    )

    # 4. 格式化 Markdown 文章
    content = format_article(input_path.name, segments, paragraphs)

    # 5. 计算输出路径
    out_path = resolve_output_path(input_path, output_dir, overwrite)
    if out_path is None:
        # 不应到达此处（resolve_output_path 总是返回路径）
        return 0

    # 6. 写入输出文件
    write_output(content, out_path)

    return 0


# ---------------------------------------------------------------------------
# T020/T021: 批量转换与错误处理
# ---------------------------------------------------------------------------


def convert_batch(
    dir_path: Path,
    output_dir: Path | None = None,
    overwrite: bool = False,
) -> int:
    """批量转换目录下所有 JSON 文件为 Markdown 文章（Chapter 1）。

    扫描指定目录（非递归）中的所有 *.json 文件，逐个调用 convert_single 进行转换。
    单个文件失败时记录错误并继续处理剩余文件。

    Args:
        dir_path: 包含 JSON 文件的目录路径
        output_dir: 输出目录（None 表示与输入同目录）
        overwrite: 是否覆盖已存在的输出文件

    Returns:
        退出码：0=全部成功，1=部分失败，2=致命错误（无 JSON 文件）
    """
    # 扫描目录下的 *.json 文件（非递归，参考 FR-008）
    json_files = sorted(dir_path.glob("*.json"))

    if not json_files:
        logger.error("Error: No JSON files found in %s", dir_path)
        return 2

    total = len(json_files)
    success_count = 0
    fail_count = 0

    for i, json_file in enumerate(json_files, 1):
        logger.info("Converting %d/%d: %s", i, total, json_file.name)
        try:
            exit_code = convert_single(json_file, output_dir, overwrite)
            if exit_code == 0:
                success_count += 1
            else:
                fail_count += 1
        except SystemExit:
            # convert_single 内部的 validate/read 可能调用 sys.exit
            # 在批量模式下捕获并继续
            fail_count += 1
            logger.error("Error processing %s, skipping", json_file.name)

    # 输出摘要报告
    if fail_count == 0:
        logger.info("Converted %d/%d files", success_count, total)
        return 0
    else:
        logger.error(
            "Completed with errors: %d/%d files failed",
            fail_count,
            total,
        )
        return 1


# ---------------------------------------------------------------------------
# T009: argparse CLI 接口
# ---------------------------------------------------------------------------


def build_arg_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器。

    Returns:
        配置好的 ArgumentParser 实例
    """
    parser = argparse.ArgumentParser(
        prog="json2md",
        description="将 stt JSON 转录导出文件转换为 Markdown 演讲稿文章（第一章：原文）。",
        epilog=(
            "示例:\n"
            "  python tools/json2md.py Export/audio.json\n"
            "  python tools/json2md.py Export/audio.json -o output/\n"
            "  python tools/json2md.py Export/ -f\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "input",
        help="JSON 文件路径或包含 JSON 文件的目录路径",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        default=None,
        help="输出目录（默认：与输入文件相同目录）",
    )
    parser.add_argument(
        "--overwrite",
        "-f",
        action="store_true",
        default=False,
        help="覆盖已存在的输出文件（默认：跳过并追加数字后缀）",
    )
    return parser


def main():
    """主入口函数。"""
    parser = build_arg_parser()
    args = parser.parse_args()

    input_path = Path(args.input)

    # 验证输入路径存在
    if not input_path.exists():
        logger.error("Error: File not found: %s", input_path)
        sys.exit(2)

    # 解析输出目录
    output_dir = Path(args.output_dir) if args.output_dir else None

    # 根据输入类型分发处理（单文件 / 目录）
    if input_path.is_file():
        # T014: 单文件模式
        exit_code = convert_single(input_path, output_dir, args.overwrite)
        sys.exit(exit_code)
    elif input_path.is_dir():
        # T022: 目录批量模式
        exit_code = convert_batch(input_path, output_dir, args.overwrite)
        sys.exit(exit_code)
    else:
        logger.error("Error: File not found: %s", input_path)
        sys.exit(2)


if __name__ == "__main__":
    main()
