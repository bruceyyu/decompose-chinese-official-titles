"""Qing instructions, field definitions, and response/metric helpers."""

from __future__ import annotations

import json
from typing import Any


STRING_FIELDS = [
    "original_title",
    "duty_office",
    "base_office",
    "office_status",
    "qualification_title",
    "jurisdiction",
    "garrison",
    "noble_title",
]

ARRAY_FIELDS = [
    "local_department",
    "central_department",
    "military_department",
    "assignment",
    "additional_title",
    "ceremonial_office",
    "warrior_title",
    "honors_awards",
]

ALL_FIELDS = STRING_FIELDS + ARRAY_FIELDS

MASTER_PROMPT = """
角色:
你是一位精通清代官制的歷史學家。你的任務是從包含噪聲（如 NA、-、OCR錯誤）的官職描述中，提取結構化信息。

任務:
請先在內部完成實體邊界切分，再將結果精確映射到指定 JSON 字段。

實體邊界切分時請辨認：
1. 機構/層級（包含地方、中央、武職等）
2. 核心官職與本職
3. 差使/任務（臨時性或專門性職責）
4. 前後綴/加銜/榮譽/爵位

JSON 字段定義:
- original_title: 原始字符串，禁止修改
- duty_office: 核心實缺/差遣官職，即官員實際行使職權的職位
- base_office: 原隸屬本職（若無差遣為 null）
- local_department, central_department, military_department: 隸屬機構數組
- office_status: 署理、候補等狀態
- qualification_title: 名義資歷（如盡先補用）
- jurisdiction: 管轄區
- garrison: 駐地
- assignment: 差使任務數組
- additional_title: 加銜數組
- ceremonial_office: 榮譽虛銜數組
- noble_title: 爵位
- warrior_title: 勇號數組
- honors_awards: 封號賞賜數組

規則:
1. 語法解構與純淨度：提取 duty_office 或 base_office 時，必須剝離品階、狀態和榮譽，分別放入適當字段。duty_office 必須是純淨的職權名詞。
2. 層級空間約束：duty_office 必須與 local_department 的最終行政層級匹配。高於當前機構層級的官名應判為 additional_title 或 qualification_title。
3. 實體守恆：只能修復錯別字或向上歸類，禁止捏造文本中不存在的官職。找不到實質核心職務時，duty_office 必須為 null。
4. 核心官職標準化：地理/轄區前綴移入 local_department 或 jurisdiction。遇到「特定前綴 + 通用官職」時，通用部分放入 duty_office，特定前綴放入 jurisdiction。多個實缺中選擇與當前部門匹配且權力最大者。

輸出格式:
只輸出一個合法 JSON object，不要輸出分析、說明或 Markdown code fence。空的單值字段填 null，空的多值字段填 []。
""".strip()


def extract_json_object(text: str) -> dict[str, Any] | None:
    """Extract the first valid JSON object from a model response."""
    decoder = json.JSONDecoder()
    stripped = text.strip()

    try:
        value = json.loads(stripped)
        if isinstance(value, list) and value and isinstance(value[0], dict):
            return value[0]
        return value if isinstance(value, dict) else None
    except json.JSONDecodeError:
        pass

    for index, character in enumerate(stripped):
        if character != "{":
            continue
        try:
            value, _ = decoder.raw_decode(stripped[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    return None






