# Feature Specification: STT Command 拆分与 Skill 化重构

**Feature Branch**: `004-stt-command-refactor`
**Created**: 2026-03-31
**Status**: Draft
**Input**: User description: "Skill化命令拆分与重构：将 jsonvoice2md 拆分为 stt.summarize、stt.extract、stt.json2md 三个命令，增加 AI 演讲稿重写功能，配合一键配置脚本实现跨 IDE 部署"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - JSON 转 Markdown 并 AI 重写（stt.json2md）(Priority: P1)

用户已有 stt 导出的 JSON 转录文件，希望通过 AI Command 一键完成：① 调用脚本将 JSON 转换为 Markdown 原文（第一章）；② AI 阅读原文内容，进行子标题分配、重新分段、添加标点符号，并检测对话性内容进行区分标注，生成 AI 重写稿（第二章）。这是整个工作流的核心步骤。

**Why this priority**: 这是最核心的自动化步骤，既包含脚本生成（确定性），又包含 AI 重写（智能化）。AI 重写解决了口语转录中标点缺失、无子标题、段落混乱、对话与叙述混杂的痛点。

**Independent Test**: 在 IDE 中输入 `/stt.json2md` 并提供 JSON 文件路径，验证生成的 MD 文件包含第一章原文和第二章 AI 重写稿。

**Acceptance Scenarios**:

1. **Given** 用户有一个 stt 导出的 JSON 文件（如 `Export/audio.json`），**When** 用户在 CodeBuddy/Cursor 中执行 `/stt.json2md Export/audio.json`，**Then** 系统先运行 `python tools/json2md.py` 生成第一章原文，然后 AI 阅读原文并生成第二章 AI 重写稿（含子标题、标点、分段优化）。
2. **Given** JSON 文件路径不存在或格式无效，**When** 用户执行 `/stt.json2md bad-path.json`，**Then** 系统输出明确的错误信息并停止，不生成任何文件。
3. **Given** 输出 MD 文件已存在，**When** 用户再次执行同一命令，**Then** 系统覆盖已有文件（幂等性），输出内容一致。
4. **Given** 第一章原文中存在对话性内容（如「弹幕里扣个1让我看看」「你们有没有遇到过...的经历」），**When** AI 生成第二章重写稿，**Then** AI 检测出这些对话性内容并使用 Markdown 引用块（`>`）格式标注，与叙述性正文明确区分。

---

### User Story 2 - AI 内容总结（stt.summarize）(Priority: P1)

用户已有通过 stt.json2md 生成的 Markdown 文件（包含第一章原文和第二章 AI 重写稿），希望 AI 对内容进行深度分析，生成结构化的内容分析报告（第三章），仅保留总结功能。

**Why this priority**: 这是用户获取核心价值的步骤——从原始转录文本中提取结构化知识（主题、核心观点、案例、数据等）。

**Independent Test**: 对已有的 MD 文件执行 `/stt.summarize`，验证生成的第三章包含主题、核心观点等必选章节。

**Acceptance Scenarios**:

1. **Given** 用户有一个包含第一章原文和第二章 AI 重写稿的 MD 文件，**When** 用户执行 `/stt.summarize Export/audio.md`，**Then** AI 分析内容，在文件末尾追加第三章（内容分析）。
2. **Given** MD 文件内容较长（> 6000 tokens），**When** 用户执行 `/stt.summarize`，**Then** 系统采用渐进式加载策略，分段分析后合并结果。
3. **Given** MD 文件已包含第三章，**When** 用户再次执行 `/stt.summarize`，**Then** 系统替换已有的第三章（幂等性），不产生重复内容。

---

### User Story 3 - 音频提取为 JSON（stt.extract）(Priority: P2)

用户有一个 wav 音频文件，希望通过 AI Command 引导完成从音频到 JSON 转录文件的全流程，包括自动检测本地 stt 服务是否已部署、未部署时辅助部署、调用 API 提取转录结果。

**Why this priority**: 这是整个工作流的起点，但依赖本地服务部署，复杂度较高。作为 P2 是因为用户也可以手动通过 Web UI 完成此步骤。

**Independent Test**: 在 IDE 中执行 `/stt.extract static/tmp/audio.wav`，验证系统能检测服务状态并引导完成 JSON 提取。

**Acceptance Scenarios**:

1. **Given** 本地 stt 服务已在 `http://127.0.0.1:9977` 运行，**When** 用户执行 `/stt.extract static/tmp/audio.wav`，**Then** 系统调用 API 提交音频文件，等待识别完成，将 JSON 结果保存到 `Export/` 目录。
2. **Given** 本地 stt 服务未运行，**When** 用户执行 `/stt.extract`，**Then** 系统检测到服务未启动，自动在终端执行 `python start.py` 启动服务，轮询等待服务就绪后继续提取流程。
3. **Given** 自动启动服务失败（如缺少依赖、端口占用），**When** 系统检测到启动异常，**Then** 系统降级为提示用户手动处理，输出具体的错误信息和修复步骤（如 `pip install -r requirements.txt`）。
4. **Given** 音频文件格式为非 wav（如 mp3、mp4），**When** 用户提供该文件，**Then** 系统提示需要先通过 Web UI 上传（Web UI 内置 FFmpeg 转换），或引导用户手动转换。

