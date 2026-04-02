# Requirements Quality Review Checklist: JSON Voice Transcription to Markdown

**Purpose**: 全面需求质量审查 — 评审者视角检查需求规格的完整性、清晰度、一致性与可实现性
**Created**: 2026-03-31
**Feature**: [spec.md](./spec.md) | [plan.md](./plan.md) | [clarifications.md](./clarifications.md)
**Scope**: PR 评审级别 — 确保需求足够清晰，让评审者和实现者都能准确理解

## 一、需求完整性（Completeness）

- [ ] CHK001 **用户故事覆盖度** — 三个用户故事（P1×2 + P2×1）是否覆盖了所有核心使用场景？是否遗漏了"仅生成 Chapter 2"（对已有 Chapter 1 的文件追加分析）的场景？
- [ ] CHK002 **边缘情况定义** — spec.md 列出了 7 个边缘情况，但仅以问题形式呈现，未定义具体处理行为。评审者能否从 cli-contract.md 的错误消息表中找到每个边缘情况的对应处理？
- [ ] CHK003 **空文件/空数组处理** — JSON 文件为空（0字节）或包含空数组 `[]` 时的行为是否明确定义？cli-contract.md 中 "Not stt export" 错误是否覆盖此情况？
- [x] CHK004 **非 UTF-8 字符处理** — spec.md 边缘情况提到了 "non-UTF-8 characters"，但所有文档中均未定义具体处理策略（跳过？替换？报错？）
  > ✅ 已修复：spec.md 新增 FR-017（强制 UTF-8，非法编码报错退出码 2）；cli-contract.md 新增 Encoding error 错误消息行
- [ ] CHK005 **超大文件处理** — spec.md 提到 "extremely large JSON files (hours-long recordings)"，但仅 SC-001 定义了 "1小时内5秒" 的性能目标，未定义超过此范围的行为或限制

## 二、需求清晰度（Clarity）

- [x] CHK006 **段落合并算法的精确性** — 合并条件 "gap < 2s AND 无句末标点 AND 长度 < 500字" 在 research.md 和 data-model.md 中一致，但 spec.md FR-004 仅提到前两个条件，未提及 500 字上限。三处定义是否需要统一？
  > ✅ 已修复：spec.md FR-004 已补充 500 字安全上限条件，三处定义现已一致
- [ ] CHK007 **Token 估算公式** — research.md R5 定义 "1中文字 ≈ 1.5 tokens"，阈值为 6000 tokens（约 4000 字）。此估算是否足够准确？是否需要说明这是保守估计？
- [ ] CHK008 **"句末标点"的完整定义** — FR-004 和 research.md 定义句末标点为 `。！？.!?`，但中文语境中 `……`（省略号）、`——`（破折号）、`；`（分号）是否也应视为断句标志？
- [ ] CHK009 **文件命名规则** — cli-contract.md 示例显示 `audio.json → audio.md`，但未明确定义命名转换规则。如果 JSON 文件名包含特殊字符（空格、中文、括号）如何处理？
- [ ] CHK010 **数字后缀冲突解决** — FR-010 定义 "appending a numeric suffix (e.g., `output_1.md`)"，但未说明起始数字、最大重试次数、以及原文件名已包含 `_1` 时的行为

## 三、需求一致性（Consistency）

- [ ] CHK011 **Chapter 标题格式** — quickstart.md 示例使用 "第一章：原文"，data-model.md 使用 "Chapter 1 (原文)"，cli-contract.md 使用 "第一章：原文"。最终输出的 H2 标题格式是否统一确认？
- [ ] CHK012 **元数据格式一致性** — quickstart.md 示例显示 `**Segments**: 695 (merged into ~80 paragraphs)`，但 data-model.md 的 MarkdownArticleDocument 定义中 metadata 字段为 "segment count, paragraph count, duration"。"merged into ~80 paragraphs" 中的 `~` 近似值是否合适？
- [ ] CHK013 **FR 编号连续性** — spec.md 的 FR 编号从 FR-001 到 FR-016，但 FR-006 的描述（"preserve original text content exactly"）与 clarifications.md Q1 的决定（规则合并改变段落结构）是否存在语义冲突？需确认 "exactly" 的范围
- [ ] CHK014 **退出码与错误处理** — cli-contract.md 定义了退出码 0/1/2，但 spec.md 的功能需求中未提及退出码。评审者是否能仅从 spec.md 理解错误处理策略？
- [x] CHK015 **批处理范围** — spec.md FR-008 说 "converting all JSON files within it"，但未说明是否递归搜索子目录。cli-contract.md 也未明确。默认行为是仅当前目录还是递归？
  > ✅ 已修复：spec.md FR-008 已明确为 non-recursive（仅处理指定目录下的直接 JSON 文件，不遍历子目录）

## 四、可验证性（Testability）

