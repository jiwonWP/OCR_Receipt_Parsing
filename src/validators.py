from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ValidationResult:
    # 검증 결과 및 복구된 값
    is_valid: bool
    net_weight_kg: Optional[int] = None
    validation_errors: List[str] = field(default_factory=list)
    imputation_notes: List[str] = field(default_factory=list)


def validate_and_recover(
    date: Optional[str],
    time: Optional[str],
    vehicle_no: Optional[str],
    gross_weight_kg: Optional[int],
    tare_weight_kg: Optional[int],
    net_weight_kg: Optional[int],
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
    
    반환:
    - is_valid: 치명적 오류가 없으면 True
    - net_weight_kg: 원본 또는 복구된 값
    - validation_errors: 검증 실패 항목
    - imputation_notes: 복구/계산 이력
    """
    errors: List[str] = []
    notes: List[str] = []
    final_net_kg = net_weight_kg
    
    # 1. 필수 필드 검증
    if not date:
        errors.append("missing_required_field:date")
    
    if not vehicle_no:
        errors.append("missing_required_field:vehicle_no")
    
    # 2. 중량 관계 검증
    if gross_weight_kg is not None and tare_weight_kg is not None:
        # 2-1. gross >= tare 검증
        if gross_weight_kg < tare_weight_kg:
            errors.append(
                f"invalid_weight_relation:gross({gross_weight_kg}) < tare({tare_weight_kg})"
            )
        
        # 2-2. net_weight 복구 시도
        if net_weight_kg is None:
            # 복구: net = gross - tare
            calculated = gross_weight_kg - tare_weight_kg
            final_net_kg = calculated
            notes.append(
                f"imputed:net_weight={calculated} (gross={gross_weight_kg} - tare={tare_weight_kg})"
            )
        else:
            # 2-3. 기존 net_weight가 있으면 정합성 검증
            expected = gross_weight_kg - tare_weight_kg
            diff = abs(net_weight_kg - expected)
            
            # 오차 허용 범위: +,-10kg 또는 +,-2% 중 큰 값
            tolerance = max(10, int(expected * 0.02))
            
            if diff > tolerance:
                errors.append(
                    f"weight_mismatch:net({net_weight_kg}) != gross({gross_weight_kg}) - tare({tare_weight_kg}) "
                    f"[expected={expected}, diff={diff}, tolerance={tolerance}]"
                )
    
    # 3. 중량이 음수인지 검증
    if gross_weight_kg is not None and gross_weight_kg < 0:
        errors.append(f"negative_weight:gross={gross_weight_kg}")
    
    if tare_weight_kg is not None and tare_weight_kg < 0:
        errors.append(f"negative_weight:tare={tare_weight_kg}")
    
    if final_net_kg is not None and final_net_kg < 0:
        errors.append(f"negative_weight:net={final_net_kg}")
    
    # 4. 중량이 비현실적으로 큰지 검증
    if gross_weight_kg is not None and gross_weight_kg > 100000:
        errors.append(f"unrealistic_weight:gross={gross_weight_kg}")
    
    # 최종 판정
    is_valid = (len(errors) == 0)
    
    return ValidationResult(
        is_valid=is_valid,
        net_weight_kg=final_net_kg,
        validation_errors=errors,
        imputation_notes=notes,
    )