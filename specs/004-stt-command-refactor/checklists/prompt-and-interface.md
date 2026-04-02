# Prompt Engineering & Command Interface Checklist: STT Command 拆分与 Skill 化重构

**Purpose**: 编码前作者自查 — 验证 AI 重写 prompt 指令和命令接口需求的完整性与清晰度
**Created**: 2026-04-01
**Feature**: [spec.md](../spec.md) | [command-contracts.md](../contracts/command-contracts.md)

## A. Prompt Engineering 需求质量

- [x] CHK-P01 AI 重写的 5 项核心指令（子标题分配、标点补充、重新分段、对话检测、风格保持）在 spec FR-004~FR-008 中均有独立需求条目
- [x] CHK-P02 子标题分配规则已明确：`###` 三级标题 + 内容概括式命名 + 不带编号（FR-004, Clarification Q4）
- [x] CHK-P03 对话性内容的判断标准已定义（互动性内容：弹幕互动、提问、号召），输出格式为 `>` 引用块（FR-004, Clarification Q2）
- [x] CHK-P04 "保持口语自然风格，不过度书面化"（FR-008）有足够的约束力，不会与"补充标点使语句通顺"（FR-007）产生冲突
- [x] CHK-P05 信息完整性约束（SC-006: 保留 ≥ 95% 核心信息点）的验证方式已明确（人工评审 vs 自动化）
- [x] CHK-P06 渐进式加载策略（FR-009）对 AI 重写的触发条件已定义（原文 > 20000 tokens，见 Edge Cases）
- [x] CHK-P07 stt.summarize 的必选章节（主题、核心观点）和可选章节列表在 contract 中已明确枚举

## B. 命令接口需求质量

- [x] CHK-I01 三个命令的输入参数类型、必选性、描述在 contract 中均已定义，无歧义
- [x] CHK-I02 stt.json2md 的全自动串联流程（脚本 → AI 读取 → AI 追加）的每个步骤的失败条件和 ABORT 行为已定义（contract Error Codes）
- [x] CHK-I03 stt.summarize 的前置条件检查（必须包含第一章和第二章标题）在 contract 和 Edge Cases 中均有覆盖
- [x] CHK-I04 stt.extract 的服务检测 → 自动启动 → 轮询 → 超时降级的完整链路在 contract 中有时序图和超时参数（60s）
- [x] CHK-I05 三个命令的幂等性策略（覆盖/替换）在 contract Idempotency 章节中均已明确
- [x] CHK-I06 输出文件路径规则（`Export/{stem}.md`、`Export/{stem}.json`）在 contract 中已定义，与 FR-014 一致
- [x] CHK-I07 json2md.py 的 `-f` 覆盖标志在 contract 执行流程中已体现，与 FR-020 幂等性要求一致
- [x] CHK-I08 三个命令的串联工作流顺序（extract → json2md → summarize）在 SC-005 中已定义，且每个命令可独立执行

## Notes

- 本 checklist 聚焦 **需求层面** 的完整性，不涉及实现细节
- CHK-P04 需要特别关注：如果 prompt 中"自然风格"和"补充标点"的指令权重不明确，AI 可能产生不一致的输出
- CHK-P05 的验证方式建议在 tasks.md 阶段明确（当前 spec 中标注为"人工评审"）
- 已有的 [requirements.md](./requirements.md) 覆盖了 spec 整体质量，本 checklist 是对 prompt 和接口维度的深入补充