---

### User Story 4 - Skill 一键配置（setup-commands）(Priority: P2)

用户 clone 项目后，希望一条命令即可将所有自定义 AI Command 部署到 CodeBuddy 和/或 Cursor IDE 中，无需手动复制文件。

**Why this priority**: 这是 Skill 化的基础设施，解决跨设备、跨 IDE 共享 Command 的痛点。但不影响单机使用。

**Independent Test**: clone 项目后运行 `.\scripts\setup-commands.ps1`，验证 `.codebuddy/commands/` 和 `.cursor/commands/` 下出现所有 Command 文件。

**Acceptance Scenarios**:

1. **Given** 用户刚 clone 项目，`.codebuddy/commands/` 目录不存在，**When** 用户运行 `.\scripts\setup-commands.ps1`，**Then** 脚本创建目录并复制 `commands/` 下所有 `.md` 文件到 `.codebuddy/commands/`。
2. **Given** 用户指定 `-IDE cursor`，**When** 运行脚本，**Then** 仅部署到 `.cursor/commands/`。
3. **Given** 用户指定 `-IDE codebuddy,cursor`，**When** 运行脚本，**Then** 同时部署到两个 IDE 目录。
4. **Given** 用户重复运行脚本，**When** 目标目录已有文件，**Then** 以源文件覆盖（幂等性），不报错。
5. **Given** `commands/` 目录为空，**When** 运行脚本，**Then** 输出提示信息并退出（exit code 0），不视为错误。

---

### Edge Cases

- 用户在 `/stt.summarize` 时提供的文件不包含 `## 第一章：原文` 或 `## 第二章：AI 重写` 标题 → 报错并提示先运行 `/stt.json2md`
- `/stt.extract` 时 stt 服务端口被其他程序占用 → 提示端口冲突
- `/stt.json2md` 输入的 JSON 文件编码不是 UTF-8 → 报错并提示编码问题
- `setup-commands.ps1` 在 Linux/macOS 上运行 → 提示使用 `setup-commands.sh`（如果存在）
- AI 重写时原文过长（> 20000 tokens）→ 分段重写后合并
- AI 重写时无法识别对话性内容（如纯技术讲座无互动）→ 跳过对话检测，全部作为叙述性内容处理
- 用户在 `/stt.extract` 时提供的 wav 文件超过 500MB → 提示文件过大，建议分段处理

## Requirements *(mandatory)*

### Functional Requirements

**命令拆分与重构**：

- **FR-001**: 系统 MUST 提供 `stt.json2md` 命令，采用全自动串联模式：先调用 `python tools/json2md.py` 生成第一章原文，然后 AI 自动阅读生成的 MD 文件并追加第二章 AI 重写稿，用户无需中间操作
- **FR-002**: 系统 MUST 提供 `stt.summarize` 命令，对已有 MD 文件进行 AI 内容分析，生成第三章总结报告（主题、核心观点、可选章节）
- **FR-003**: 系统 MUST 提供 `stt.extract` 命令，引导用户从 wav 音频文件提取 JSON 转录结果
- **FR-004**: `stt.json2md` 的 AI 重写 MUST 包含：子标题分配（使用 `###` 三级标题，内容概括式命名，不带编号）、重新分段、添加标点符号、对话性内容检测与引用块标注
- **FR-005**: `stt.summarize` MUST 保留原 `jsonvoice2md` 的内容分析功能（主题、核心观点、可选章节），仅负责总结，不负责重写

**AI 重写功能**：

- **FR-006**: AI 重写 MUST 保留原文的核心语义和信息完整性，不得添加原文中不存在的观点
- **FR-007**: AI 重写 MUST 补充合理的标点符号（句号、逗号、问号等），使语句通顺
- **FR-008**: AI 重写 MUST 保持演讲稿/口语的自然风格，不过度书面化
- **FR-009**: AI 重写 MUST 采用渐进式加载策略，与内容分析共享 Token 预算机制
- **FR-010**: AI 重写的输出格式 MUST 为 Markdown，使用 `## 第二章：AI 重写` 作为标题，内容分析使用 `## 第三章：内容分析` 作为标题

**stt.extract 服务检测**：

- **FR-011**: `stt.extract` MUST 在执行前检测 `http://127.0.0.1:9977` 是否可达
- **FR-012**: 如果服务未运行，`stt.extract` MUST 自动在终端执行 `python start.py` 启动服务，轮询等待就绪后继续；启动失败时降级为提示用户手动处理
- **FR-013**: `stt.extract` MUST 通过 API（`/api` 或 `/v1/audio/transcriptions`）提交音频并获取 JSON 结果
- **FR-014**: `stt.extract` MUST 将 JSON 结果保存到 `Export/` 目录，文件名与音频文件同名

**Skill 化部署**：

