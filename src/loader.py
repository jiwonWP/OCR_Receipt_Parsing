import json
from pathlib import Path
from typing import Any, Dict

from .schema import RawDocument


def load_ocr_json(path: str) -> RawDocument:
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        data: Dict[str, Any] = json.load(f)

    # OCR 원문과 메타정보 분리
    raw_text = data.get("text", "")
    meta = {k: v for k, v in data.items() if k != "text"}

    return RawDocument(
        source_path=str(p),
        raw_text=raw_text,
        meta=meta,
    )
