# Research: JSON Voice Transcription to Markdown Article & Analysis

**Feature**: 002-json-voice-to-md
**Date**: 2026-03-31
**Updated**: 2026-03-31 (post-clarification)

## Research Tasks

### R1: JSON Export Schema

**Task**: Confirm the exact JSON structure produced by stt's export feature.

**Finding**: The JSON export is a flat array of segment objects. Each segment has:
- `line` (int): Sequential line number starting from 1
- `start_time` (string): SRT-format timestamp `HH:MM:SS,mmm`
- `end_time` (string): SRT-format timestamp `HH:MM:SS,mmm`
- `text` (string): Transcribed text content

Example:
```json
[
  {"end_time":"00:00:06,380","line":1,"start_time":"00:00:00,000","text":"大家好..."},
  {"end_time":"00:00:12,560","line":2,"start_time":"00:00:07,120","text":"先说结论..."}
]
```

**Source**: `Export/为什么你的Agent总翻车？Harness Engineering全拆解：Ant.json` (695 segments, 71KB)

**Decision**: Parse as JSON array; validate each element has `line`, `start_time`, `end_time`, `text` keys.
**Rationale**: This is the only JSON format the stt tool produces. No versioning or schema variations exist.
**Alternatives considered**: None — single format.

---

### R2: Paragraph Merging Algorithm (Chapter 1 — Core)

**Task**: Design the rule-based algorithm to merge fragmented subtitle segments into coherent article paragraphs.

**Finding**: The stt tool produces very short segments (often 1-3 seconds each, single sentence fragments). Analysis of the sample file (695 segments, 22 minutes) shows:
- Average segment length: ~15-30 characters
- Time gaps between consecutive segments: typically 0-2 seconds
- Sentence-ending punctuation (。！？.!?) appears roughly every 3-5 segments

**Merging Algorithm**:
1. Initialize a new paragraph with the first segment's text
2. For each subsequent segment:
   - Calculate time gap = `next.start_time - current.end_time`
   - If gap < 2 seconds AND current paragraph doesn't end with sentence-ending punctuation (。！？.!?):
     - Append segment text to current paragraph (no separator needed — Chinese text flows naturally)
   - Else:
     - Close current paragraph, start a new one
3. Apply a max paragraph length cap (~500 characters) as safety valve
4. Strip leading/trailing whitespace from each paragraph

**Decision**: Rule-based merging with 2-second gap threshold + punctuation detection. This is the **default behavior** (not optional), as the core purpose is article generation.
**Rationale**: Produces natural paragraphs from speech segments without AI dependency. The 2-second threshold captures natural speech pauses while the punctuation detection respects sentence boundaries.
**Alternatives considered**:
- AI-driven rewriting — rejected per Q1 clarification: user chose rule-based approach
- Fixed segment count per paragraph — rejected: ignores semantic boundaries
- Always merge everything — rejected: produces wall-of-text without paragraph breaks

---

### R3: Markdown Output Structure (Two-Chapter Format)

**Task**: Design the two-chapter Markdown document structure.

**Finding**: Based on clarification results, the output is fundamentally different from the original subtitle-format design:

```markdown
# [Audio Filename] — 演讲稿与内容分析

**Source**: filename.json
**Segments**: 695 (merged into ~80 paragraphs)
**Duration**: 00:00:00 → 00:22:28

---

## 第一章：原文

大家好,今天我们聊一个2026年上半年AI工程圈里升温速度最快的概念,Hardness Engineering。先说结论,如果你现在还停留在怎么写一条更好的prompt这个层面去做agent,那今天这集视频你一定要看完。

因为prompt只是冰山一角,真正决定你的agent能不能在生产环境里稳定运行的,是一整套叫做Hardness Engineering的工程方法论。...

---

## 第二章：内容分析

### 主题
[由 AI 生成的一句话主题概括]

### 核心观点
1. [观点1]
2. [观点2]
...

### [动态章节标题]
[由 AI 根据内容动态生成的分析章节]
```

**Decision**: Two-chapter structure with H2 headings. Chapter 1 is plain paragraphs (no blockquotes, no timestamps). Chapter 2 uses H3 for sub-sections.
**Rationale**: Chapter 1 should read like a natural article — blockquotes and timestamps would break the reading flow. Chapter 2 uses structured headings for scannability.
**Alternatives considered**:
- Original blockquote-per-segment format — rejected per clarification: user wants article, not subtitles
- Single chapter with inline analysis — rejected: separating content from analysis is cleaner

---

### R4: Implementation Approach (Two-Component Architecture)

**Task**: Determine the implementation architecture given the two-chapter requirement.

