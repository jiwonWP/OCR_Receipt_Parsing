from __future__ import annotations

import re
from dataclasses import asdict
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .schema import PreprocessedDocument, Candidate, ExtractedCandidates, ExtractionMetadata
from .patterns import (
    DATE_PATTERN,
    TIME_PATTERN,
    WEIGHT_KG_PATTERN,
    VEHICLE_NO_PATTERN,
    VEHICLE_NO_SIMPLE,
    LABEL_TOKENS,
)


def _iter_lines(text: str) -> List[str]:
    return text.splitlines()


def _first_match(pattern: re.Pattern, text: str) -> Optional[re.Match]:
    return pattern.search(text)


def _all_matches(pattern: re.Pattern, text: str) -> List[re.Match]:
    return list(pattern.finditer(text))


def _match_any_token(line: str, tokens: Iterable[str]) -> Optional[str]:
    for t in tokens:
        if t in line:
            return t
    return None


def _make_extraction_meta(
    field: str,
    strategy_used: str,
    raw_match: str,
    normalized_match: str,
    source_line_index: int,
    confidence: float,
    is_imputed: bool = False,
    notes: str = "",
) -> Dict[str, Any]:
    m = ExtractionMetadata(
        field=field,
        strategy_used=strategy_used,
        raw_match=raw_match,
        normalized_match=normalized_match,
        source_line_index=source_line_index,
        confidence=confidence,
        is_imputed=is_imputed,
        notes=notes,
    )
    return asdict(m)


def _add_candidate(
    out: List[Candidate],
    field: str,
    value_raw: str,
    source_line: str,
    method: str,
    score: int,
    meta: Optional[Dict[str, Any]] = None,
) -> None:
    value_raw = (value_raw or "").strip()
    source_line = (source_line or "").strip()
    if not value_raw:
        return

    if meta is None:
        meta = {}

    # 모든 후보에 ExtractionMetadata가 붙도록
    if "extraction_metadata" not in meta:
        line_index = int(meta.get("line_index", -1) if meta.get("line_index") is not None else -1)
        meta["extraction_metadata"] = _make_extraction_meta(
            field=field,
            strategy_used="label_match" if method == "label" else "pattern_fallback",
            raw_match=value_raw,
            normalized_match=value_raw,
            source_line_index=line_index,
            confidence=0.9 if method == "label" else 0.5,
            notes="auto_attached",
        )

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


def _dedupe_candidates(candidates: List[Candidate]) -> List[Candidate]:
    by_key: Dict[Tuple[str, str], Candidate] = {}
    for c in candidates:
        key = (c.field, c.value_raw)
        if key not in by_key or c.score > by_key[key].score:
            by_key[key] = c
    return list(by_key.values())


def _extract_weight_near_line(lines: List[str], idx: int) -> Optional[Tuple[str, str]]:
    """
    중량(kg) 값 추출 (라벨 근처)
    1) 같은 줄에서 WEIGHT_KG_PATTERN
    2) 다음 줄에서 WEIGHT_KG_PATTERN
    """
    line = lines[idx]
    m = _first_match(WEIGHT_KG_PATTERN, line)
    if m:
        return (m.group(0), line)

    if idx + 1 < len(lines):
        next_line = lines[idx + 1]
        m2 = _first_match(WEIGHT_KG_PATTERN, next_line)
        if m2:
            return (m2.group(0), next_line)

    return None


def _extract_vehicle_digits_from_label_line(line: str, label_token: str) -> str:
    parts = line.split(label_token, 1)
    tail = parts[1] if len(parts) > 1 else ""
    digits = "".join(ch for ch in tail if ch.isdigit())
    return digits.strip() 


