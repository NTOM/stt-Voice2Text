# Clarification Record: JSON Voice Transcription to Markdown Converter

**Feature**: 002-json-voice-to-md
**Date**: 2026-03-31
**Status**: ✅ All clarifications resolved

## Context

During the `speckit.clarify` workflow, a **major scope change** was identified. The original spec defined the output as a subtitle-format Markdown (preserving individual timestamped segments). The user clarified that the actual need is:

1. **第一章节（原文）**: 将零散字幕片段整合为一篇**连贯的演讲稿/文章**（可用于笔记或发表）
2. **第二章节（分析）**: 对文章内容进行**智能分析总结**——提取主题、观点、核心内容（论文式精简清晰），结构需根据内容动态调整

This fundamentally changes the feature from a "subtitle formatter" to an "article generator + content analyzer".

---

## Q1: 第一章节"演讲稿"的生成方式

**Category**: 功能范围与行为
**Impact**: High — 决定核心输出的生成方式

| Option | Description |
|--------|-------------|
| A | AI 驱动重写：调用 LLM API 将字幕片段重写为正式文章 |
| **B ✅** | **规则合并成文：按标点/时间间隔智能合并片段为自然段落，去除口语冗余** |
| C | 混合模式：先规则合并生成草稿，再可选调用 AI 润色 |

**User Choice**: **B — 规则合并成文**

**Rationale**: stt 的字幕片段本身已经是完整的口语句子，只需去除时间戳、合并连续片段、按语义断句分段即可形成流畅文章，无需 AI 介入，保持离线和零依赖的优势。

**Spec Impact**: 
- FR-007（保留原文）需重新定义：不再是逐段保留，而是合并为连贯段落
- 新增段落合并算法需求
- 第一章节输出格式从"带时间戳的块引用"变为"自然段落文章"

---

## Q2: 第二章节"内容分析总结"的实现方式

**Category**: 功能范围与行为
**Impact**: High — 引入全新功能模块

| Option | Description |
|--------|-------------|
| **A ✅** | **LLM API 分析：调用大模型对第一章节内容进行分析，动态生成总结结构** |
| B | 基于 NLP 规则的关键词/句提取 |
| C | 预设 Prompt 模板 + LLM |

**User Choice**: **A — LLM API 分析**

**Rationale**: "动态调整结构"和"提取观点/主题"本质上是语义理解任务，纯规则方法很难做到高质量。

**Spec Impact**:
- 新增第二章节功能需求
- 需要 LLM 集成（具体方式见 Q3）
- 输出模型需要扩展

---

## Q3: LLM 接入方式

**Category**: 集成与外部依赖
**Impact**: High — 决定技术架构和依赖

**User Choice**: **自定义回答 — 通过 CodeBuddy 的自定义 command（`jsonvoice2md.md`）直接利用 IDE 内置的 LLM 能力**

**Key Points**:
- 不需要额外的 API key 配置
- 不需要网络依赖管理
- 直接复用 IDE 的 AI 能力
- 需要考虑 token 长度限制，具备**预警和切分**机制

**Spec Impact**:
- 移除"离线运行"假设（第二章节需要 IDE AI 能力）
- 工具分为两部分：
  - `tools/json2md.py`：纯 Python 脚本，负责第一章节（规则合并）
  - `.codebuddy/commands/jsonvoice2md.md`：AI command，负责调用脚本 + 第二章节分析
- 新增 token 长度预警和切分功能需求

---

## Q4: 长文本切分策略

**Category**: 约束与权衡
**Impact**: Medium — 影响长录音的处理质量

| Option | Description |
|--------|-------------|
| A | 按固定 token 数切分 |
| **B ✅** | **按语义段落自动切分：利用第一章节已合并的自然段落为单位进行分组** |
| C | 按时间区间切分 |

**User Choice**: **B — 按语义段落自动切分**

**Rationale**: 每个切片都是语义完整的，分段分析后再合并总结，最终输出质量最高。

**Spec Impact**:
- 新增长度检测和预警功能需求
- 新增分段分析 + 合并总结的工作流
- 工作流：JSON → 规则合并 → 长度检测 → (超限则切分) → 分段/整体分析 → 输出

---

## Q5: 第二章节"动态结构"的输出边界

**Category**: 领域与数据模型
**Impact**: Medium — 影响 prompt 设计和输出一致性

| Option | Description |
|--------|-------------|
| A | 完全自由 |
| **B ✅** | **必选项 + 可选项池：固定"主题"和"核心观点"为必选，其余由 AI 根据内容选取** |
| C | 多模板切换 |

**User Choice**: **B — 必选项 + 可选项池**

**Output Structure**:
```markdown
## 内容分析

### 主题 *(必选)*
[一句话概括核心主题]

### 核心观点 *(必选)*
1. [观点1]
2. [观点2]
...

### [动态章节] *(可选，由 AI 根据内容决定)*
可能包括：
- "论据与案例" — 当内容包含大量举例论证时
- "关键数据" — 当内容涉及数据引用时
- "争议与反思" — 当内容包含辩证讨论时
- "行动建议" — 当内容具有指导性质时
- "关键引用" — 当有值得摘录的金句时
```

**Spec Impact**:
- 第二章节输出模型需要定义必选/可选结构
- Prompt 设计需要包含可选项池列表

---

## Impact Summary

### Scope Changes (vs. Original Spec)

| Area | Before | After |
|---|---|---|
| **核心定位** | 字幕格式转换器 | 演讲稿生成器 + 内容分析器 |
| **输出结构** | 单一时间戳字幕 | 两章节：原文文章 + 智能总结 |
| **第一章节** | 逐段保留时间戳 | 规则合并为连贯段落 |
| **第二章节** | 不存在 | AI 驱动的内容分析（主题+观点+动态章节） |
| **AI 依赖** | 无 | CodeBuddy IDE 内置 LLM |
| **离线能力** | 完全离线 | 第一章节离线，第二章节需 IDE AI |
| **长文本处理** | 未考虑 | 语义段落切分 + 预警 |

### Files Requiring Update

- [x] `clarifications.md` — 本文件（新建）
- [ ] `spec.md` — 重写用户故事、需求、成功标准
- [ ] `research.md` — 新增段落合并算法、prompt 设计研究
- [ ] `data-model.md` — 新增两章节输出模型
- [ ] `contracts/cli-contract.md` — 更新输出格式
- [ ] `quickstart.md` — 更新使用说明
