# Quickstart: JSON Voice Transcription to Markdown Article & Analysis

## Prerequisites

- Python 3.9+ (already installed if running stt)
- CodeBuddy IDE (for Chapter 2 AI analysis)
- No additional pip dependencies required

## Two Ways to Use

### Option A: Full Experience (Article + AI Analysis) — Recommended

Use the CodeBuddy command for the complete two-chapter output:

```
/jsonvoice2md Export/your-audio-file.json
```

This generates:
- **Chapter 1 (原文)**: Coherent article merged from transcription segments
- **Chapter 2 (内容分析)**: AI-powered analysis with theme, key arguments, and dynamic sections

### Option B: Article Only (CLI Tool)

Use the Python script directly for Chapter 1 only (no AI needed):

```bash
python tools/json2md.py Export/your-audio-file.json
```

This is also useful for **batch processing** multiple files:

```bash
python tools/json2md.py Export/
```

## Example Output

Given a JSON file with 695 transcription segments from a 22-minute recording:

```markdown
# 为什么你的Agent总翻车？Harness Engineering全拆解：Ant — 演讲稿与内容分析

**Source**: 为什么你的Agent总翻车？Harness Engineering全拆解：Ant.json
**Segments**: 695 (merged into ~80 paragraphs)
**Duration**: 00:00:00 → 00:22:28

---

## 第一章：原文

大家好,今天我们聊一个2026年上半年AI工程圈里升温速度最快的概念,
Hardness Engineering。先说结论,如果你现在还停留在怎么写一条更好的
prompt这个层面去做agent,那今天这集视频你一定要看完。

因为prompt只是冰山一角,真正决定你的agent能不能在生产环境里稳定运行的,
是一整套叫做Hardness Engineering的工程方法论。...

---

## 第二章：内容分析

### 主题
Harness Engineering 是一种超越 Prompt Engineering 的系统性 AI Agent
工程方法论。

### 核心观点
1. Prompt Engineering 只是冰山一角
2. Harness Engineering 包含上下文管理、工具编排、错误恢复等实践
3. ...

### 概念解释
- **Harness Engineering**: ...
- **Context Engineering**: ...

### 行动建议
1. 从 Prompt 思维升级到 Harness 思维
2. ...
```

## CLI Options

| Option | Description |
|---|---|
| `<input>` | JSON file or directory path (required) |
| `-o, --output-dir` | Custom output directory |
| `-f, --overwrite` | Overwrite existing files |

## Long Content Handling

For recordings longer than ~30 minutes, the AI analysis may need to split the content:

1. The system will **warn you** about the content length
2. It automatically **splits by semantic paragraphs** (never mid-paragraph)
3. Each segment is **analyzed separately**
4. Results are **merged into a unified Chapter 2**

No manual intervention needed — just acknowledge the warning and let it process.
