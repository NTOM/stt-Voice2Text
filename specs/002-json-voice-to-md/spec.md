# Feature Specification: JSON Voice Transcription to Markdown Article & Analysis

**Feature Branch**: `002-json-voice-to-md`  
**Created**: 2026-03-31  
**Updated**: 2026-03-31 (post-clarification)  
**Status**: Clarified  
**Input**: User description: "创建一个自定义的 command，将导出的 JSON 音频转录转化为 Markdown 演讲稿文章，并生成内容分析总结报告"  
**Clarifications**: See [clarifications.md](./clarifications.md) for full Q&A record

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate Article from JSON Transcription (Priority: P1)

A user has completed audio transcription using the stt tool and exported the result in JSON format. They want to convert the fragmented subtitle segments into a **coherent, publishable article** (演讲稿) — suitable for notes, blog posts, or documentation — rather than a raw subtitle listing.

**Why this priority**: This is the core value proposition — transforming raw transcription fragments into a readable, flowing article is the fundamental operation that enables all downstream use cases.

**Independent Test**: Can be fully tested by providing a single exported JSON file and verifying the output Markdown Chapter 1 contains all transcription text merged into natural paragraphs without timestamps.

**Acceptance Scenarios**:

1. **Given** a valid JSON transcription export file, **When** the user runs the conversion command, **Then** a Markdown file is generated with Chapter 1 containing all transcription text merged into coherent natural paragraphs.
2. **Given** a JSON file with many short segments (1-3 seconds each), **When** the conversion is performed, **Then** consecutive segments are intelligently merged based on punctuation and time gaps, forming flowing paragraphs rather than individual lines.
3. **Given** a JSON file with speaker/audio metadata, **When** the conversion is performed, **Then** the metadata is included as a header section, and the article body reads as a natural speech transcript.
4. **Given** a JSON file with 695 segments from a 22-minute recording, **When** the conversion is performed, **Then** the output article has significantly fewer paragraphs (e.g., ~50-120) that are semantically coherent.

---

### User Story 2 - AI-Powered Content Analysis & Summary (Priority: P1)

After generating the article (Chapter 1), the user wants an **intelligent analysis summary** (Chapter 2) that extracts the core theme, key arguments, and other relevant insights — structured like a research summary or executive briefing, with the structure dynamically adapted to the content.

**Why this priority**: The analysis chapter is equally important as the article — it transforms a long transcript into actionable knowledge. Users need this for quick review, sharing key takeaways, or creating study notes.

**Independent Test**: Can be tested by providing a generated Chapter 1 article and verifying Chapter 2 contains at minimum a "主题" and "核心观点" section, plus at least one dynamically chosen section relevant to the content.

**Acceptance Scenarios**:

1. **Given** a generated Chapter 1 article, **When** the AI analysis is performed, **Then** Chapter 2 contains a "主题" section with a one-sentence topic summary.
2. **Given** a generated Chapter 1 article, **When** the AI analysis is performed, **Then** Chapter 2 contains a "核心观点" section listing the key arguments/viewpoints.
3. **Given** an article about a technical topic with examples, **When** the AI analysis is performed, **Then** Chapter 2 dynamically includes a "论据与案例" section.
4. **Given** an article with actionable advice, **When** the AI analysis is performed, **Then** Chapter 2 dynamically includes a "行动建议" section.
5. **Given** a long article that exceeds the AI context window, **When** the analysis is triggered, **Then** the system warns the user about the length, splits the content by semantic paragraphs, analyzes each segment, and merges the results into a unified summary.

---

### User Story 3 - Batch Convert Multiple JSON Files (Priority: P2)

A user has exported multiple audio transcription results as individual JSON files. They want to convert all of them to Markdown articles in a single operation (Chapter 1 only; Chapter 2 analysis is per-file via the AI command).

**Why this priority**: Batch processing saves significant time for the article generation step. AI analysis (Chapter 2) is handled separately per file through the CodeBuddy command.

**Independent Test**: Can be tested by providing a directory containing multiple JSON export files and verifying each one produces a corresponding Markdown article file.

**Acceptance Scenarios**:

1. **Given** a directory containing multiple JSON transcription files, **When** the user runs the batch conversion command, **Then** each JSON file produces a corresponding Markdown article (Chapter 1).
2. **Given** a batch conversion in progress, **When** one file fails to convert, **Then** the process continues with remaining files and reports the failure at the end.

---

### Edge Cases

- What happens when the JSON file is empty or contains no transcription segments?
- How does the system handle a JSON file that is not a valid stt export (wrong schema)?
- What happens when the JSON contains non-UTF-8 characters or special Unicode?
- How does the system handle extremely large JSON files (e.g., hours-long recordings)?
- What happens when the output Markdown file already exists at the target path?
- What happens when the generated article exceeds the IDE AI's context window limit?
- How does the system handle content that doesn't have clear arguments or themes (e.g., casual conversation)?

## Requirements *(mandatory)*

### Functional Requirements

#### Chapter 1 — Article Generation (Rule-Based)

