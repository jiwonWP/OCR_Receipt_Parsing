from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict

# 전처리 단계 출력 스키마
class PreprocessLogSchema(TypedDict):
    source: str
    applied_rules: List[str]
    warnings: List[str]
    raw_line_count: int
    normalized_line_count: int


# Extraction 단계 출력 스키마
class CandidateSchema(TypedDict):
    field: str
    value_raw: str
    value_normalized: Optional[Any]
    method: str
    score: int
    confidence: str
    source_line: str
    meta: Dict[str, Any]


class CandidateSummarySchema(TypedDict):
    """후보 요약 통계 스키마"""
    total: int
    by_field: Dict[str, int]
    by_method: Dict[str, int]


class ExtractLogSchema(TypedDict):
    """추출 로그 스키마"""
    source: str
    warnings: List[str]
    candidate_summary: Dict[str, Any]


class CandidatesOutputSchema(TypedDict):
    """후보 출력 파일 스키마"""
    source: str
    candidates: List[CandidateSchema]


# Resolve 단계 출력 스키마
class ResolvedFieldsSchema(TypedDict):
    date_raw: Optional[str]
    time_raw: Optional[str]
    vehicle_no_raw: Optional[str]
    gross_weight_raw: Optional[str]
    tare_weight_raw: Optional[str]
    net_weight_raw: Optional[str]


class EvidenceSchema(TypedDict):
    """증거 정보 스키마"""
    field: str
    selected_value: str
    selected_method: str
    selected_score: int
    runner_up_value: Optional[str]
    runner_up_score: Optional[int]
    score_gap: Optional[int]


class ResolvedOutputSchema(TypedDict):
    """후보 선택 출력 파일 스키마"""
    source: str
    resolved_fields: ResolvedFieldsSchema
    evidence: Dict[str, EvidenceSchema]
    warnings: List[str]


# Parse/Validate 단계 출력 스키마
class ParsedOutputSchema(TypedDict):
    source: str
    date: Optional[str]
    time: Optional[str]
    vehicle_no: Optional[str]
    gross_weight_kg: Optional[int]
    tare_weight_kg: Optional[int]
    net_weight_kg: Optional[int]
    parse_warnings: List[str]
    validation_errors: List[str]
    imputation_notes: List[str]
    is_valid: bool



# CSV 출력 스키마
class CSVRowSchema(TypedDict):
    filename: str
    date: str
    time: str
    vehicle_no: str
    gross_weight_kg: str
    tare_weight_kg: str
    net_weight_kg: str
    is_valid: str
    validation_errors: str
    parse_warnings: str
    imputation_notes: str



# 스키마 검증 함수
def validate_preprocess_log(data: dict) -> bool:
    """전처리 로그 스키마 검증"""
    required_keys = {"source", "applied_rules", "warnings", "raw_line_count", "normalized_line_count"}
    return all(k in data for k in required_keys)


def validate_candidates_output(data: dict) -> bool:
    """후보 출력 스키마 검증"""
    if "source" not in data or "candidates" not in data:
        return False
    
    # 각 후보 검증
    for candidate in data.get("candidates", []):
        required = {"field", "value_raw", "method", "score", "source_line"}
        if not all(k in candidate for k in required):
            return False
    
    return True


def validate_resolved_output(data: dict) -> bool:
    """후보 선택 출력 스키마 검증"""
    required_keys = {"source", "resolved_fields", "evidence", "warnings"}
    return all(k in data for k in required_keys)


def validate_parsed_output(data: dict) -> bool:
    """파싱 결과 출력 스키마 검증"""
    required_keys = {
        "source", "date", "time", "vehicle_no",
        "gross_weight_kg", "tare_weight_kg", "net_weight_kg",
        "parse_warnings", "validation_errors", "imputation_notes", "is_valid"
    }
    return all(k in data for k in required_keys)



# 스키마 템플릿 (빈 데이터)
def get_empty_preprocess_log(source: str) -> PreprocessLogSchema:
    """빈 전처리 로그 템플릿"""
    return {
        "source": source,
        "applied_rules": [],
        "warnings": [],
        "raw_line_count": 0,
        "normalized_line_count": 0,
    }


def get_empty_extract_log(source: str) -> ExtractLogSchema:
    """빈 추출 로그 템플릿"""
    return {
        "source": source,
        "warnings": [],
        "candidate_summary": {
            "total": 0,
            "by_field": {},
            "by_method": {},
        }
    }


def get_empty_resolved_output(source: str) -> ResolvedOutputSchema:
    """빈 후보 선택 출력 템플릿"""
    return {
        "source": source,
        "resolved_fields": {
            "date_raw": None,
            "time_raw": None,
            "vehicle_no_raw": None,
            "gross_weight_raw": None,
            "tare_weight_raw": None,
            "net_weight_raw": None,
        },
        "evidence": {},
        "warnings": [],
    }


def get_empty_parsed_output(source: str) -> ParsedOutputSchema:
    """빈 파싱 결과 출력 템플릿"""
    return {
        "source": source,
        "date": None,
        "time": None,
        "vehicle_no": None,
        "gross_weight_kg": None,
        "tare_weight_kg": None,
        "net_weight_kg": None,
        "parse_warnings": [],
        "validation_errors": [],
        "imputation_notes": [],
        "is_valid": False,
    }