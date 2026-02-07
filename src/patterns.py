from __future__ import annotations

import re
from typing import List

from .config import Patterns, LabelTokens


DATE_PATTERN = Patterns.DATE
TIME_PATTERN = Patterns.TIME
WEIGHT_KG_PATTERN = Patterns.WEIGHT_KG
VEHICLE_NO_PATTERN = Patterns.VEHICLE_NO
VEHICLE_NO_SIMPLE = Patterns.VEHICLE_NO_SIMPLE

LABEL_TOKENS = LabelTokens.as_dict()

def find_all(pattern: re.Pattern, text: str) -> List[re.Match]:
        return list(pattern.finditer(text)) # 모든 매칭 결과 반환