- **FR-015**: 系统 MUST 提供 `commands/` 源目录，存放所有自定义 Command 的 `.md` 文件
- **FR-015a**: Command MD 文件的 frontmatter 中 MUST NOT 指定 `model` 字段，由 IDE 使用默认模型，用户可在 IDE 设置中自行选择
- **FR-016**: 系统 MUST 提供 `scripts/setup-commands.ps1` 一键配置脚本
- **FR-017**: 配置脚本 MUST 支持 `-IDE` 参数指定目标 IDE（codebuddy / cursor）
- **FR-018**: 配置脚本 MUST 默认部署到 CodeBuddy（`.codebuddy/commands/`）
- **FR-019**: `.gitignore` MUST 忽略 `.codebuddy/` 和 `.cursor/` 目录，`commands/` 目录 MUST 纳入版本管理

**幂等性与错误处理**：

- **FR-020**: 所有命令 MUST 支持幂等执行——重复运行产生一致结果
- **FR-021**: 所有命令 MUST 在遇到错误时立即停止并输出明确的错误信息

### Key Entities

- **Command 源文件**：存放在 `commands/` 目录下的 `.md` 文件，是 AI Command 的唯一权威来源
- **stt 服务**：基于 Flask 的本地 Web 服务（`start.py`），提供语音识别 API，监听 `127.0.0.1:9977`
- **JSON 转录文件**：stt 服务导出的 JSON 格式音频转录结果，包含 line、start_time、end_time、text 字段
- **Markdown 演讲稿**：最终输出文件，包含三章：第一章原文（脚本生成）、第二章 AI 重写（stt.json2md 中 AI 生成）、第三章内容分析（stt.summarize 中 AI 生成）

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 用户执行 `/stt.json2md` 后，`json2md.py` 脚本阶段在 5 秒内完成并生成包含第一章原文的 MD 文件，文本完整性 ≥ 99%（AI 重写阶段耗时取决于 LLM 响应速度，不计入此指标）
- **SC-002**: 用户执行 `/stt.json2md` 后，AI 生成的第二章重写稿包含合理的标点符号（句号、逗号、问号等，标点数量显著多于原文），且包含 AI 分配的 `###` 三级子标题
- **SC-002a**: 用户执行 `/stt.summarize` 后，AI 生成的第三章包含「主题」和「核心观点」必选章节
- **SC-003**: 用户执行 `/stt.extract` 后，在服务已运行的情况下，能在 3 分钟内完成音频识别并保存 JSON 文件
- **SC-004**: 用户 clone 项目后运行 `setup-commands.ps1`，所有 Command 文件在 5 秒内部署到目标 IDE 目录
- **SC-005**: 三个命令（stt.extract → stt.json2md → stt.summarize）的串联工作流可在单次会话中顺序完成
- **SC-006**: AI 重写后的演讲稿保留原文 ≥ 95% 的核心信息点，同时可读性显著提升（通过人工抽样评审验证：随机选取 3 个段落，对比原文与重写稿的信息覆盖度）

## Assumptions

- 用户已安装 Python 3.9+ 环境
- 用户使用 Windows 操作系统（PowerShell 脚本为主，Bash 脚本为可选）
- stt 服务的 API 接口（`/api`、`/v1/audio/transcriptions`）保持现有格式不变
- CodeBuddy 和 Cursor 的命令目录格式兼容（均为 `.{ide}/commands/*.md`，frontmatter + Markdown）
- 音频文件已转换为 wav 格式（stt 服务内部通过 FFmpeg 处理其他格式）
- 现有的 `json2md.py` 脚本功能保持不变，新命令通过调用该脚本实现
- AI 重写功能依赖 IDE 内置的 LLM 能力（CodeBuddy / Cursor 的 AI 模型）

## Clarifications

### Session 2026-03-31

- Q: AI 重写功能应归属哪个命令？ → A: 归属 `stt.json2md`，作为脚本生成原文后的 AI 后处理步骤。AI 需要阅读内容，进行子标题分配、重新分段、添加标点符号，并能检测对话性内容进行区分标注。`stt.summarize` 仅保留总结功能。
- Q: 对话性内容检测后使用什么格式标注？ → A: 使用 Markdown 引用块（`>`）格式标注对话性内容，与叙述性正文明确区分。
- Q: stt.json2md 的脚本生成与 AI 重写如何衔接？ → A: 全自动串联模式。用户执行一次 `/stt.json2md` 后，AI 自动先运行脚本生成第一章，然后立即阅读生成的 MD 文件并追加第二章重写稿，无需用户中间操作。
- Q: AI 重写中子标题分配的层级和命名风格？ → A: 使用 `###` 三级标题（`##` 已用于章节标题），采用内容概括式命名（如 `### Harness Engineering 的定义`、`### 三层演进链条`），不带编号。
- Q: stt.extract 服务未运行时的自动化程度？ → A: 自动启动模式。AI 检测到服务未运行时，自动在终端执行 `python start.py` 启动服务，轮询等待服务就绪后继续提取流程。如果启动失败（如缺少依赖），再降级为提示用户手动处理。
- Q: Command MD 文件的 frontmatter 中 model 字段如何设置？ → A: 不指定 `model` 字段，让 IDE 使用默认模型，用户可在 IDE 设置中自行选择。
