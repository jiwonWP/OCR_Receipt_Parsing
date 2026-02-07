from __future__ import annotations

from dataclasses import asdict
from typing import Dict, Iterable, List, Optional, Tuple
import re
from .schema import PreprocessedDocument, Candidate, ExtractedCandidates
from .patterns import (
    DATE_PATTERN,
    TIME_PATTERN,
    WEIGHT_KG_PATTERN,
    VEHICLE_NO_PATTERN,
    LABEL_TOKENS,
)

def _iter_lines(text: str) -> List[str]:
    # 텍스트를 라인 단위로 분할
    return text.splitlines()


def _add_candidate(
    out: List[Candidate],
    field: str,
    value_raw: str,
    source_line: str,
    method: str,
    score: int,
    meta: Optional[Dict] = None,
) -> None:
    # 후보 리스트에 새 후보 추가
    value_raw = (value_raw or "").strip()
    source_line = (source_line or "").strip()
    if not value_raw:
        return
    if meta is None:
        meta = {}

    out.append(
        Candidate(
            field=field,
            value_raw=value_raw,
            source_line=source_line,
            method=method,
            score=score,
            meta=meta,
        )
    )

# 중복 후보 제거 - 같은 field+value는 최고 score만 유지
def _dedupe_candidates(candidates: List[Candidate]) -> List[Candidate]:
    by_key: Dict[Tuple[str, str], Candidate] = {}
    
    for c in candidates:
        key = (c.field, c.value_raw)
        if key not in by_key or c.score > by_key[key].score:
            by_key[key] = c
    
    return list(by_key.values())

# 패턴 매칭
def _first_match(pattern, text: str):
    return pattern.search(text)

# 모든 매칭 결과 반환
def _all_matches(pattern, text: str):
    return list(pattern.finditer(text))


# 라벨 기반 추출
def _match_any_token(line: str, tokens: Iterable[str]) -> Optional[str]:
    for t in tokens:
        if t in line:
            return t
    return None

# 중량(kg) 라벨 주변에서 값 추출
def _extract_weight_from_line(line: str) -> Optional[str]:
    """
    중량 값만 추출
    1. 시간 패턴(HH:MM) 제거
    2. 남은 텍스트에서 kg 패턴 추출
    """
    # 1. 시간 패턴 제거 (HH:MM / HH:MM:SS)
    cleaned = re.sub(r'\b\d{1,2}:\d{2}(?::\d{2})?\b', '', line)   

    # 2. kg 패턴 찾기
    m = WEIGHT_KG_PATTERN.search(cleaned)
    if m:
        return m.group(0)
    
    return None


def _extract_weight_near_line(lines: List[str], idx: int) -> Optional[Tuple[str, str]]:
    line = lines[idx]
    
    # 같은 줄에서 추출
    weight = _extract_weight_from_line(line)
    if weight:
        return (weight, line)

    # 다음 줄 확인
    if idx + 1 < len(lines):
        next_line = lines[idx + 1]
        
        # [방어 로직] 다음 줄에 다른 핵심 라벨(차량, 날짜, 다른 중량 등)이 보이면 
        # 현재 라벨의 값일 확률이 낮으므로 추출하지 않음
        other_labels = ["차량", "번호", "일자", "일시", "총중량", "차중량", "실중량"]
        if not any(lbl in next_line for lbl in other_labels):
            weight = _extract_weight_from_line(next_line)
            if weight:
                return (weight, next_line)

    return None

# 차량번호 라벨 라인에서 digits-only 추출
# 전형적 패턴 실패 시 후보 수집용
def _extract_vehicle_digits_from_label_line(line: str, label_token: str) -> str:
    parts = line.split(label_token, 1)
    tail = parts[1] if len(parts) > 1 else ""
    digits = "".join(ch for ch in tail if ch.isdigit())
    return digits.strip()

