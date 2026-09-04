# Domain

## Layout

Single-context 布局：仓库根目录一个 `CONTEXT.md`，加上 `docs/adr/` 目录存放架构决策记录。

- `CONTEXT.md` — 项目领域概念与术语表（当项目有实际代码后逐步填充）
- `docs/adr/` — 架构决策记录，每个重要决策一个文件，格式见 `docs/adr/0000-template.md`

## ADR 格式

每个 ADR 文件命名 `NNNN-title.md`（四位序号 + 短标题）：

```markdown
# NNNN. <决策标题>

- **日期**: YYYY-MM-DD
- **状态**: proposed / accepted / superseded by NNNN
- **背景**: 为什么需要做这个决策
- **决策**: 决定了什么
- **后果**: 正面影响、负面影响、折中
```

## 维护规则

- 讨论中达成共识的领域术语 → 沉淀到 `CONTEXT.md`
- 重要技术选型、架构决策 → 写 ADR
- ADR 一旦 accepted 不再修改内容；被替代时改状态并写新 ADR
