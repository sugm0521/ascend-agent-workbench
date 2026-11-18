"""Emit a naming reminder for UserPromptSubmit; no network or state writes."""

import json
from pathlib import Path
import sys


def main():
    try:
        event = json.loads(sys.stdin.buffer.read().decode("utf-8-sig"))
    except (ValueError, UnicodeError):
        print("chat naming hook: invalid event; skipped", file=sys.stderr)
        return 0
    if not isinstance(event, dict) or event.get("hook_event_name") != "UserPromptSubmit":
        return 0
    skill = Path(__file__).resolve().parents[1] / "SKILL.md"
    if not skill.is_file():
        print("chat naming hook: skill unavailable; skipped", file=sys.stderr)
        return 0
    context = (
        f"当前项目已启用会话命名。按 {skill.as_posix()} 处理："
        "新任务目标明确或明显变化时，检查并按 [类型] 对象 | 具体目标 调整当前会话标题，"
        "无需逐次确认，改名后回读核对；普通追问不改，保留用户明确指定的标题。"
        "目标未明确先正常澄清。只处理当前会话，批量整理、移动和归档沿用用户明确范围。"
        "工具不可用时说明缺口并继续业务任务。"
    )
    result = {"hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit", "additionalContext": context,
    }}
    # ASCII JSON is portable across Windows console code pages; decoded text is Unicode.
    print(json.dumps(result, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
