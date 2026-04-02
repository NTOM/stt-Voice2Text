# Research: STT Command 拆分与 Skill 化重构

**Feature**: 004-stt-command-refactor
**Date**: 2026-04-01
**Status**: Complete

## R1: AI Command MD 文件的 Frontmatter 格式

**Decision**: 新命令使用 CodeBuddy/Cursor 标准 frontmatter 格式，不指定 `model` 字段。

**Rationale**: 
- 现有 `jsonvoice2md.md` 使用 `model: claude-3.5-sonnet`，但 clarify 阶段用户选择不指定 model
- 不指定 model 让 IDE 使用默认模型，用户可在 IDE 设置中自行选择
- 降低了对特定模型的耦合，提高了跨 IDE 兼容性

**Alternatives considered**:
- 统一指定 `claude-3.5-sonnet` → 拒绝：限制了用户选择
- 按任务复杂度区分模型 → 拒绝：增加维护复杂度

**Frontmatter 模板**:
```yaml
---
description: [命令描述]
arguments:
  - name: [参数名]
    description: [参数描述]
    required: true/false
---
```

## R2: stt.json2md 全自动串联模式的实现方式

**Decision**: 在 Command MD 的 prompt 中编排两阶段流程：① 运行脚本 → ② AI 阅读输出并追加重写稿。

**Rationale**:
- AI Command 本质是 prompt 驱动的工作流，AI 可以执行终端命令并读取文件
- 全自动串联无需用户中间操作，体验最流畅
- 现有 `jsonvoice2md.md` 已验证了"先运行脚本 → 再 AI 分析"的模式可行

**Alternatives considered**:
- 两个独立命令 → 拒绝：用户需要手动衔接，体验差
- Python 脚本内嵌 AI 调用 → 拒绝：AI Command 不应依赖外部 AI SDK

**实现要点**:
- Step 1: `python tools/json2md.py "{json-file-path}" -f` 生成第一章
- Step 2: AI 读取生成的 MD 文件，分析原文内容
- Step 3: AI 生成第二章（AI 重写稿），追加到文件末尾
- 幂等性：检查是否已存在 `## 第二章：AI 重写`，存在则替换

## R3: AI 重写的 Prompt 工程策略

**Decision**: 采用结构化 prompt，明确指定重写规则（子标题、标点、对话检测、风格保持）。

**Rationale**:
- 口语转录的核心问题：标点缺失（8465 字符仅 35 个标点）、无子标题、段落混乱
- AI 重写需要精确的指令来保持原意同时提升可读性
- 对话性内容检测需要明确的判断标准和输出格式

**Prompt 关键指令**:
1. **子标题分配**: 使用 `###` 三级标题，内容概括式命名，不带编号
2. **标点补充**: 补充句号、逗号、问号等，使语句通顺
3. **对话检测**: 识别互动性内容（弹幕互动、提问、号召），使用 `>` 引用块标注
4. **风格保持**: 保持演讲稿/口语的自然风格，不过度书面化
5. **信息完整性**: 保留原文 ≥ 95% 的核心信息点

**Alternatives considered**:
- 无结构化 prompt，让 AI 自由发挥 → 拒绝：输出不稳定
- 分步骤多次调用（先加标点 → 再分段 → 再加标题）→ 拒绝：Token 消耗过大

## R4: stt.extract 服务检测与自动启动策略

**Decision**: AI Command 通过终端命令检测服务状态，未运行时自动启动，失败时降级提示。

**Rationale**:
- stt 服务监听 `http://127.0.0.1:9977`，可通过 HTTP 请求检测
- `python start.py` 是标准启动命令，AI 可在终端执行
- 自动启动 + 降级提示兼顾了自动化和容错

**检测流程**:
```
1. curl/Invoke-WebRequest http://127.0.0.1:9977 → 200 OK → 服务已运行
2. 失败 → 执行 python start.py（后台）
3. 轮询检测（最多 60 秒，间隔 5 秒）
4. 超时 → 降级提示用户手动处理
```

**API 端点选择**:
- `/api` — 标准 stt API（POST，需要音频文件）
- `/v1/audio/transcriptions` — OpenAI 兼容端点
- 检测时使用根路径 `/` 或 `/api`（GET 请求即可判断服务是否存活）

**Alternatives considered**:
- 仅提示用户手动启动 → 拒绝：用户明确要求自动化
- Docker 容器化部署 → 拒绝：过度工程化，项目已有 `start.py`

## R5: setup-commands.ps1 脚本设计

**Decision**: PowerShell 脚本，支持 `-IDE` 参数，默认部署到 CodeBuddy。

**Rationale**:
- 用户使用 Windows，PowerShell 是原生选择
- 零外部依赖，仅使用 `Copy-Item`、`New-Item` 等内置 cmdlet
- `-IDE` 参数支持 `codebuddy`、`cursor` 或逗号分隔的多选

**脚本逻辑**:
```
1. 扫描 commands/*.md
2. 如果为空 → 提示并退出
3. 解析 -IDE 参数（默认 codebuddy）
4. 对每个 IDE：
   a. 创建 .{ide}/commands/ 目录（如不存在）
   b. 复制所有 .md 文件（覆盖模式）
5. 输出部署报告
```

**Alternatives considered**:
- Python 脚本 → 拒绝：增加依赖，PowerShell 更轻量
- Makefile → 拒绝：Windows 原生不支持 make
- 符号链接 → 拒绝：Windows 符号链接需要管理员权限

## R6: 命令拆分后的章节编号策略

**Decision**: 三章结构保持不变，但分属不同命令生成。

**Rationale**:
- 第一章（原文）：`stt.json2md` 中由 `json2md.py` 脚本生成
- 第二章（AI 重写）：`stt.json2md` 中由 AI 自动追加
- 第三章（内容分析/总结）：`stt.summarize` 中由 AI 生成
- 章节标题使用 `##` 二级标题，章内子标题使用 `###` 三级标题

**Markdown 结构**:
```markdown
# {文件名} — 演讲稿与内容分析

**Source**: ...
**Segments**: ...
**Duration**: ...

---

## 第一章：原文              ← json2md.py 生成
{段落合并后的原文}

---

## 第二章：AI 重写            ← stt.json2md AI 追加
### {子标题1}
{重写内容，含标点、分段优化}
> {对话性内容，引用块标注}

---

## 第三章：内容分析            ← stt.summarize AI 追加
### 主题
### 核心观点
### {可选章节...}
```

## R7: Constitution 合规性分析

| 原则 | 合规状态 | 说明 |
|------|---------|------|
| I. Upstream Isolation | ✅ 合规 | 所有新文件在 `commands/`、`scripts/` 目录，不修改上游文件 |
| II. Minimal Diff | ✅ 合规 | 纯新增文件（3 个 Command MD + 1 个 PS1 脚本），零上游文件修改 |
| III. Backward Compatibility | ✅ 合规 | 不修改 `/api`、`/v1` 端点，`python start.py` 行为不变 |
| IV. Code Quality | ✅ 合规 | Command MD 使用中文注释，脚本使用英文变量名 |
| V. Test Before Merge | ✅ 合规 | 每个命令有独立的 smoke test 场景 |
