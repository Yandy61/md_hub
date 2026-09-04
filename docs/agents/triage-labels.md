# Triage Labels

Default five canonical labels for this project's issue tracking.

| Label | 含义 | 使用场景 |
|---|---|---|
| `needs-triage` | 待分诊 | 新建 issue 文件的默认状态，尚未评估 |
| `needs-info` | 缺信息 | 描述不完整，无法行动，等待补充细节 |
| `ready-for-agent` | 可交 agent | 信息齐全，agent 可直接开工实现 |
| `ready-for-human` | 需人类 | 需要人来决策、评审或实现 |
| `wontfix` | 不修复 | 决定不做，记录原因后关闭 |

## 生命周期

```
新建 → needs-triage → (评估) → ready-for-agent → 完成
                          ├→ needs-info → (补充后重新评估)
                          └→ ready-for-human → 完成 / wontfix
```

## 规则

- 新建 issue 默认打 `needs-triage`
- 只有用户能确认"信息已足够"后才改为 `ready-for-agent`
- agent 实现中遇到信息缺口，改回 `needs-info` 并在文件中写明缺什么
- `wontfix` 必须写明原因
