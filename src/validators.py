from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class ValidationResult:
    # 검증 결과 및 복구된 값
    is_valid: bool
    net_weight_kg: Optional[int] = None
    validation_errors: List[str] = field(default_factory=list)
    imputation_notes: List[str] = field(default_factory=list)

def _tolerance(expected: int) -> int:
    # 오차 허용 범위: +,-10kg 또는 +,-2% 중 큰 값
    # expected=0인 경우에도 최소 10kg 허용
    return max(10, int(expected * 0.02))

def _relation_ok(gross: int, tare: int, net: int) -> Tuple[bool, int, int, int]:
    # gross, tare, net 사이의 관계가 허용 오차 내에 있는지 검사
    expected = gross - tare
    diff = abs(net - expected)
    tol = _tolerance(expected)
    return (diff <= tol, expected, diff, tol)

def _unique_ints(values: list[int]) -> list[int]:
    seen = set()
    out: list[int] = []
    for v in values:
        if v in seen:
            continue
        seen.add(v)
        out.append(v)
    return out

def _try_recover_by_candidates(
    gross: Optional[int],
    tare: Optional[int],
    net: Optional[int],
    weight_candidates_kg: List[int],
) -> Tuple[Optional[int], Optional[int], Optional[int], Optional[str]]:
    """
    후보 풀을 이용해 (gross, tare, net) 재조합을 시도

    우선순위:
    1. gross,tare 고정 → net 후보로 맞추기
    2. gross,net 고정 → tare 후보로 맞추기
    3. tare,net 고정 → gross 후보로 맞추기
    4. gross 고정 → (tare,net) 후보 쌍으로 맞추기
    5. net 고정   → (gross,tare) 후보 쌍으로 맞추기
    6. tare 고정  → (gross,net) 후보 쌍으로 맞추기
    """
    if not weight_candidates_kg:
        return gross, tare, net, None

    cand = _unique_ints([v for v in weight_candidates_kg if v is not None])

    # 1) gross,tare 고정 → net 찾기
    if gross is not None and tare is not None:
        best = None 
        expected = gross - tare
        tol = _tolerance(expected)
        for n in cand:
            diff = abs(n - expected)
            if diff <= tol:
                if best is None or diff < best[0]:
                    best = (diff, n)
        if best is not None:
            return gross, tare, best[1], (
                f"recovered:net={best[1]} (from weight_candidates, "
                f"expected={expected}, diff={best[0]}, tol={tol})"
            )

    # 2) gross,net 고정 → tare 찾기
    if gross is not None and net is not None:
        best = None  
        expected_tare = gross - net
        tol = _tolerance(net)  
        for t in cand:
            diff = abs(t - expected_tare)
            if diff <= tol:
                if best is None or diff < best[0]:
                    best = (diff, t)
        if best is not None and gross >= best[1]:
            new_tare = best[1]
            ok, _, _, _ = _relation_ok(gross, new_tare, net)
            if ok:
                return gross, new_tare, net, (
                    f"recovered:tare={new_tare} (from weight_candidates, "
                    f"expected_tare={expected_tare}, diff={best[0]})"
                )

    # 3) tare,net 고정 → gross 찾기
    if tare is not None and net is not None:
        best = None 
        expected_gross = tare + net
        tol = _tolerance(net)
        for g in cand:
            diff = abs(g - expected_gross)
            if diff <= tol:
                if best is None or diff < best[0]:
                    best = (diff, g)
        if best is not None and best[1] >= tare:
            new_gross = best[1]
            ok, _, _, _ = _relation_ok(new_gross, tare, net)
            if ok:
                return new_gross, tare, net, (
                    f"recovered:gross={new_gross} (from weight_candidates, "
                    f"expected_gross={expected_gross}, diff={best[0]})"
                )

    # 4) gross 고정 → (tare, net) 쌍으로 맞추기
    if gross is not None:
        best = None 
        for t in cand:
            if gross < t:
                continue
            expected_net = gross - t
            tol = _tolerance(expected_net)
            for n in cand:
                diff = abs(n - expected_net)
                if diff <= tol:
                    if best is None or diff < best[0]:
                        best = (diff, t, n)
        if best is not None:
            return gross, best[1], best[2], (
                f"recovered:tare={best[1]},net={best[2]} (pair_search, diff={best[0]})"
            )

    # 5) net 고정 → (gross, tare) 쌍으로 맞추기
    if net is not None:
        best = None 
        for g in cand:
            for t in cand:
                if g < t:
                    continue
                ok, _, diff, _ = _relation_ok(g, t, net)
                if ok:
                    if best is None or diff < best[0]:
                        best = (diff, g, t)
        if best is not None:
            return best[1], best[2], net, (
                f"recovered:gross={best[1]},tare={best[2]} (pair_search, diff={best[0]})"
            )

    # 6) tare 고정 → (gross, net) 쌍으로 맞추기
    if tare is not None:
        best = None 
        for g in cand:
            if g < tare:
                continue
            expected_net = g - tare
            tol = _tolerance(expected_net)
            for n in cand:
                diff = abs(n - expected_net)
                if diff <= tol:
                    if best is None or diff < best[0]:
                        best = (diff, g, n)
        if best is not None:
            return best[1], tare, best[2], (
                f"recovered:gross={best[1]},net={best[2]} (pair_search, diff={best[0]})"
            )

    return gross, tare, net, None

