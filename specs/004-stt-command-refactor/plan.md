# Implementation Plan: STT Command 拆分与 Skill 化重构

**Branch**: `004-stt-command-refactor` | **Date**: 2026-04-01 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-stt-command-refactor/spec.md`

## Summary

将现有的单一 `jsonvoice2md` AI Command 拆分为三个职责单一的命令（`stt.extract`、`stt.json2md`、`stt.summarize`），新增 AI 演讲稿重写功能（含子标题分配、标点补充、对话性内容检测），并通过 `commands/` 源目录 + `setup-commands.ps1` 一键配置脚本实现 Skill 化跨 IDE 部署。

## Technical Context

**Language/Version**: Python 3.9+ (upstream stt service), PowerShell 5.1+ (scripts), Markdown (AI Commands)
**Primary Dependencies**: Flask (existing stt service), json2md.py (existing tool), IDE AI Agent (CodeBuddy/Cursor)
**Storage**: 文件系统 — JSON 转录文件 → Markdown 演讲稿，Command 源文件
**Testing**: 手动 smoke test（Constitution Principle V）
**Target Platform**: Windows (PowerShell 主力)
**Project Type**: CLI tool + AI Command (Markdown-driven prompt engineering)
**Performance Goals**: json2md.py 脚本 < 5s，AI 重写/总结取决于 LLM 响应速度
**Constraints**: 零上游文件修改（Constitution Principle I & II），UTF-8 编码
**Scale/Scope**: 3 个 AI Command MD + 1 个 PowerShell 脚本 + .gitignore 更新

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Check ✅

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Upstream Isolation | ✅ PASS | 所有新文件在 `commands/`、`scripts/` 目录，不修改上游文件。`main` 分支不受影响。 |
| II. Minimal Diff | ✅ PASS | 纯新增文件（3 个 Command MD + 1 个 PS1 脚本），零上游文件编辑。 |
| III. Backward Compatibility | ✅ PASS | `/api`、`/v1` 端点不变，`python start.py` 行为不变，现有 `jsonvoice2md.md` 保留。 |
| IV. Code Quality | ✅ PASS | Command MD 使用中文注释，PS1 脚本使用英文变量名，UTF-8 编码。 |
| V. Test Before Merge | ✅ PASS | 每个命令有独立的 smoke test 场景（见 spec Acceptance Scenarios）。 |

### Post-Phase 1 Re-check ✅

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Upstream Isolation | ✅ PASS | data-model.md 确认无上游实体修改，仅新增 CommandSource 和 IDETarget 实体。 |
| II. Minimal Diff | ✅ PASS | contracts 确认所有接口为新增，不修改现有 `/api` 或 `/v1` 端点。 |
| III. Backward Compatibility | ✅ PASS | 现有 `jsonvoice2md.md` 保留不删除，用户可继续使用旧命令。 |
| IV. Code Quality | ✅ PASS | 所有新文件遵循 UTF-8 编码，PS1 脚本使用英文变量名。 |
| V. Test Before Merge | ✅ PASS | quickstart.md 包含验证步骤，每个命令可独立 smoke test。 |

## Project Structure

### Documentation (this feature)

```text
specs/004-stt-command-refactor/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── command-contracts.md  # Phase 1 output
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
stt-Voice2Text/
├── commands/                        # 📦 新增：Command 源文件（Git 追踪）
│   ├── stt.extract.md              # 新增：音频提取命令
│   ├── stt.json2md.md              # 新增：JSON→MD + AI 重写命令
│   └── stt.summarize.md            # 新增：AI 总结命令
├── scripts/
│   └── setup-commands.ps1          # 新增：一键配置脚本
├── tools/
│   └── json2md.py                  # 已有：JSON→MD 转换脚本（不修改）
├── .codebuddy/commands/            # 脚本部署目标（.gitignore 忽略）
│   └── jsonvoice2md.md             # 已有：保留不删除
├── .cursor/commands/               # 脚本部署目标（.gitignore 忽略）
├── Export/                          # 输出目录
├── .gitignore                      # 更新：确保 commands/ 被追踪
└── start.py                        # 已有：stt 服务入口（不修改）
```

**Structure Decision**: 采用 `commands/` 独立源目录 + `scripts/setup-commands.ps1` 部署脚本的方案（参考 ADR-001、ADR-002 in 001-skill化.md）。不修改任何上游文件，所有新增内容为独立文件。

## Complexity Tracking

> 无 Constitution 违规，无需记录。