- [ ] CHK016 **SC-002 的可测量性** — "reads as a natural, flowing article" 是主观标准，评审者如何验证？是否需要补充客观指标（如：段落数在 segments/5 ~ segments/10 范围内）？
- [ ] CHK017 **SC-004 的验证方法** — "at least one dynamically chosen section" 如何在自动化测试中验证？是否需要定义 Chapter 2 的最小结构（H3 数量 ≥ 3）？
- [ ] CHK018 **SC-005 的端到端验证** — 长内容切分+合并的成功标准是 "without user intervention"，但如何验证合并后的 Chapter 2 质量？是否需要定义合并后不应出现的问题（如重复观点）？
- [ ] CHK019 **段落合并质量基准** — 695 segments → "~50-120 paragraphs" 的范围是否过宽？评审者如何判断 50 段和 120 段的输出都是"正确"的？
- [ ] CHK020 **批处理进度指示** — SC-006 要求 "clear progress indication"，但 spec.md 和 cli-contract.md 均未定义进度输出的格式（百分比？文件名？进度条？）

## 五、接口契约完备性（Interface Contracts）

- [ ] CHK021 **CodeBuddy command 的参数验证** — cli-contract.md 定义了 `/jsonvoice2md <json-file-path>`，但未说明：(a) 是否支持目录路径（批处理）？(b) 路径不存在时的行为？(c) 是否支持相对路径？
- [x] CHK022 **Chapter 2 追加机制** — cli-contract.md 工作流显示 "追加到 Markdown 文件"，但未定义：如果文件已包含 Chapter 2（重复执行），是替换还是追加第二个 Chapter 2？
  > ✅ 已修复：spec.md 新增 FR-018（检测已有 Chapter 2 并替换）；cli-contract.md 新增 Re-execution Behavior 章节
- [x] CHK023 **长内容预警的交互方式** — research.md R5 定义了预警消息格式，但在 CodeBuddy command 上下文中，"预警"是以什么形式呈现？用户如何"确认"继续？IDE command 是否支持交互式确认？
  > ✅ 已修复：spec.md FR-014/SC-005 + research.md R5 已明确为非阻塞信息性提示，自动继续处理（无需用户确认）
- [ ] CHK024 **分段分析的 prompt 上下文** — research.md R5 提到 "这是第 X/M 段内容"，但未定义是否需要在每段 prompt 中包含前一段的摘要以保持上下文连贯性
- [ ] CHK025 **CLI 输出日志级别** — CODEBUDDY.md 提到使用 `logging` 模块，但 cli-contract.md 未定义默认日志级别（INFO？WARNING？）和是否支持 `--verbose` / `--quiet` 选项

## 六、非功能性需求（Non-Functional）

- [ ] CHK026 **跨平台兼容性** — plan.md 标注 "Windows (primary), cross-platform compatible"，但未定义具体的跨平台测试范围。路径分隔符（`\` vs `/`）、文件编码（BOM）等是否需要在需求中明确？
- [ ] CHK027 **Python 版本兼容性** — plan.md 定义 "Python 3.9–3.11"，但 stt 上游项目的 Python 版本要求是否已确认一致？是否需要在脚本中添加版本检查？
- [ ] CHK028 **内存使用约束** — 对于超大 JSON 文件（如数小时录音），是否需要流式解析而非一次性加载？当前需求未定义内存限制
- [ ] CHK029 **错误消息的国际化** — cli-contract.md 的错误消息使用英文，但工具面向中文用户。是否需要统一为中文错误消息？或双语？
- [ ] CHK030 **幂等性** — 对同一 JSON 文件多次运行 CLI（不带 `-f`），行为是否幂等？当前定义是跳过已存在文件，但如果源 JSON 已更新，用户如何知道需要重新生成？

## 七、文档与可维护性（Documentation & Maintainability）

- [ ] CHK031 **Prompt 版本管理** — Chapter 2 的 AI prompt 定义在 research.md R6 中，但实际实现在 `.codebuddy/commands/jsonvoice2md.md` 中。prompt 的修改是否需要同步更新 research.md？如何追踪 prompt 版本？
- [ ] CHK032 **合并算法参数可配置性** — 2秒阈值和500字上限是硬编码常量。需求是否应预留配置接口（如命令行参数或配置文件），以便未来调优？
- [ ] CHK033 **依赖隔离验证** — plan.md Constitution Check 声明 "zero modifications to upstream files"，评审者如何验证？是否需要在 checklist 中列出所有新增文件的完整清单？

## Notes

- 勾选已确认的项目：`[x]`
- 对于发现的问题，在对应项目下方添加 `> 发现：...` 注释
- 标记为 ⚠️ 的项目表示需要 spec 修订
- 标记为 ℹ️ 的项目表示已确认无需修改（附理由）
- 本检查清单基于 spec.md、plan.md、clarifications.md、research.md、data-model.md、cli-contract.md、quickstart.md 七份文档交叉审查生成
