"""Exact instructions for the two released adapters."""
from ._qing_protocol import MASTER_PROMPT
from ._joseon_protocol import PROMPT_HANGUL


def user_message(title: str, task: str = "qing") -> dict[str, str]:
    if not isinstance(title, str) or not title.strip():
        raise ValueError("A nonempty title string is required")
    if task == "qing":
        text = f"{MASTER_PROMPT}\n\n請解析這個官職：\n`{title}`"
    elif task == "joseon":
        text = f"{PROMPT_HANGUL}\n\n분석할 관직명:\n`{title}`"
    else:
        raise ValueError(f"Unknown task: {task}")
    return {"role": "user", "content": text}

