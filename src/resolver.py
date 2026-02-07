from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from collections import defaultdict

from .schema import Candidate


@dataclass
class ResolvedFields:
    # 후보들 중 최종 선택된 필드 값들
    date_raw: Optional[str] = None
    time_raw: Optional[str] = None
    vehicle_no_raw: Optional[str] = None
    gross_weight_raw: Optional[str] = None
    tare_weight_raw: Optional[str] = None
    net_weight_raw: Optional[str] = None
    evidence: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)


def _pick_best(items: List[Candidate]) -> Optional[Candidate]:
    """
    선택 정책:
    1. method == "label" 우선
    2. score 내림차순
    3. meta.line_index 오름차순 (없으면 아주 큰 값 취급)
    """
    if not items:
        return None

    def key(c: Candidate):
        # 1순위: 방법 (label > pattern)
        method_rank = 0 if c.method == "label" else 1
        
        # 2순위: 점수
        # 단, 라벨 토큰이 source_line에 실제로 들어있는 경우(같은 줄 추출) 가산점 +15
        score = c.score
        if c.method == "label" and c.meta.get("label_token"):
            if c.meta.get("label_token") in c.source_line:
                score += 15
            
        return (method_rank, -score, c.meta.get("line_index", 10**9))

    return sorted(items, key=key)[0]


def resolve_candidates(candidates: List[Candidate]) -> ResolvedFields:
    """
    ExtractedCandidates.candidates를 입력으로 받아
    필드별 최적 후보를 1개씩 선택
    """
    warnings: List[str] = []
    evidence: Dict[str, Any] = {}

    # 필드별로 후보 그룹화
    by_field: Dict[str, List[Candidate]] = defaultdict(list)
    for c in candidates:
        by_field[c.field].append(c)

    # 각 필드별로 최적 후보 선택
    def resolve_one(field_name: str) -> Optional[str]:
        items = by_field.get(field_name, [])
        if not items:
            return None

        best = _pick_best(items)
        if best is None:
            return None

        # top2가 동점이면 애매함 경고
        if len(items) >= 2:
            sorted_items = sorted(items, key=lambda x: (
                0 if x.method == "label" else 1,
                -x.score,
                x.meta.get("line_index", 10**9),
            ))
            a, b = sorted_items[0], sorted_items[1]
            if a.method == b.method and a.score == b.score:
                warnings.append(f"ambiguous_candidate:{field_name}")

        evidence[field_name] = {
            "selected_value": best.value_raw,
            "selected_method": best.method,
            "selected_score": best.score,
            "selected_source_line": best.source_line,
            "candidate_count": len(items),
        }
        return best.value_raw
    
    date_raw = resolve_one("date")
    time_raw = resolve_one("time")
    vehicle_no_raw = resolve_one("vehicle_no")

    gross_raw = resolve_one("gross_weight_kg")
    tare_raw = resolve_one("tare_weight_kg")
    net_raw = resolve_one("net_weight_kg")

    # 역할이 확정되지 않은 weight_kg 후보는 확정하지 않고 근거로만 남김
    misc_weights = by_field.get("weight_kg", [])
    if misc_weights:
        evidence["weight_kg_candidates"] = {
            "candidates": [
                {
                    "value_raw": c.value_raw,
                    "method": c.method,
                    "score": c.score,
                    "source_line": c.source_line,
                }
                for c in misc_weights
            ],
            "candidate_count": len(misc_weights),
        }
        warnings.append("unassigned_weight_candidates_present")

    return ResolvedFields(
        date_raw=date_raw,
        time_raw=time_raw,
        vehicle_no_raw=vehicle_no_raw,
        gross_weight_raw=gross_raw,
        tare_weight_raw=tare_raw,
        net_weight_raw=net_raw,
        evidence=evidence,
        warnings=warnings,
    )