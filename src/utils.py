from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Dict, List


def format_weight_kg(value: Any) -> str:
    """
    중량 값을 가독성 높은 형식으로 포맷
    예시:
        - format_weight_kg(12340) => '12,340 kg'
        - format_weight_kg(None) => '(없음)'
    """
    if value is None:
        return "(없음)"
    try:
        return f"{int(value):,} kg"
    except (ValueError, TypeError):
        return str(value)

    
# 후보 리스트를 요약 통계로 변환
def summarize_candidates(candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_field: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    method_counter = Counter()
    field_counter = Counter()

    for c in candidates:
        f = c.get("field", "")
        by_field[f].append(c)

        method = c.get("method", "")
        method_counter[method] += 1
        field_counter[f] += 1

    top_by_field: Dict[str, List[Dict[str, Any]]] = {}
    for field, items in by_field.items():
        items_sorted = sorted(items, key=lambda x: int(x.get("score", 0)), reverse=True)
        # 상위 3개만
        top_by_field[field] = [
            {
                "value_raw": it.get("value_raw", ""),
                "method": it.get("method", ""),
                "score": it.get("score", 0),
                "source_line": it.get("source_line", ""),
            }
            for it in items_sorted[:3]
        ]

    return {
        "counts": {
            "total": len(candidates),
            "by_field": dict(field_counter),
            "by_method": dict(method_counter),
        },
        "top_by_field": top_by_field,
    }


def compute_weight_relation_summary(
    gross: Any,
    tare: Any,
    net: Any
) -> str:
    """
    중량 관계식 요약 문자열 생성
    반환:
        예: "12,480 - 7,470 = 5,010 [일치]"
        예: "12,480 - 7,470 = 5,000 [불일치 (계산=5,010kg)]"
    """
    if gross is None or tare is None or net is None:
        return "(중량 정보 불완전)"
    
    try:
        gross_int = int(gross)
        tare_int = int(tare)
        net_int = int(net)
        
        calc_net = gross_int - tare_int
        
        if calc_net == net_int:
            match_status = "일치"
        else:
            match_status = f"불일치 (계산={calc_net:,}kg)"
        
        return f"{gross_int:,} - {tare_int:,} = {net_int:,} [{match_status}]"
    
    except (ValueError, TypeError):
        return "(중량 계산 실패)"

# 전체 처리 단계 요약 생성
def build_processing_summary(
    preprocessed_dict: Dict[str, Any],
    extracted_dict: Dict[str, Any],
    resolved_dict: Dict[str, Any],
    parsed_dict: Dict[str, Any],
    candidate_summary: Dict[str, Any]
) -> Dict[str, Any]:

    validation_errors = parsed_dict.get("validation_errors", []) or []
    is_valid = (len(validation_errors) == 0)
    
    return {
        "is_valid": is_valid,
        "validation_errors": validation_errors,
        
        "preprocess": {
            "applied_rules_count": len(preprocessed_dict.get("applied_rules", [])),
            "applied_rules": preprocessed_dict.get("applied_rules", []),
            "warnings_count": len(preprocessed_dict.get("warnings", [])),
            "warnings": preprocessed_dict.get("warnings", []),
        },
        
        "extract": {
            "total_candidates": candidate_summary["counts"]["total"],
            "by_field": candidate_summary["counts"]["by_field"],
            "by_method": candidate_summary["counts"]["by_method"],
            "warnings_count": len(extracted_dict.get("warnings", [])),
        },
        
        "resolve": {
            "date_raw": resolved_dict.get("date_raw"),
            "time_raw": resolved_dict.get("time_raw"),
            "vehicle_no_raw": resolved_dict.get("vehicle_no_raw"),
            "gross_weight_raw": resolved_dict.get("gross_weight_raw"),
            "tare_weight_raw": resolved_dict.get("tare_weight_raw"),
            "net_weight_raw": resolved_dict.get("net_weight_raw"),
            "warnings_count": len(resolved_dict.get("warnings", [])),
            "warnings": resolved_dict.get("warnings", []),
        },
        
        "normalize": {
            "date": parsed_dict.get("date"),
            "time": parsed_dict.get("time"),
            "vehicle_no": parsed_dict.get("vehicle_no"),
            "gross_weight_kg": parsed_dict.get("gross_weight_kg"),
            "tare_weight_kg": parsed_dict.get("tare_weight_kg"),
            "net_weight_kg": parsed_dict.get("net_weight_kg"),
            "parse_warnings_count": len(parsed_dict.get("parse_warnings", [])),
            "parse_warnings": parsed_dict.get("parse_warnings", []),
        },
    }

# 요약 정보를 콘솔 출력 형식으로 포맷팅
def format_console_output(
    filename: str,
    summary: Dict[str, Any] # build_processing_summary()의 결과
) -> str:

    lines = []
    
    is_valid = summary["is_valid"]
    status_symbol = "✓" if is_valid else "✗"
    status_text = "VALID" if is_valid else "INVALID"
    
    lines.append(f"\n{'='*60}")
    lines.append(f"파일: {filename} [{status_symbol} {status_text}]")
    lines.append(f"{'='*60}")
    
    # 1. 전처리
    preprocess = summary["preprocess"]
    lines.append(f"\n[1] 전처리 단계")
    lines.append(f"  - 적용 규칙: {preprocess['applied_rules_count']}개")
    if preprocess["applied_rules"]:
        head = preprocess["applied_rules"][:5]
        lines.append(f"    · {', '.join(head)}")
        if preprocess["applied_rules_count"] > 5:
            lines.append(f"    · ... 외 {preprocess['applied_rules_count'] - 5}개")
    lines.append(f"  - 경고: {preprocess['warnings_count']}개")
    if preprocess["warnings"]:
        for w in preprocess["warnings"][:3]:
            lines.append(f"    · {w}")
    
    # 2. 추출
    extract = summary["extract"]
    lines.append(f"\n[2] 추출 단계")
    lines.append(f"  - 후보 총개수: {extract['total_candidates']}")
    lines.append(f"  - 필드별 후보: {extract['by_field']}")
    lines.append(f"  - 방법별 후보: {extract['by_method']}")
    lines.append(f"  - 추출 경고: {extract['warnings_count']}개")
    
    # 3. 후보 선택
    resolve = summary["resolve"]
    lines.append(f"\n[3] 후보 선택 단계")
    lines.append(f"  - 선택된 필드:")
    for field_name in ["date_raw", "time_raw", "vehicle_no_raw", 
                       "gross_weight_raw", "tare_weight_raw", "net_weight_raw"]:
        value = resolve[field_name]
        lines.append(f"    · {field_name:20s}: {value if value else '(없음)'}")
    lines.append(f"  - 선택 경고: {resolve['warnings_count']}개")
    if resolve["warnings"]:
        for w in resolve["warnings"][:3]:
            lines.append(f"    · {w}")
    
    # 4. 정규화
    normalize = summary["normalize"]
    lines.append(f"\n[4] 정규화 단계")
    lines.append(f"  - 최종 결과:")
    lines.append(f"    · 날짜:     {normalize['date'] or '(없음)'}")
    lines.append(f"    · 시간:     {normalize['time'] or '(없음)'}")
    lines.append(f"    · 차량번호: {normalize['vehicle_no'] or '(없음)'}")
    lines.append(f"    · 총중량:   {format_weight_kg(normalize['gross_weight_kg'])}")
    lines.append(f"    · 차중량:   {format_weight_kg(normalize['tare_weight_kg'])}")
    lines.append(f"    · 실중량:   {format_weight_kg(normalize['net_weight_kg'])}")
    lines.append(f"  - 정규화 경고: {normalize['parse_warnings_count']}개")
    if normalize["parse_warnings"]:
        for w in normalize["parse_warnings"][:3]:
            lines.append(f"    · {w}")
    
    # 5. 검증
    lines.append(f"\n[5] 검증 단계")
    lines.append(f"  - 검증 결과: {status_text}")
    lines.append(f"  - 검증 오류: {len(summary['validation_errors'])}개")
    if summary["validation_errors"]:
        for e in summary["validation_errors"]:
            lines.append(f"    ✗ {e}")
    
    # 중량 관계 요약
    weight_summary = compute_weight_relation_summary(
        normalize["gross_weight_kg"],
        normalize["tare_weight_kg"],
        normalize["net_weight_kg"]
    )
    if weight_summary != "(중량 정보 불완전)":
        lines.append(f"  - 중량 관계: {weight_summary}")
    
    return "\n".join(lines)