- **FR-001**: The command MUST accept a JSON file path as input and produce a Markdown file as output.
- **FR-002**: The command MUST parse the stt JSON export format and extract all transcription segments with their timestamps.
- **FR-003**: The command MUST generate a Markdown document with a metadata header (source file name, segment count, duration range) as the document preamble.
- **FR-004**: The command MUST merge consecutive transcription segments into natural paragraphs using rule-based logic: merge when time gap between segments is less than 2 seconds AND no sentence-ending punctuation (。！？.!?) terminates the current segment AND the current paragraph length is under 500 characters (safety cap to prevent excessively long paragraphs).
- **FR-005**: The merged article (Chapter 1) MUST read as a coherent speech transcript / article, suitable for notes or publication, without individual timestamps interrupting the flow.
- **FR-006**: The command MUST preserve the original text content exactly as it appears in the JSON — merging affects paragraph structure only, not the words themselves.
- **FR-007**: The command MUST validate that the input file is a valid stt JSON export before attempting conversion, and provide a clear error message if not.
- **FR-008**: The command MUST support batch mode — accepting a directory path and converting all JSON files directly within it (non-recursive; subdirectories are not traversed).
- **FR-009**: The command MUST allow the user to specify an output directory; if not specified, the Markdown file is written alongside the source JSON file.
- **FR-010**: The command MUST handle filename conflicts by appending a numeric suffix (e.g., `output_1.md`) rather than overwriting existing files, unless an overwrite flag is explicitly set.
- **FR-017**: The command MUST require input JSON files to be valid UTF-8 encoded. If the file contains invalid UTF-8 byte sequences, the command MUST reject the file with a clear encoding error message and exit code 2.

#### Chapter 2 — Content Analysis (AI-Powered via CodeBuddy Command)

- **FR-011**: The CodeBuddy command (`jsonvoice2md.md`) MUST invoke the Python script to generate Chapter 1, then use the IDE's built-in AI to analyze the content and generate Chapter 2.
- **FR-012**: Chapter 2 MUST contain two mandatory sections: "主题"（a one-sentence topic summary）and "核心观点"（a numbered list of key arguments/viewpoints）.
- **FR-013**: Chapter 2 MUST dynamically include additional sections from an optional pool based on content relevance. The optional pool includes but is not limited to: "论据与案例", "关键数据", "争议与反思", "行动建议", "关键引用".
- **FR-014**: The command MUST detect when the Chapter 1 content exceeds the AI context window limit and display an informational warning (non-blocking) to the user, then automatically proceed with the splitting strategy.
- **FR-015**: When content exceeds the limit, the command MUST split the article by semantic paragraph groups (keeping each group within the context window), analyze each group separately, and merge the analysis results into a unified Chapter 2.
- **FR-016**: The AI analysis prompt MUST instruct the model to adapt the Chapter 2 structure to the content — not use a rigid template — while always including the two mandatory sections.
- **FR-018**: When the CodeBuddy command is executed on a Markdown file that already contains Chapter 2 (i.e., a `## 第二章：内容分析` heading exists), the command MUST replace the existing Chapter 2 content rather than appending a duplicate. This ensures idempotent re-execution.

### Key Entities

- **JSON Transcription Export**: The source file produced by stt's export feature; contains an array of segments, each with `line`, `start_time`, `end_time`, and `text`.
- **Markdown Article Document**: The output file; a two-chapter document:
  - **Chapter 1 (原文)**: Coherent article merged from transcription segments
  - **Chapter 2 (内容分析)**: AI-generated analysis with mandatory and dynamic sections
- **Transcription Segment**: A single unit of transcribed speech with a time range and text content.
- **Paragraph**: A merged group of consecutive segments forming a natural text block.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can generate a Chapter 1 article from a single JSON export in under 5 seconds for files up to 1 hour of transcription.
- **SC-002**: The generated Chapter 1 reads as a natural, flowing article — not a list of subtitle fragments — and is suitable for notes or publication without manual editing.
- **SC-003**: 100% of transcription text content from the JSON is preserved in the Chapter 1 output (no data loss; only paragraph structure is changed).
- **SC-004**: Chapter 2 always contains "主题" and "核心观点" sections, plus at least one dynamically chosen section relevant to the content.
- **SC-005**: For content exceeding the AI context window, the system displays an informational warning about the content length, then automatically proceeds to split, analyze, and merge results without requiring user confirmation or intervention.
- **SC-006**: Batch conversion of 50 files (Chapter 1 only) completes without manual intervention, with clear progress indication.
- **SC-007**: Users unfamiliar with the tool can successfully run the command on their first attempt using only the command help/documentation.

## Assumptions

- The input JSON files follow the stt project's existing export format (as produced by the current export functionality in `index.html`).
- Users have access to the exported JSON files on their local filesystem.
- The feature is implemented as two components:
  1. **`tools/json2md.py`**: Standalone Python CLI script for Chapter 1 generation (rule-based, offline, no dependencies)
  2. **`.codebuddy/commands/jsonvoice2md.md`**: AI command definition that orchestrates the full workflow (Chapter 1 + Chapter 2)
- Chapter 1 generation is fully offline; Chapter 2 analysis requires the IDE's built-in AI capability (CodeBuddy).
- The rule-based paragraph merging (2-second gap threshold + punctuation detection) produces acceptable article quality for most speech transcripts.
- The IDE AI's context window is the primary constraint for Chapter 2; the semantic paragraph splitting strategy handles this gracefully.
- The dynamic structure of Chapter 2 (必选项 + 可选项池) provides sufficient consistency while allowing content-appropriate flexibility.