def extract_by_label(normalized_text: str) -> Tuple[List[Candidate], List[str]]:
    """
    라벨 기반 후보 추출
    반환: (candidates, label_found_but_no_value 리스트)
    """
    lines = _iter_lines(normalized_text)
    out: List[Candidate] = []
    label_misses: List[str] = []

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
        # 1) 중량(kg) 라벨 기반
        for field, tokens in weight_label_map:
            token = _match_any_token(line, tokens)
            if not token:
                continue

            near = _extract_weight_near_line(lines, i)
            if near:
                value_raw, src_line = near
                _add_candidate(
                    out,
                    field=field,
                    value_raw=value_raw,
                    source_line=src_line,
                    method="label",
                    score=90,
                    meta={
                        "line_index": i,
                        "label_token": token,
                        "extraction_metadata": _make_extraction_meta(
                            field=field,
                            strategy_used="label_match",
                            raw_match=value_raw,
                            normalized_match=value_raw,
                            source_line_index=i,
                            confidence=0.95,
                            notes="weight_from_label_nearby",
                        ),
                    },
                )
            else:
                # 라벨은 발견됐지만 값 추출 실패
                label_misses.append(f"{field}@line:{i}")

        # 2) 날짜/시간 라벨 기반 (같은 줄 or 다음 줄)
        for field, tokens, pattern in dt_label_map:
            token = _match_any_token(line, tokens)
            if not token:
                continue

            targets = [(line, i)]
            if i + 1 < len(lines):
                targets.append((lines[i + 1], i + 1))

            found = False
            for tgt_line, tgt_idx in targets:
                m = _first_match(pattern, tgt_line)
                if m:
                    value_raw = m.group(0)
                    _add_candidate(
                        out,
                        field=field,
                        value_raw=value_raw,
                        source_line=tgt_line,
                        method="label",
                        score=85,
                        meta={
                            "line_index": tgt_idx,
                            "label_token": token,
                            "extraction_metadata": _make_extraction_meta(
                                field=field,
                                strategy_used="label_match",
                                raw_match=value_raw,
                                normalized_match=value_raw,
                                source_line_index=tgt_idx,
                                confidence=0.9,
                                notes="dt_from_label",
                            ),
                        },
                    )
                    found = True
                    break

            if not found:
                label_misses.append(f"{field}@line:{i}")

        # 3) 차량번호 라벨 기반
        v_token = _match_any_token(line, vehicle_tokens)
        if v_token:
            # 1) 같은 줄에서 전형 패턴
            m = _first_match(VEHICLE_NO_PATTERN, line)
            if m:
                value_raw = m.group(0)
                _add_candidate(
                    out,
                    field="vehicle_no",
                    value_raw=value_raw,
                    source_line=line,
                    method="label",
                    score=85,
                    meta={
                        "line_index": i,
                        "label_token": v_token,
                        "extraction_metadata": _make_extraction_meta(
                            field="vehicle_no",
                            strategy_used="label_match",
                            raw_match=value_raw,
                            normalized_match=value_raw,
                            source_line_index=i,
                            confidence=0.9,
                            notes="vehicle_from_label_same_line",
                        ),
                    },
                )
            else:
                # 2) 다음 줄
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    m2 = _first_match(VEHICLE_NO_PATTERN, next_line)
                    if m2:
                        value_raw = m2.group(0)
                        _add_candidate(
                            out,
                            field="vehicle_no",
                            value_raw=value_raw,
                            source_line=next_line,
                            method="label",
                            score=85,
                            meta={
                                "line_index": i + 1,
                                "label_token": v_token,
                                "extraction_metadata": _make_extraction_meta(
                                    field="vehicle_no",
                                    strategy_used="label_match",
                                    raw_match=value_raw,
                                    normalized_match=value_raw,
                                    source_line_index=i + 1,
                                    confidence=0.85,
                                    notes="vehicle_from_label_next_line",
                                ),
                            },
                        )
                    else:
                        # 3) 전형 패턴 실패 → digits-only 후보(낮은 확신)
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
                                    "extraction_metadata": _make_extraction_meta(
                                        field="vehicle_no",
                                        strategy_used="label_match",
                                        raw_match=digits,
                                        normalized_match=digits,
                                        source_line_index=i,
                                        confidence=0.4,
                                        notes="vehicle_digits_fallback_from_label_line",
                                    ),
                                },
                            )
                        else:
                            label_misses.append(f"vehicle_no@line:{i}")

    return out, label_misses


