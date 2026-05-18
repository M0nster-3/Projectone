#!/usr/bin/env python3
"""SDK Spawner — 使用 Claude Agent SDK 启动拥有完整 tools 和 skills 的子 Agent。

工作流程：
1. 从 progress.json 中按阶段选取任务
2. 在 units/ 目录中定位对应的描述文件（JSON + 同名 MD）
3. 解析章节/节号，在 WillardTopology/ 下创建目标 .lean 文件
4. 启动受限 agent，仅允许写入该 .lean 文件（全自动，无交互）

阶段说明：
  --stage statement  筛选 dependency_status=="ready" && proof_status=="none"
                     使用 prompts/statement_formalization.md
  --stage proof      筛选 dependency_status=="ready" && proof_status=="statement_done"
                     使用 prompts/proof_formalization.md
"""
import argparse, asyncio, json, os, re, sys, time
from datetime import datetime
from pathlib import Path

from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    AssistantMessage,
    ResultMessage,
    TextBlock,
)
from claude_agent_sdk.types import PermissionResultAllow, PermissionResultDeny

sys.stdout.reconfigure(encoding='utf-8')

# 确保 API 密钥对 SDK 可见：SDK 内部读取 ANTHROPIC_API_KEY，
# 但某些环境（如 DeepSeek 兼容端点）可能仅设置 ANTHROPIC_AUTH_TOKEN
if not os.environ.get("ANTHROPIC_API_KEY"):
    token = os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("ANTHROPIC_API_KEY")
    if token:
        os.environ["ANTHROPIC_API_KEY"] = token

PROJECT_ROOT = Path(__file__).resolve().parent.parent  # .autoFormalization/
LEAN_ROOT = PROJECT_ROOT.parent  # WillardTopology/
LOG_DIR = PROJECT_ROOT / "logs"
PROGRESS_PATH = PROJECT_ROOT / "memory" / "progress.json"
LOCK_PATH = PROJECT_ROOT / "memory" / "progress.json.lock"
UNITS_DIR = PROJECT_ROOT / "units"
PROMPTS_DIR = PROJECT_ROOT / "prompts"
WILLARD_TOPOLOGY = LEAN_ROOT / "WillardTopology"
ROOT_LEAN = LEAN_ROOT / "WillardTopology.lean"
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")

# 当前目标任务文件（供 can_use_tool 回调闭包引用）
_TARGET_LEAN_FILE: Path | None = None

# 阶段配置：筛选条件 + 对应的 prompt 文件名 + 本阶段完成状态集合
STAGE_CONFIG = {
    "statement": {
        "filter": "none",
        "prompt_file": "statement_formalization.md",
        "done_statuses": ["statement_done", "proof_in_progress", "done"],
    },
    "proof": {
        "filter": "statement_done",
        "prompt_file": "proof_formalization.md",
        "done_statuses": ["done"],
    },
}


def parse_signal(text: str):
    """从 agent 输出中解析任务完成/失败信号。

    TASK_COMPLETED:Thm1.15
    TASK_FAILED:Thm1.15:error message (possibly multiline)
    """
    if m := re.search(r"TASK_COMPLETED:(\S+)", text):
        return ("TASK_COMPLETED", m.group(1))
    if m := re.search(r"TASK_FAILED:([^:\s]+)", text):
        return ("TASK_FAILED", m.group(1))
    return ("UNKNOWN", None)


