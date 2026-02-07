from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ResolvedFields:
    # 후보들 중 최종 선택된 필드 값들
    date_raw: Optional[str]
    time_raw: Optional[str]
    vehicle_no_raw: Optional[str]
    gross_weight_raw: Optional[str]
    tare_weight_raw: Optional[str]
    net_weight_raw: Optional[str]
    evidence: Dict[str, Any]
    warnings: List[str]


def _pick_best_candidate(field_candidates: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    # 후보들 중 최적 후보 1개 선택
    # 후보 정렬 기준: 1. label 기반 우선, 2. score 내림차순, 3. meta.line_index 오름차순
    if not field_candidates:
        return None

    def sort_key(c: Dict[str, Any]):
        method = c.get("method")
        score = c.get("score", 0.0)
        meta = c.get("meta", {}) or {}
        line_index = meta.get("line_index", 10**9)

        # label 우선, pattern은 뒤
        method_rank = 0 if method == "label" else 1

        # score는 내림차순 => -score
        return (method_rank, -score, line_index)

    return sorted(field_candidates, key=sort_key)[0]


def resolve_candidates(candidates: Dict[str, List[Dict[str, Any]]]) -> ResolvedFields:
    """
    Extractor가 만든 candidates(dict[field] -> list[candidate])에서
    각 필드별 최적 후보를 1개씩 선택
    -> *_raw(선택된 raw 문자열), evidence(선택 근거), warnings(경고) 포함
    """

    warnings: List[str] = []
    evidence: Dict[str, Any] = {}

    # 각 필드별 후보들 중 최적 후보 1개 선택 함수
    def resolve_one(field_key: str, out_key: str) -> Optional[str]:
        field_list = candidates.get(field_key, []) or []
        if not field_list:
            return None

        # 정렬 1등 후보
        best = _pick_best_candidate(field_list)
        if best is None:
            return None

        # 동점/경합 후보 경고 처리
        #   - label 후보가 여러 개인데 score가 같거나 top2 score가 같으면 ambiguous로 기록
        if len(field_list) >= 2:
            top = sorted(field_list, key=lambda c: (
                0 if c.get("method") == "label" else 1,
                -(c.get("score", 0.0)),
                (c.get("meta", {}) or {}).get("line_index", 10**9),
            ))
            if (top[0].get("method") == top[1].get("method")
                    and float(top[0].get("score", 0.0)) == float(top[1].get("score", 0.0))):
                warnings.append(f"ambiguous_candidate:{field_key}")

        evidence[out_key] = {
            "selected": best,
            "candidate_count": len(field_list),
        }
        return best.get("value")

    date_raw = resolve_one("date", "date")
    time_raw = resolve_one("time", "time")
    vehicle_no_raw = resolve_one("vehicle_no", "vehicle_no")

    # weights: extractor에서 gross/tare/net 필드 후보가 존재하면 우선 선택
    gross_weight_raw = resolve_one("gross_weight_kg", "gross_weight_kg")
    tare_weight_raw = resolve_one("tare_weight_kg", "tare_weight_kg")
    net_weight_raw = resolve_one("net_weight_kg", "net_weight_kg")

    # fallback weight_kg는 "총/차/실" 확정이 안 되므로 여기서는 '근거만'
    misc_weights = candidates.get("weight_kg", []) or []
    if misc_weights:
        evidence["weight_kg_candidates"] = {
            "candidates": misc_weights,
            "candidate_count": len(misc_weights),
        }
        warnings.append("unassigned_weight_candidates_present")

    return ResolvedFields(
        date_raw=date_raw,
        time_raw=time_raw,
        vehicle_no_raw=vehicle_no_raw,
        gross_weight_raw=gross_weight_raw,
        tare_weight_raw=tare_weight_raw,
        net_weight_raw=net_weight_raw,
        evidence=evidence,
        warnings=warnings,
    )
