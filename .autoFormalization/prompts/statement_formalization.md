# Statement Formalization Agent

将自然语言定理/定义形式化为 Lean 4 statement（proof 用 `sorry` 占位），通过 `lake build` 编译验证。

## 核心原则

**忠实原文**：不改写、不缩写、不引入原文之外的证明路线。形式化必须严格对应原始数学陈述。

## 输入

系统提示词中已包含：项目根目录、任务 ID、类型（Definition/Theorem）、章节、标题、目标 `.lean` 文件绝对路径、根模块路径、摘要、问题详细描述（含 LaTeX）。

## 工作流程

### 0. 类型判断

- **Definition**：形式化为 `def`，直接写出定义体，编译通过后输出 `TASK_COMPLETED:<TheoremID>`。
- **Theorem/Lemma/Corollary**：形式化为 `theorem`，proof 用 `sorry` 占位，按下方流程执行。

### 1. 读取上下文

- 读取目标 `.lean` 文件（已有占位注释 `-- <TheoremID>: <title>`,已有的内容可视情况使用）
- 视情况读取 `.autoFormalization/memory/api_index.json`（若不存在则视为 `{}`）。需引用已形式化的定理/定义时，从此文件查询
- 定位并读取对应 unit JSON：`.autoFormalization/units/Ch{chapter}/{id_safe}.json`，获取 `statement_dependency`

### 2. 构造 import

对 `statement_dependency` 中每个 `dep_id`，从 `api_index.json[dep_id].lean_name` 获取模块名，生成 `import` 语句。同时确保 `import WillardTopology.Basic`。

### 3. 形式化 statement

命名与格式：
- 定理名小写+下划线：`thm_2_5_closure_neighborhood`
- 隐式参数用 `{}`，显式用 `()`
- `:= by` 后换行缩进写 `sorry`
- `open Set` 后使用集合论符号（`Set X`、`∈`、`⊆`、`∩`、`∪` 等）

### 4. 注册模块导入

检查根模块 `WillardTopology.lean` 中是否有目标模块的 import 行。若没有则追加：
```lean
import WillardTopology.<ChapterDir>.<ModuleName>
```

### 5. 编译验证

```bash
lake build
```

### 6a. 编译通过 → 输出

```
TASK_COMPLETED:<TheoremID>
```

### 6b. 编译失败 → 修复重试

分析错误 → 修改 `.lean` 文件 → 重新 `lake build`，最多 **10 轮**。

常见错误速查：

| 错误 | 典型消息 | 修复 |
|---|---|---|
| unknown identifier | `unknown identifier: closure` | 检查拼写/API 名称，添加 `open` |
| type mismatch | `has type ... but is expected ...` | 检查类型注解 |
| failed to synthesize | `failed to synthesize instance` | 补充 typeclass 参数 |
| unknown module | `unknown package` | 修正 import 路径 |

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
| `TASK_COMPLETED:<TheoremID>` | 编译通过 |
| `TASK_FAILED:<TheoremID>:<error>` | 失败，spawner 回退 proof_status 并设 blocked |

**约束**：
- 信号必须是最后一行输出，输出后立即停止
- 若未输出任何信号，spawner 视为 `UNKNOWN` 并标记为 `blocked`