def acquire_lock(timeout: int = 60) -> None:
    """通过原子创建锁文件获取互斥锁，若已被占用则排队等待。"""
    start = time.time()
    while True:
        try:
            fd = os.open(LOCK_PATH, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            return
        except FileExistsError:
            if time.time() - start > timeout:
                print(f"[SDK_SPAWNER] EXIT error | 获取 progress.json 锁超时 ({timeout}s)")
                sys.exit(1)
            time.sleep(max(0.1, min(1.0, (timeout - (time.time() - start)) / 10)))


def release_lock() -> None:
    """释放互斥锁。"""
    LOCK_PATH.unlink(missing_ok=True)


# ── 任务选取 ────────────────────────────────────────────────
def select_task(stage: str) -> str:
    """在文件锁保护下读取 progress.json，选取第一个可用任务并立即标记 proof_status。

    - stage=="statement": proof_status "none" → "statement_in_progress"
    - stage=="proof":     proof_status "statement_done" → "proof_in_progress"

    若无可用任务，判断所有条目的 proof_status 是否均已达到本阶段完成状态：
    - 若是：输出 STAGE_COMPLETED 后正常退出
    - 若否：输出 NO_TASK_AVAILABLE 后正常退出
    """
    if not PROGRESS_PATH.exists():
        print(f"[SDK_SPAWNER] EXIT error | progress.json 不存在: {PROGRESS_PATH}")
        sys.exit(1)

    acquire_lock()
    try:
        progress = json.loads(PROGRESS_PATH.read_text(encoding="utf-8"))
        val = STAGE_CONFIG[stage]["filter"]
        done_statuses = STAGE_CONFIG[stage]["done_statuses"]

        for task_id, info in progress.items():
            if info.get("dependency_status") == "ready" and info.get("proof_status") == val:
                info["proof_status"] = (
                    "statement_in_progress" if stage == "statement"
                    else "proof_in_progress"
                )
                PROGRESS_PATH.write_text(
                    json.dumps(progress, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                return task_id

        # 无可用任务：判断是否所有条目均已达到本阶段完成状态
        all_done = all(
            info.get("proof_status") in done_statuses
            for info in progress.values()
        )
        if all_done:
            print("[SDK_SPAWNER] EXIT normal | result=STAGE_COMPLETED")
        else:
            print("[SDK_SPAWNER] EXIT normal | result=NO_TASK_AVAILABLE")
        sys.exit(0)
    finally:
        release_lock()


def find_unit(task_id: str) -> tuple[dict, str] | None:
    """在 units/ 目录下递归搜索与 task_id 对应的 JSON 和同名 MD 文件。

    task_id 中的点号映射为下划线：Def1.1 → Def1_1.{json,md}

    返回 (unit_dict, md_content)；找不到 JSON 时以 exit code 1 退出。
    """
    base_name = task_id.replace(".", "_")
    json_name = f"{base_name}.json"
    md_name = f"{base_name}.md"

    json_matches = list(UNITS_DIR.rglob(json_name))
    if not json_matches:
        print(f"[SDK_SPAWNER] EXIT error | 找不到 unit 文件: {json_name}")
        sys.exit(1)

    json_path = json_matches[0]
    unit = json.loads(json_path.read_text(encoding="utf-8"))

    # 读取同名 MD 文件（详细问题描述）
    md_path = json_path.with_name(md_name)
    md_content = md_path.read_text(encoding="utf-8") if md_path.exists() else ""

    return unit, md_content


# ── .lean 文件路径解析与创建 ───────────────────────────────
def resolve_lean_path(unit: dict) -> Path:
    """根据 unit JSON 解析 .lean 文件路径，创建必要的目录和文件。

    unit JSON 字段：
      - chapter: int       章节号
      - section: int|None  节号（可选）；若无则 .lean 直接放在章节目录下
      - id: str            任务 ID
      - title: str         标题

    目录匹配优先级：
      1. WillardTopology/Ch{chapter}_*/（已有具名目录）
      2. WillardTopology/Ch{chapter}/（自动创建）
    """
    try:
        ch = unit["chapter"]
        task_id = unit["id"]
    except KeyError as e:
        print(f"[SDK_SPAWNER] EXIT error | unit JSON 缺少必要字段: {e}")
        sys.exit(1)

    sec = unit.get("section")  # int or None
    title = unit.get("title", "")

    try:
        # 匹配或创建章节目录
        ch_dirs = list(WILLARD_TOPOLOGY.glob(f"Ch{ch}_*"))
        if ch_dirs:
            ch_dir = ch_dirs[0]
        else:
            ch_dir = WILLARD_TOPOLOGY / f"Ch{ch}"
            ch_dir.mkdir(parents=True, exist_ok=True)

        # 节目录（仅当 section 存在时）—— 已改为直接放在 ch 文件夹下
        # if sec is not None:
        #     target_dir = ch_dir / f"Sec{sec}"
        # else:
        #     target_dir = ch_dir
        target_dir = ch_dir

        target_dir.mkdir(parents=True, exist_ok=True)

        lean_filename = task_id.replace(".", "_") + "_" + title.replace(" ", "_") + ".lean"
        lean_path = target_dir / lean_filename

        if not lean_path.exists():
            lean_path.write_text(f"-- {task_id}: {title}\n\n", encoding="utf-8")

        return lean_path
    except OSError as e:
        print(f"[SDK_SPAWNER] EXIT error | 创建 .lean 文件失败: {e}")
        sys.exit(1)


# ── 依赖更新 ────────────────────────────────────────────────
def update_dependencies(task_id: str) -> None:
    """当任务完成时，更新 progress.json 中下游任务的依赖状态。

    遍历 dependency_status=="pending" 的任务，检查其 unit JSON 中的
    statement_dependency 与 proof_dependency 列表。若 task_id 属于任一列表，
    则将其加入 completed 列表；若 statement_dependency 全部满足，则将
    dependency_status 改为 "ready"。
    """
    if not PROGRESS_PATH.exists():
        return

    acquire_lock()
    try:
        progress = json.loads(PROGRESS_PATH.read_text(encoding="utf-8"))

        for other_id, info in progress.items():
            if info.get("dependency_status") != "pending":
                continue

            base_name = other_id.replace(".", "_")
            json_matches = list(UNITS_DIR.rglob(f"{base_name}.json"))
            if not json_matches:
                continue
            unit_path = json_matches[0]
            unit = json.loads(unit_path.read_text(encoding="utf-8"))

            deps_stmt = unit.get("statement_dependency", [])
            deps_proof = unit.get("proof_dependency", [])

            if task_id not in deps_stmt and task_id not in deps_proof:
                continue

            completed: list[str] = unit.get("completed", [])
            if task_id not in completed:
                completed.append(task_id)
                unit["completed"] = completed
                unit_path.write_text(
                    json.dumps(unit, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )

            if set(completed) >= set(deps_stmt) :
                info["dependency_status"] = "ready"

        PROGRESS_PATH.write_text(
            json.dumps(progress, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    finally:
        release_lock()


def update_api_index(task_id: str, lean_path: Path) -> None:
    """向 api_index.json 添加/更新当前任务的条目。

    从 .lean 文件中提取 import 语句和非注释代码行作为 statement；
    从文件路径构造 lean_name。文件不存在时自动创建空字典。
    """
    api_index_path = PROJECT_ROOT / "memory" / "api_index.json"

    if api_index_path.exists():
        api_index = json.loads(api_index_path.read_text(encoding="utf-8"))
    else:
        api_index = {}

    lean_content = lean_path.read_text(encoding="utf-8")

    imports: list[str] = []
    statement_lines: list[str] = []
    for line in lean_content.split("\n"):
        stripped = line.strip()
        if stripped.startswith("import "):
            imports.append(stripped[len("import "):].strip())
        elif stripped and not stripped.startswith("--"):
            statement_lines.append(stripped)

    relative = lean_path.relative_to(WILLARD_TOPOLOGY)
    parts = [p.replace(".lean", "") for p in relative.parts]
    lean_name = "WillardTopology." + ".".join(parts)

    key = task_id

    api_index[key] = {
        "lean_name": lean_name,
        "file": relative.as_posix(),
        "statement": " ".join(statement_lines),
        "key_imports": imports,
    }

    api_index_path.write_text(
        json.dumps(api_index, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ── 权限回调：仅允许写入目标 .lean 文件 ────────────────────
async def can_use_tool_callback(
    tool_name: str, tool_input: dict, _context
) -> PermissionResultAllow | PermissionResultDeny:
    """全自动模式下限制写工具仅能操作目标 .lean 文件和根模块导入文件。"""
    if tool_name in ("Read", "Glob", "Grep"):
        return PermissionResultAllow()

    if tool_name in ("Edit", "Write"):
        fp = tool_input.get("file_path", "")
        resolved = Path(fp).resolve()
        if _TARGET_LEAN_FILE and resolved == _TARGET_LEAN_FILE.resolve():
            return PermissionResultAllow()
        if resolved == ROOT_LEAN.resolve():
            return PermissionResultAllow()
        return PermissionResultDeny(
            message=f"仅允许写入 {_TARGET_LEAN_FILE} 或 {ROOT_LEAN}，拒绝: {fp}"
        )

    return PermissionResultAllow()


# ── 主流程 ──────────────────────────────────────────────────
async def main_async():
    global _TARGET_LEAN_FILE

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--stage",
        required=True,
        choices=["statement", "proof"],
        help="工作阶段：statement（形式化陈述）或 proof（形式化证明）",
    )
    parser.add_argument(
        "--tools",
        default="",
        help="额外追加的工具名，逗号分隔（如 'tool_a,tool_b'）",
    )
    args = parser.parse_args()

    stage = args.stage
    extra_tools = [t.strip() for t in args.tools.split(",") if t.strip()]

    # ── 1. 选取任务 ──
    task_id = select_task(stage)

    # ── 2. 定位 unit 文件（JSON + MD） ──
    unit, md_content = find_unit(task_id)

    # ── 3. 解析并创建目标 .lean 文件 ──
    lean_path = resolve_lean_path(unit)

    _TARGET_LEAN_FILE = lean_path
    print(f"[SDK_SPAWNER] 开始形式化{stage} | 任务: {task_id}  →  {lean_path}")

    # ── 4. 读取阶段对应的 prompt ──
    prompt_filename = STAGE_CONFIG[stage]["prompt_file"]
    prompt_path = PROMPTS_DIR / prompt_filename
    if not prompt_path.exists():
        print(f"[SDK_SPAWNER] EXIT error | 找不到 prompt 文件: {prompt_path}")
        sys.exit(1)
    base_prompt = prompt_path.read_text(encoding="utf-8")

    # ── 5. 构造完整 system prompt ──
    task_info = (
        f"\n\n---\n\n# 当前任务\n\n"
        f"- 项目根目录: {LEAN_ROOT}\n"
        f"- 任务 ID: {task_id}\n"
        f"- 类型: {unit.get('type', 'Unknown')}\n"
        f"- 章节: 第 {unit['chapter']} 章"
        + (f", 第 {unit['section']} 节" if unit.get("section") is not None else "")
        + f"\n- 标题: {unit.get('title', '')}\n"
        f"- 目标文件: {lean_path}\n"
        f"- 摘要: {unit.get('summary', '')}\n"
        f"\n**你只能编辑这一个文件: {lean_path}**\n"
        f"**如需追加模块导入，可同时编辑: {ROOT_LEAN}**\n"
    )
    if md_content:
        task_info += (
            f"\n---\n\n# 问题详细描述\n\n{md_content}\n"
        )

    system_prompt = base_prompt + task_info

    # ── 5.5. 确保工作目录存在 ──
    cwd_path = PROJECT_ROOT / "tmp" / task_id.replace(".", "_")
    cwd_path.mkdir(parents=True, exist_ok=True)

    # ── 6. 构造 tools 配置 ──
    tools_config: dict | list = {"type": "preset", "preset": "claude_code"}
    if extra_tools:
        tools_config = [tools_config] + extra_tools

    # ── 7. 启动 agent ──
    options = ClaudeAgentOptions(
        model=MODEL if MODEL else None,
        tools=tools_config,
        skills="all",
        system_prompt={
            "type": "preset",
            "preset": "claude_code",
            "append": (
                "\n\n---\n\n# 自定义任务指令（优先级高于上述默认行为）\n\n"
                + system_prompt
            ),
        },
        permission_mode="dontAsk",
        allowed_tools=["Read", "Glob", "Grep", "Bash"],
        can_use_tool=can_use_tool_callback,
        cwd=str(cwd_path),
        setting_sources=["project"],
        max_turns=100,
        task_budget={"total": 32000},
    )

    all_text: list[str] = []
    sdk_error: str | None = None
    async def prompt_stream():
        yield {
            "type": "user",
            "session_id": "",
            "message": {"role": "user", "content": "开始执行工作流程。"},
            "parent_tool_use_id": None,
        }

    try:
        async for message in query(prompt=prompt_stream(), options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        all_text.append(block.text)
            elif isinstance(message, ResultMessage):
                if message.result:
                    all_text.append(message.result)
    except Exception as e:
        sdk_error = f"{type(e).__name__}: {e}"
        all_text.append(sdk_error)

    text = "\n".join(all_text)

    # 日志
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    (LOG_DIR / f"session_{ts}.json").write_text(
        json.dumps(
            {
                "timestamp": ts,
                "stage": stage,
                "task_id": task_id,
                "lean_path": str(lean_path),
                "system_prompt": system_prompt,
                "output": text,
                "sdk_error": sdk_error,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    # 输出结果
    signal, task = parse_signal(text)
    if signal == "TASK_COMPLETED":
        print(f"[SDK_SPAWNER] EXIT normal | result=TASK_COMPLETED | task={task_id}")
        acquire_lock()
        try:
            progress = json.loads(PROGRESS_PATH.read_text(encoding="utf-8"))
            if task_id in progress:
                progress[task_id]["proof_status"] = (
                    "statement_done" if stage == "statement" else "done"
                )
            PROGRESS_PATH.write_text(
                json.dumps(progress, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        finally:
            release_lock()
        if stage == "statement":
            update_dependencies(task_id)
            update_api_index(task_id, lean_path)
    else:
        if signal == "TASK_FAILED":
            print(f"[SDK_SPAWNER] EXIT normal | result=TASK_FAILED | task={task_id}")
        else:
            print(f"[SDK_SPAWNER] EXIT normal | result=UNKNOWN | task={task_id} | raw={text[:200]}")
        acquire_lock()
        try:
            progress = json.loads(PROGRESS_PATH.read_text(encoding="utf-8"))
            if task_id in progress:
                progress[task_id]["proof_status"] = (
                    "none" if stage == "statement" else "statement_done"
                )
                progress[task_id]["dependency_status"] = "blocked"
                PROGRESS_PATH.write_text(
                    json.dumps(progress, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
        finally:
            release_lock()


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
