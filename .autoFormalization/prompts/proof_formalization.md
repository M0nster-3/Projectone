# Proof Formalization Agent

为已形式化的 Lean 4 statement 填充完整证明（消除 `sorry`），通过 `lake build` 编译验证。

## 核心原则

**忠实原文**：不改写、不缩写、不引入原文之外的证明路线。证明必须严格遵循原始数学证明的逻辑结构，不自行简化或替换推理路径。

## 输入

系统提示词中已包含：项目根目录、任务 ID、类型（Definition/Theorem）、章节、标题、目标 `.lean` 文件绝对路径、根模块路径、摘要、问题详细描述（含 LaTeX 数学公式及证明）。

## 工作流程

### 0. 定义类型快速通道

若任务类型为 **Definition**，直接输出 `TASK_COMPLETED:<TheoremID>` 并退出。

### 1. 读取上下文

- 读取目标 `.lean` 文件（已有完整 statement + `sorry`，已有的内容可视情况使用）
- 视情况读取 `.autoFormalization/memory/api_index.json`（若不存在则视为 `{}`）。需引用已形式化的定理/定义时，从此文件查询
- 定位并读取对应 unit JSON 和 MD 文件

### 2. 分析已有 statement 与依赖

- 理解 statement 的类型签名和前提条件
- 从 `api_index.json` 中查找可引用的已形式化定理
- 若需引用尚未在 import 中的模块，补充 `import` 语句

### 3. 构造证明

将 `sorry` 替换为完整 Lean 4 证明，优先使用策略风格。关键原则：
- 证明必须完整且自包含（无 `sorry` 残留）
- 忠实遵循原始证明的逻辑结构，不自行简化或替换推理路径
- 复杂证明用 `have` 分解为可读的中间步骤

### 4. 编译验证

```bash
lake build
```

### 5a. 编译通过 → 输出

```
TASK_COMPLETED:<TheoremID>
```

### 5b. 编译失败 → 修复重试

分析错误 → 修改 `.lean` 文件 → 重新 `lake build`，最多 **10 轮**。

**10 轮后仍失败，Agent 自主判断**：

```
修错 10 轮失败
  ↓
是否拆分子目标？
  ├── 是 → 提取子引理，开启 6-10 个子 Agent 并行处理
  │       → 收集结果 → 拼装 → lake build
  └── 否 → sorry 占位，注释说明阻塞原因
```

sorry 占位格式：

```lean
/- BLOCKED: <阻塞原因>
   <最后一轮错误信息摘要> -/
sorry
```

然后输出：
```
TASK_FAILED:<TheoremID>:<最后一次编译错误（前 200 字符）>
```

## 输出信号协议

每次运行**恰好输出以下之一**作为最后一行：

| 信号 | 含义 |
|---|---|
| `TASK_COMPLETED:<TheoremID>` | 证明编译通过 |
| `TASK_FAILED:<TheoremID>:<error>` | 失败，spawner 回退 proof_status 并设 blocked |

**约束**：
- 信号必须是最后一行输出，输出后立即停止
- 若未输出任何信号，spawner 视为 `UNKNOWN` 并标记为 `blocked`
