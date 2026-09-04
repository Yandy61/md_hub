# Issue Tracker

Local markdown-based issue tracking for this project.

## Location

Issues are tracked as local markdown files under `.scratch/<feature-slug>/` in this repository.

## What is an issue

An issue is a bug report, an improvement proposal, or a discussion topic that survives longer than a single conversation. If a discussion produces an actionable follow-up that outlives the session, write it down as an issue.

## Lifecycle

1. New issues are created with label `needs-triage`.
2. Triage happens in conversation with the user; labels are updated as decisions are made.
3. `ready-for-agent` issues are ready for an agent to implement.
4. `ready-for-human` issues need a human decision or implementation.
5. `wontfix` issues are archived (kept in the file but closed with explanation).
6. Resolved issues can be deleted or kept as a record — user's choice, default keep.

## Creating issues

Create `.scratch/<feature-slug>/<issue-slug>.md`:

```markdown
# <issue-slug>

- **Labels**: needs-triage
- **Created**: <date>
- **Status**: open

## 描述

<具体问题描述>

## 备注

<补充信息、复现步骤、相关讨论链接等>
```

## 查找 issue

- 列出所有 issue：`ls .scratch/*/` 或搜索 `.scratch/` 下所有 `.md` 文件
- 查看单个：直接 Read 对应 markdown 文件
- 更新状态：编辑文件中的 Labels/Status 字段

## Labels

Labels come from `docs/agents/triage-labels.md`。五标签体系：

- `needs-triage` — 新建 issue 的默认标签，等待分诊
- `needs-info` — 缺少必要信息，等待补充
- `ready-for-agent` — 信息齐全，agent 可以直接实现
- `ready-for-human` — 需要人来决策或实现
- `wontfix` — 决定不修复，记录原因后关闭