**Finding**: Per Q3 clarification, the feature uses CodeBuddy's built-in AI for Chapter 2. This means:
- **Component 1**: `tools/json2md.py` — Python CLI script that generates Chapter 1 (rule-based paragraph merging)
- **Component 2**: `.codebuddy/commands/jsonvoice2md.md` — AI command that:
  1. Instructs CodeBuddy to run the Python script for Chapter 1
  2. Reads the generated Chapter 1 content
  3. Uses the IDE's AI to analyze and generate Chapter 2
  4. Appends Chapter 2 to the Markdown file

**Decision**: Two-component architecture: Python script + CodeBuddy command.
**Rationale**: Separates deterministic logic (merging) from AI logic (analysis). Python script can be used standalone for batch processing. CodeBuddy command provides the full experience.
**Alternatives considered**:
- All-in-Python with API calls — rejected per Q3: user wants to leverage IDE AI directly
- All-in-command (no Python script) — rejected: batch processing needs a standalone tool

---

### R5: Long Content Splitting Strategy (Chapter 2)

**Task**: Design the strategy for handling content that exceeds the AI context window.

**Finding**: Per Q4 clarification, the user chose semantic paragraph splitting. The workflow:

```
Chapter 1 content → Length check → Split by paragraph groups → Analyze each → Merge analyses
```

**Algorithm**:
1. Estimate token count of Chapter 1 content (rough: 1 Chinese char ≈ 1.5 tokens)
2. If total tokens < threshold (e.g., 6000 tokens for safety margin):
   - Analyze entire content at once
3. If total tokens >= threshold:
   - Display informational warning (non-blocking): "内容较长（约 N 字），将分 M 段进行分析"
   - Automatically proceed without waiting for user confirmation
   - Group consecutive paragraphs into chunks, each under the token limit
   - Never split a paragraph across chunks
   - Analyze each chunk with context: "这是第 X/M 段内容，请分析以下内容..."
   - Merge: Take union of all themes/viewpoints, deduplicate, synthesize

**Decision**: Semantic paragraph grouping with non-blocking informational warning (auto-proceed).
**Rationale**: Preserves semantic coherence within each chunk. Informational warning keeps user informed without requiring interactive confirmation (CodeBuddy commands do not support mid-execution user prompts). Paragraph-level splitting is natural since paragraphs are already semantically meaningful units.
**Alternatives considered**:
- Fixed token count splitting — rejected per Q4: may cut mid-paragraph
- Time-based splitting — rejected per Q4: paragraph boundaries are more natural

---

### R6: Chapter 2 Prompt Design (AI Analysis)

**Task**: Design the prompt template for the CodeBuddy command to generate Chapter 2.

**Finding**: Per Q5 clarification, the output uses a "必选项 + 可选项池" structure.

**Prompt Strategy**:
```
你是一位专业的内容分析师。请对以下演讲稿/文章进行深度分析，生成一份结构化的内容分析报告。

## 必选输出（必须包含）：
1. **主题**：用一句话概括文章的核心主题
2. **核心观点**：提取文章中的主要观点/论点，以编号列表形式呈现

## 可选输出（根据内容相关性选择，至少选择1项）：
- **论据与案例**：当文章包含具体案例、数据或论证时
- **关键数据**：当文章引用了重要的数字、统计或指标时
- **争议与反思**：当文章包含辩证讨论或不同观点时
- **行动建议**：当文章提供了可执行的建议或方法论时
- **关键引用**：当文章中有值得摘录的精彩语句时
- **概念解释**：当文章引入了专业术语或新概念时
- **时间线/流程**：当文章描述了时序事件或步骤流程时

## 要求：
- 结构要根据内容动态调整，不要生搬硬套
- 分析要精简而清晰，类似论文摘要的风格
- 使用中文输出
- 每个章节标题使用 ### 级别的 Markdown 标题
```

**Decision**: Structured prompt with mandatory + optional sections, Chinese output.
**Rationale**: Balances consistency (always have theme + viewpoints) with flexibility (dynamic sections based on content).
**Alternatives considered**:
- Fully free-form prompt — rejected per Q5: too inconsistent
- Rigid template — rejected per Q5: too inflexible

## Summary

All technical decisions resolved post-clarification. Key decisions:

| Decision | Choice | Key Reason |
|---|---|---|
| JSON schema | Flat array of `{line, start_time, end_time, text}` | Only format stt produces |
| Paragraph merging | Rule-based: 2s gap + punctuation detection (default) | Core feature, not optional |
| Output structure | Two chapters: 原文 + 内容分析 | User clarification |
| Architecture | Python script + CodeBuddy command | Separate deterministic from AI logic |
| AI integration | CodeBuddy IDE built-in LLM | User clarification (Q3) |
| Long content | Semantic paragraph grouping + warning | User clarification (Q4) |
| Chapter 2 structure | 必选项(主题+观点) + 可选项池 | User clarification (Q5) |