def extract_by_pattern(normalized_text: str) -> List[Candidate]:
    # 패턴 기반 후보 추출 (fallback)

    lines = _iter_lines(normalized_text)
    out: List[Candidate] = []

    for i, line in enumerate(lines):
        # 날짜
        for m in _all_matches(DATE_PATTERN, line):
            value_raw = m.group(0)
            _add_candidate(
                out,
                field="date",
                value_raw=value_raw,
                source_line=line,
                method="pattern",
                score=50,
                meta={
                    "line_index": i,
                    "extraction_metadata": _make_extraction_meta(
                        field="date",
                        strategy_used="pattern_fallback",
                        raw_match=value_raw,
                        normalized_match=value_raw,
                        source_line_index=i,
                        confidence=0.6,
                        notes="date_from_pattern",
                    ),
                },
            )

        # 시간
        for m in _all_matches(TIME_PATTERN, line):
            value_raw = m.group(0)
            _add_candidate(
                out,
                field="time",
                value_raw=value_raw,
                source_line=line,
                method="pattern",
                score=50,
                meta={
                    "line_index": i,
                    "extraction_metadata": _make_extraction_meta(
                        field="time",
                        strategy_used="pattern_fallback",
                        raw_match=value_raw,
                        normalized_match=value_raw,
                        source_line_index=i,
                        confidence=0.6,
                        notes="time_from_pattern",
                    ),
                },
            )

        # 중량(kg)
        for m in _all_matches(WEIGHT_KG_PATTERN, line):
            value_raw = m.group(0)
            _add_candidate(
                out,
                field="weight_kg",
                value_raw=value_raw,
                source_line=line,
                method="pattern",
                score=45,
                meta={
                    "line_index": i,
                    "extraction_metadata": _make_extraction_meta(
                        field="weight_kg",
                        strategy_used="pattern_fallback",
                        raw_match=value_raw,
                        normalized_match=value_raw,
                        source_line_index=i,
                        confidence=0.5,
                        notes="weight_from_pattern",
                    ),
                },
            )

        # 차량번호
        for m in _all_matches(VEHICLE_NO_PATTERN, line):
            value_raw = m.group(0)
            _add_candidate(
                out,
                field="vehicle_no",
                value_raw=value_raw,
                source_line=line,
                method="pattern",
                score=45,
                meta={
                    "line_index": i,
                    "extraction_metadata": _make_extraction_meta(
                        field="vehicle_no",
                        strategy_used="pattern_fallback",
                        raw_match=value_raw,
                        normalized_match=value_raw,
                        source_line_index=i,
                        confidence=0.5,
                        notes="vehicle_from_pattern",
                    ),
                },
            )

        # 차량번호(단순 4자리) - 낮은 score
        for m in _all_matches(VEHICLE_NO_SIMPLE, line):
            value_raw = m.group(0)
            _add_candidate(
                out,
                field="vehicle_no",
                value_raw=value_raw,
                source_line=line,
                method="pattern",
                score=20,
                meta={
                    "line_index": i,
                    "note": "vehicle_simple_4digits",
                    "extraction_metadata": _make_extraction_meta(
                        field="vehicle_no",
                        strategy_used="pattern_fallback",
                        raw_match=value_raw,
                        normalized_match=value_raw,
                        source_line_index=i,
                        confidence=0.2,
                        notes="vehicle_simple_4digits",
                    ),
                },
            )

    return out


def extract_candidates(preprocessed: PreprocessedDocument) -> ExtractedCandidates:
    label_candidates, label_misses = extract_by_label(preprocessed.normalized_text)
    pattern_candidates = extract_by_pattern(preprocessed.normalized_text)

    candidates = _dedupe_candidates(label_candidates + pattern_candidates)

    warnings: List[str] = []

    # 라벨은 발견됐는데 값이 없었던 경우도 경고로 남김
    if label_misses:
        for miss in label_misses[:10]:
            warnings.append(f"label_found_but_no_value:{miss}")
        if len(label_misses) > 10:
            warnings.append(f"label_found_but_no_value:...+{len(label_misses) - 10}")

    # 주요 필드 존재 여부
    if not any(c.field == "date" for c in candidates):
        warnings.append("Extractor:no_date_candidates")
    if not any(c.field == "time" for c in candidates):
        warnings.append("Extractor:no_time_candidates")
    if not any(c.field == "vehicle_no" for c in candidates):
        warnings.append("Extractor:no_vehicle_no_candidates")
    if not any(c.field.endswith("_weight_kg") or c.field == "weight_kg" for c in candidates):
        warnings.append("Extractor:no_weight_candidates")

    return ExtractedCandidates(
        raw_text=preprocessed.raw_text,
        normalized_text=preprocessed.normalized_text,
        candidates=candidates,
        warnings=warnings,
    )
