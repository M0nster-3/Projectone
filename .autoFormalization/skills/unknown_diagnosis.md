# UNKNOWN 诊断与重试 Skill

## 用途

当 `sdk_spawner.py` 返回 `result=UNKNOWN` 时，Master Agent 调用本 Skill 诊断原因并决定是否重试。

## 背景

`sdk_spawner.py` 在 `parse_signal()` 未匹配到 `TASK_COMPLETED` 或 `TASK_FAILED` 时输出 `UNKNOWN`，
并将对应条目的 `proof_status` 回退、`dependency_status` 设为 `"blocked"`。

## 诊断流程

### 第一阶段：编译验证

从 spawner 输出行（格式 `[SDK_SPAWNER] 开始形式化<stage> | 任务: <task_id>  →  <lean_path>`）或日志文件 `.autoFormalization/logs/session_<ts>.json` 的 `lean_path` 字段获取目标 `.lean` 文件路径，运行：

```
lake build <目标模块>
```

- **编译通过**：子 Agent 完成了工作但未输出 `TASK_COMPLETED` 信号。执行修复：
  1. 将 `proof_status` 更新为对应阶段完成状态（statement 阶段 → `"statement_done"`，proof 阶段 → `"done"`）
  2. 将 `dependency_status` 从 `"blocked"` 改为 `"ready"`
  3. 若为 statement 阶段，更新 `api_index.json` 中对应条目并更新下游依赖
  4. 记录 `[MasterAgent] UNKNOWN 恢复: <task_id> 编译通过，状态已修正`
  5. `stop_flag = false`，返回调度循环步骤 1

- **编译失败**：进入第二阶段原因诊断。

### 第二阶段：错误原因分类与重试决策

读取对应日志文件 `.autoFormalization/logs/session_<timestamp>.json`，检查 `sdk_error` 和 `output` 字段：

| 错误模式 | 判决 | 操作 |
|---|---|---|
| `sdk_error` 含 `AnthropicError`、`APIError`、`APIConnectionError`、`RateLimitError`、`Timeout`、`ConnectionError` 等 SDK/网络异常 | **可重试** | `dependency_status` 从 `"blocked"` 改回 `"ready"`，记录 `[MasterAgent] UNKNOWN 重试: <task_id> — SDK/网络异常: <error>` |
| `output` 含 `max_turns` 或 `task_budget` 耗尽提示（非编译错误） | **可重试** | `dependency_status` 从 `"blocked"` 改回 `"ready"`，记录 `[MasterAgent] UNKNOWN 重试: <task_id> — max_turns 耗尽，重新尝试` |
| `output` 含 Lean 编译错误（类型不匹配、未知标识符、语法错误等） | **不可重试** | 保持 `"blocked"`，记录 `[MasterAgent] UNKNOWN 阻塞: <task_id> — 编译错误，需人工介入。日志: logs/session_<ts>.json` |
| `output` 或 `sdk_error` 提示找不到 unit 文件 | **不可重试** | 保持 `"blocked"`，记录 `[MasterAgent] UNKNOWN 阻塞: <task_id> — unit 文件异常` |
| 其他未分类错误 | **保守阻塞** | 保持 `"blocked"`，记录 `[MasterAgent] UNKNOWN 阻塞: <task_id> — 未分类错误，需人工检查。日志: logs/session_<ts>.json` |

### 重试上限

同一任务 `task_id` 重试最多 **3 次**。若第 3 次仍返回 `UNKNOWN` 且编译不通过，无论原因如何，保持 `"blocked"` 并报告：

```
[MasterAgent] UNKNOWN 永久阻塞: <task_id> — 已重试 3 次仍失败，需人工介入
```
