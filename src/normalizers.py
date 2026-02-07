from __future__ import annotations

import re
from datetime import datetime
from typing import Optional, Tuple


_DATE_SEPS_PATTERN = re.compile(r"[./\s]+")


def normalize_weight_kg(raw: str) -> Optional[int]:
    """
    중량 문자열을 kg(int)로 정규화
    예: "12,340" -> 12340 / "(12,340)" -> 12340 / " 12340kg " -> 12340 
    단, 숫자가 하나도 없으면 None 반환
    """
    if raw is None:
        return None

    s = str(raw).strip()
    if not s:
        return None

    # 괄호 제거
    if s.startswith("(") and s.endswith(")"):
        s = s[1:-1].strip()

    s = re.sub(r"\bkg\b", " ", s, flags=re.IGNORECASE).strip()

    candidates = re.findall(r"\d{1,3}(?:,\d{3})+|\d+", s)
    if not candidates:
        return None

    # 1) 쉼표 포함 후보 우선 
    comma_candidates = [c for c in candidates if "," in c]
    if comma_candidates:
        pick = max(comma_candidates, key=lambda x: len(x.replace(",", "")))
    else:
        # 2) 없으면 가장 긴 숫자 토큰 선택
        pick = max(candidates, key=len)

    digits = pick.replace(",", "")
    if not digits.isdigit():
        return None

    try:
        return int(digits)
    except ValueError:
        return None


def normalize_time(raw: str) -> Optional[str]:
    """
    시간 문자열을 HH:MM 형태로 정규화
    허용 입력 예: "01:01", "(01:01)", "1:1", "11시 22분", "11시22분", "11:22분"
    """
    if raw is None:
        return None

    s = str(raw).strip()
    if not s:
        return None

    # 괄호 제거
    if s.startswith("(") and s.endswith(")"):
        s = s[1:-1].strip()

    # 1. HH:MM 형태 우선
    m = re.search(r"(\d{1,2})\s*:\s*(\d{1,2})", s)
    if m:
        hh = int(m.group(1))
        mm = int(m.group(2))
        if 0 <= hh <= 23 and 0 <= mm <= 59:
            return f"{hh:02d}:{mm:02d}"
        return None

    # 2. "HH시 MM분" 형태
    m = re.search(r"(\d{1,2})\s*시\s*(\d{1,2})\s*분?", s)
    if m:
        hh = int(m.group(1))
        mm = int(m.group(2))
        if 0 <= hh <= 23 and 0 <= mm <= 59:
            return f"{hh:02d}:{mm:02d}"
        return None

    return None


def _try_parse_date_tokens(y: int, m: int, d: int) -> Optional[str]:
    # 날짜 토큰으로부터 유효한 날짜 생성 시도
    try:
        dt = datetime(y, m, d)
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return None


def normalize_date(raw: str) -> Tuple[Optional[str], Optional[str]]:
    """
    날짜 문자열을 ISO(YYYY-MM-DD)로 정규화
    반환: (date_iso, warning_code)

    warning_code 가능 값:
    - "ambiguous_date_tail" ('2026-01-01-000'처럼 꼬리값이 붙어 있어 잘라냈을 때)
    - "date_parse_failed" (해석 실패)
    - None (성공)
    """
    if raw is None:
        return None, "date_parse_failed"

    s = str(raw).strip()
    if not s:
        return None, "date_parse_failed"

    # 괄호 제거
    if s.startswith("(") and s.endswith(")"):
        s = s[1:-1].strip()

    warning = None

    # 예: 2026-01-01-000 같은 케이스 -> 뒤 꼬리 제거
    tail_cut = re.match(r"^(\d{4}[-/.]\d{1,2}[-/.]\d{1,2})(?:[-/.]\d+)+$", s)
    if tail_cut:
        s = tail_cut.group(1)
        warning = "ambiguous_date_tail"

    # doc_seq: 또는 raw_tail: 같은 전처리 결과가 붙어있으면 제거
    s = re.sub(r"\s+(doc_seq|raw_tail):\d+", "", s)

    # 구분자 통일 후 토큰화
    s2 = _DATE_SEPS_PATTERN.sub("-", s)
    
    # yyyy-mm-dd / yyyy-m-d
    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", s2)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        iso = _try_parse_date_tokens(y, mo, d)
        if iso:
            return iso, warning
        return None, "date_parse_failed"

    # yyyymmdd
    compact = re.sub(r"\D", "", s)
    m = re.match(r"^(\d{4})(\d{2})(\d{2})$", compact)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        iso = _try_parse_date_tokens(y, mo, d)
        if iso:
            return iso, warning
        return None, "date_parse_failed"

    return None, "date_parse_failed"