def validate_and_recover(
    date: Optional[str],
    time: Optional[str],
    vehicle_no: Optional[str],
    gross_weight_kg: Optional[int],
    tare_weight_kg: Optional[int],
    net_weight_kg: Optional[int],
    weight_candidates_kg: Optional[List[int]] = None,
) -> ValidationResult:
    """
    도메인 검증 및 실중량 복구
    
    검증 규칙:
    1. 필수 필드 존재 여부 (date, vehicle_no)
    2. gross_weight_kg >= tare_weight_kg
    3. net_weight_kg ≈ gross_weight_kg - tare_weight_kg (있을 경우)
    
    복구 정책:
    - net_weight_kg 누락 + gross/tare 존재 시 계산으로 생성
    - 생성 시 imputation_notes에 기록
    - gross/tare/net 중복 누락 시 weight_candidates_kg 이용해 재조합 시도
    
    반환:
    - is_valid: 치명적 오류가 없으면 True
    - net_weight_kg: 원본 또는 복구된 값
    - validation_errors: 검증 실패 항목
    - imputation_notes: 복구/계산 이력
    """
    errors: List[str] = []
    notes: List[str] = []
    final_gross = gross_weight_kg
    final_tare = tare_weight_kg
    final_net = net_weight_kg
    
    # 1. 필수 필드 검증
    if not date:
        errors.append("missing_required_field:date")
    
    if not vehicle_no:
        errors.append("missing_required_field:vehicle_no")
    
    # 2. 중량 관계 검증
    if final_gross is not None and final_gross < 0:
        errors.append(f"negative_weight:gross={final_gross}")
    if final_tare is not None and final_tare < 0:
        errors.append(f"negative_weight:tare={final_tare}")
    if final_net is not None and final_net < 0:
        errors.append(f"negative_weight:net={final_net}")

    if final_gross is not None and final_gross > 100000:
        errors.append(f"unrealistic_weight:gross={final_gross}")
    
    # 3. 중량이 음수인지 검증
    if final_gross is not None and final_tare is not None:
        if final_gross < final_tare:
            errors.append(
                f"invalid_weight_relation:gross({final_gross}) < tare({final_tare})"
            )

        # 3-A) net 누락이면 계산으로 채움
        if final_net is None:
            calculated = final_gross - final_tare
            final_net = calculated
            notes.append(
                f"imputed:net_weight={calculated} (gross={final_gross} - tare={final_tare})"
            )
        else:
            ok, expected, diff, tol = _relation_ok(final_gross, final_tare, final_net)
            if not ok:
                errors.append(
                    f"weight_mismatch:net({final_net}) != gross({final_gross}) - tare({final_tare}) "
                    f"[expected={expected}, diff={diff}, tolerance={tol}]"
                )
    
    has_mismatch = any(e.startswith("weight_mismatch:") for e in errors)
    if has_mismatch and weight_candidates_kg:
        new_g, new_t, new_n, note = _try_recover_by_candidates(
            gross=final_gross,
            tare=final_tare,
            net=final_net,
            weight_candidates_kg=weight_candidates_kg,
        )

        # recovery가 실제로 성립하면 반영
        if note is not None:
            final_gross, final_tare, final_net = new_g, new_t, new_n
            notes.append(note)

            # weight_mismatch 에러 제거 후, 새 조합으로 재검증
            errors = [e for e in errors if not e.startswith("weight_mismatch:")]

            if final_gross is not None and final_tare is not None and final_net is not None:
                if final_gross < final_tare:
                    errors.append(
                        f"invalid_weight_relation:gross({final_gross}) < tare({final_tare})"
                    )
                else:
                    ok, expected, diff, tol = _relation_ok(final_gross, final_tare, final_net)
                    if not ok:
                        errors.append(
                            f"weight_mismatch:net({final_net}) != gross({final_gross}) - tare({final_tare}) "
                            f"[expected={expected}, diff={diff}, tolerance={tol}]"
                        )

    is_valid = (len(errors) == 0)

    return ValidationResult(
        is_valid=is_valid,
        net_weight_kg=final_net,
        validation_errors=errors,
        imputation_notes=notes,
    )