"""
initialization.py — Phase 1 初始化脚本

扫描 units/ 目录下所有预处理 JSON，生成或更新 progress.json。

用法:
    python .autoFormalization/tools/initialization.py [--dependency {statement,proof}]
"""

import argparse
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

PROJECT_ROOT = Path(__file__).resolve().parent.parent  # .autoFormalization/


def collect_unit_files(units_dir: Path) -> list[Path]:
    """递归收集 units/ 下所有 .json 文件。"""
    if not units_dir.is_dir():
        print(f"[initialization] 错误: units/ 目录不存在: {units_dir}", file=sys.stderr)
        sys.exit(1)
    files = sorted(units_dir.rglob("*.json"))
    if not files:
        print("[initialization] 警告: units/ 目录中未找到任何 .json 文件", file=sys.stderr)
    return files


def load_unit(filepath: Path) -> dict | None:
    """读取单个预处理 JSON，返回其字典；解析失败则返回 None。"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"[initialization] 警告: 跳过 {filepath}: {e}", file=sys.stderr)
        return None


def compute_dependency_status(unit: dict, dep_field: str) -> str:
    """
    比较 completed 与指定依赖字段，判定 dependency_status。

    Args:
        unit: 预处理 JSON 字典
        dep_field: "statement_dependency" 或 "proof_dependency"

    Returns:
        "ready"  — set(dependency) ⊆ set(completed)
        "pending" — 否则

    Raises:
        TypeError: 依赖字段或 completed 的值不是列表
    """
    deps = unit.get(dep_field, [])
    completed = unit.get("completed", [])
    if not isinstance(deps, list):
        raise TypeError(
            f"单元 {unit.get('id', '?')}: 字段 {dep_field} 应为列表，实际类型为 {type(deps).__name__}"
        )
    if not isinstance(completed, list):
        raise TypeError(
            f"单元 {unit.get('id', '?')}: 字段 completed 应为列表，实际类型为 {type(completed).__name__}"
        )
    return "ready" if set(completed) >= set(deps) else "pending"


def load_existing_progress(progress_path: Path) -> dict:
    """加载已有的 progress.json，不存在或读取出错则返回空字典。"""
    if progress_path.is_file():
        try:
            with open(progress_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def build_progress(
    units: list[dict],
    existing: dict,
    dep_field: str,
) -> dict:
    """
    构建完整的 progress 字典。

    以已有 progress 为基底，扫描 units 目录中的所有预处理单元，
    新增条目或更新已有条目的 dependency_status，保留 proof_status。

    Args:
        units: 所有预处理单元列表
        existing: 已有的 progress 字典
        dep_field: 依赖字段名

    Returns:
        新的 progress 字典
    """
    progress: dict = dict(existing)  # 以已有条目为基底，保留未出现在 units 中的旧条目

    for unit in units:
        uid = unit.get("id")
        if not uid:
            print(f"[initialization] 警告: 跳过无 id 字段的单元: {unit.get('title', '?')}", file=sys.stderr)
            continue

        dep_status = compute_dependency_status(unit, dep_field)

        if uid in existing:
            # 已存在：保留 proof_status，仅更新 dependency_status
            proof_status = existing[uid].get("proof_status", "none")
        else:
            # 新条目：proof_status = "none"
            proof_status = "none"

        progress[uid] = {
            "dependency_status": dep_status,
            "proof_status": proof_status,
        }

    return progress


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Phase 1 初始化：扫描 units/ 生成 progress.json"
    )
    parser.add_argument(
        "--dependency",
        choices=["statement", "proof"],
        default="statement",
        help="选择依据哪个依赖字段判定 dependency_status（默认: statement）",
    )
    args = parser.parse_args()

    dep_field = f"{args.dependency}_dependency"

    units_dir = PROJECT_ROOT / "units"
    memory_dir = PROJECT_ROOT / "memory"
    progress_path = memory_dir / "progress.json"

    # 1. 收集所有单元文件
    unit_files = collect_unit_files(units_dir)
    if not unit_files:
        print("[initialization] 无单元文件，退出。", file=sys.stderr)
        sys.exit(0)

    # 2. 加载所有单元，确保 completed 字段存在
    units: list[dict] = []
    for fp in unit_files:
        unit = load_unit(fp)
        if unit is None:
            continue
        if "completed" not in unit:
            unit["completed"] = []
            with open(fp, "w", encoding="utf-8") as f:
                json.dump(unit, f, indent=2, ensure_ascii=False)
                f.write("\n")
        units.append(unit)

    if not units:
        print("[initialization] 无有效单元数据，退出。", file=sys.stderr)
        sys.exit(0)

    # 3. 加载已有 progress
    existing = load_existing_progress(progress_path)
    existing_ids = set(existing)

    # 4. 构建 progress
    progress = build_progress(units, existing, dep_field)

    # 5. 确保 memory 目录存在，写入 progress.json
    memory_dir.mkdir(parents=True, exist_ok=True)
    with open(progress_path, "w", encoding="utf-8") as f:
        json.dump(progress, f, indent=2, ensure_ascii=False)
        f.write("\n")

    unit_ids = {u["id"] for u in units if "id" in u}
    new_count = len(unit_ids - existing_ids)
    updated_count = len(unit_ids & existing_ids)

    print(f"[initialization] 完成: 总计 {len(progress)} 条, 新增 {new_count} 条, 更新 dependency_status {updated_count} 条")
    print(f"[initialization] dependency 字段: {dep_field}")
    print(f"[initialization] progress.json → {progress_path}")


if __name__ == "__main__":
    main()