# 라벨 기반 후보 추출
# 매칭 성공 시 score를 높게 부여
def extract_by_label(normalized_text: str) -> List[Candidate]:
    lines = _iter_lines(normalized_text)
    out: List[Candidate] = []

    weight_label_map = [
        ("gross_weight_kg", LABEL_TOKENS.get("gross_weight", [])),
        ("tare_weight_kg", LABEL_TOKENS.get("tare_weight", [])),
        ("net_weight_kg", LABEL_TOKENS.get("net_weight", [])),
    ]

    dt_label_map = [
        ("date", LABEL_TOKENS.get("date", []), DATE_PATTERN),
        ("time", LABEL_TOKENS.get("time", []), TIME_PATTERN),
    ]
    vehicle_tokens = LABEL_TOKENS.get("vehicle_no", [])

    for i, line in enumerate(lines):
        # 1. 중량(kg) 라벨 기반
        for field, tokens in weight_label_map:
            token = _match_any_token(line, tokens)
            if not token:
                continue

            # 라벨이 발견된 위치를 찾고, 그 이후의 문자열만 추출 대상로 사용
            token_index = line.find(token)
            search_target = line[token_index + len(token):]
            
            # 현재 줄의 라벨 뒷부분에서 먼저 검색
            value_raw = _extract_weight_from_line(search_target)
            src_line = line
            
            # 현재 줄 뒷부분에 숫자가 없다면 다음 줄 확인
            if not value_raw and i + 1 < len(lines):
                next_line = lines[i + 1]
                # 다음 줄에 다른 라벨이 없는지 확인하는 방어 로직
                other_labels = ["차량", "번호", "일자", "날짜", "총중량", "차중량", "실중량", "공차"]
                if not any(lbl in next_line for lbl in other_labels):
                    value_raw = _extract_weight_from_line(next_line)
                    src_line = next_line

            if value_raw:
                _add_candidate(
                    out,
                    field=field,
                    value_raw=value_raw,
                    source_line=src_line,
                    method="label",
                    score=90,
                    meta={"line_index": i, "label_token": token},
                )

        # 2. 날짜/시간 라벨 기반
        for field, tokens, pattern in dt_label_map:
            token = _match_any_token(line, tokens)
            if not token:
                continue

            targets = [(line, i)]
            if i + 1 < len(lines):
                targets.append((lines[i + 1], i + 1))

            for tgt_line, tgt_idx in targets:
                m = _first_match(pattern, tgt_line)
                if m:
                    _add_candidate(
                        out,
                        field=field,
                        value_raw=m.group(0),
                        source_line=tgt_line,
                        method="label",
                        score=85,
                        meta={"line_index": tgt_idx, "label_token": token},
                    )
                    break  
    
        # 3. 차량번호 라벨 기반
        v_token = _match_any_token(line, vehicle_tokens)
        if v_token:
            # 1. 같은 줄
            m = _first_match(VEHICLE_NO_PATTERN, line)
            if m:
                _add_candidate(
                    out,
                    field="vehicle_no",
                    value_raw=m.group(0),
                    source_line=line,
                    method="label",
                    score=85,
                    meta={"line_index": i, "label_token": v_token},
                )
            else:
                # 2. 줄바꿈 케이스
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    m2 = _first_match(VEHICLE_NO_PATTERN, next_line)
                    if m2:
                        _add_candidate(
                            out,
                            field="vehicle_no",
                            value_raw=m2.group(0),
                            source_line=next_line,
                            method="label",
                            score=85,
                            meta={"line_index": i + 1, "label_token": v_token},
                        )
                        continue

                # 3.  전형적 패턴 실패 →후보 수집
                digits = _extract_vehicle_digits_from_label_line(line, v_token)
                if digits:
                    _add_candidate(
                        out,
                        field="vehicle_no",
                        value_raw=digits,
                        source_line=line,
                        method="label",
                        score=60,  
                        meta={
                            "line_index": i,
                            "label_token": v_token,
                            "ambiguous": True,
                        },
                    )

    return out


# 패턴 기반 후보 추출
# 최소 후보 확보 목적으로 Score는 label 기반보다 낮게 부여
def extract_by_pattern(normalized_text: str) -> List[Candidate]:
    lines = _iter_lines(normalized_text)
    out: List[Candidate] = []

    for i, line in enumerate(lines):
        # 날짜
        for m in _all_matches(DATE_PATTERN, line):
            _add_candidate(
                out,
                field="date",
                value_raw=m.group(0),
                source_line=line,
                method="pattern",
                score=50,
                meta={"line_index": i},
            )

        # 시간
        for m in _all_matches(TIME_PATTERN, line):
            _add_candidate(
                out,
                field="time",
                value_raw=m.group(0),
                source_line=line,
                method="pattern",
                score=50,
                meta={"line_index": i},
            )

        # 중량(kg)
        cleaned = re.sub(r'\b\d{1,2}:\d{2}(?::\d{2})?\b', '', line)
        for m in _all_matches(WEIGHT_KG_PATTERN, cleaned):
            _add_candidate(
                out,
                field="weight_kg",
                value_raw=m.group(0),
                source_line=line,
                method="pattern",
                score=45,
                meta={"line_index": i},
            )

        # 차량번호
        for m in _all_matches(VEHICLE_NO_PATTERN, line):
            _add_candidate(
                out,
                field="vehicle_no",
                value_raw=m.group(0),
                source_line=line,
                method="pattern",
                score=45,
                meta={"line_index": i},
            )

    return out


# 후보 추출
def extract_candidates(preprocessed: PreprocessedDocument) -> ExtractedCandidates:
    label_candidates = extract_by_label(preprocessed.normalized_text)
    pattern_candidates = extract_by_pattern(preprocessed.normalized_text)

    # 라벨 기반으로 이미 잡힌 값을 패턴으로 중복 수집 할 수 있어서 완전 동일한 것만 dedupe 
    candidates = _dedupe_candidates(label_candidates + pattern_candidates)

    warnings: List[str] = []

    # 주요 필드 존재 여부
    if not any(c.field in ("date",) for c in candidates):
        warnings.append("Extractor: no date candidates detected")
    if not any(c.field in ("time",) for c in candidates):
        warnings.append("Extractor: no time candidates detected")
    if not any(c.field in ("vehicle_no",) for c in candidates):
        warnings.append("Extractor: no vehicle_no candidates detected")

    # weight는 label 기반 3가지(gross/tare/net) / fallback 있으면 통과
    if not any(c.field.endswith("_weight_kg") or c.field == "weight_kg" for c in candidates):
        warnings.append("Extractor: no weight(kg) candidates detected")

    return ExtractedCandidates(
        raw_text=preprocessed.raw_text,
        normalized_text=preprocessed.normalized_text,
        candidates=candidates,
        warnings=warnings,
    )
