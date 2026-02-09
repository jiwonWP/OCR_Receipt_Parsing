from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, List

from .schemas import (
    PreprocessLogSchema,
    ExtractLogSchema,
    CandidatesOutputSchema,
    ResolvedOutputSchema,
    ParsedOutputSchema,
    CSVRowSchema,
)


# 파일명 규칙
class FileNamingConvention:
    """파일명 규칙"""
    
    @staticmethod
    def preprocess_raw(stem: str) -> str:
        """원문 텍스트 파일명"""
        return f"{stem}_raw.txt"
    
    @staticmethod
    def preprocess_normalized(stem: str) -> str:
        """정규화 텍스트 파일명"""
        return f"{stem}_normalized.txt"
    
    @staticmethod
    def preprocess_log(stem: str) -> str:
        """전처리 로그 파일명"""
        return f"{stem}_preprocess_log.json"
    
    @staticmethod
    def extract_candidates(stem: str) -> str:
        """후보 목록 파일명"""
        return f"{stem}_candidates.json"
    
    @staticmethod
    def extract_log(stem: str) -> str:
        """추출 로그 파일명"""
        return f"{stem}_extract_log.json"
    
    @staticmethod
    def resolve_result(stem: str) -> str:
        """후보 선택 결과 파일명"""
        return f"{stem}_resolved.json"
    
    @staticmethod
    def parse_result(stem: str) -> str:
        """최종 파싱 결과 파일명"""
        return f"{stem}_parsed.json"
    
    @staticmethod
    def summary_csv() -> str:
        """전체 요약 CSV 파일명"""
        return "summary.csv"


# 포맷터 함수
def format_preprocess_log(
    source: str,
    applied_rules: List[str],
    warnings: List[str],
    raw_line_count: int,
    normalized_line_count: int
) -> PreprocessLogSchema:
    """전처리 로그 포맷"""
    return {
        "source": source,
        "applied_rules": applied_rules,
        "warnings": warnings,
        "raw_line_count": raw_line_count,
        "normalized_line_count": normalized_line_count,
    }


def format_extract_log(
    source: str,
    warnings: List[str],
    candidate_summary: Dict[str, Any]
) -> ExtractLogSchema:
    """추출 로그 포맷"""
    return {
        "source": source,
        "warnings": warnings,
        "candidate_summary": candidate_summary,
    }


def format_candidates_output(
    source: str,
    candidates: List[Dict[str, Any]]
) -> CandidatesOutputSchema:
    """후보 목록 출력 포맷"""
    return {
        "source": source,
        "candidates": candidates,
    }


def format_resolved_output(
    source: str,
    resolved_fields: Dict[str, Any],
    evidence: Dict[str, Any],
    warnings: List[str]
) -> ResolvedOutputSchema:
    """후보 선택 결과 포맷"""
    return {
        "source": source,
        "resolved_fields": resolved_fields,
        "evidence": evidence,
        "warnings": warnings,
    }


def format_parsed_output(
    source: str,
    date: Any,
    time: Any,
    vehicle_no: Any,
    gross_weight_kg: Any,
    tare_weight_kg: Any,
    net_weight_kg: Any,
    parse_warnings: List[str],
    validation_errors: List[str],
    imputation_notes: List[str],
    is_valid: bool
) -> ParsedOutputSchema:
    """최종 파싱 결과 포맷"""
    return {
        "source": source,
        "date": date,
        "time": time,
        "vehicle_no": vehicle_no,
        "gross_weight_kg": gross_weight_kg,
        "tare_weight_kg": tare_weight_kg,
        "net_weight_kg": net_weight_kg,
        "parse_warnings": parse_warnings,
        "validation_errors": validation_errors,
        "imputation_notes": imputation_notes,
        "is_valid": is_valid,
    }


# CSV 변환
def format_csv_row(
    filename: str,
    parsed_data: ParsedOutputSchema
) -> CSVRowSchema:
    """파싱 결과를 CSV 행으로 변환"""
    
    def safe_str(value: Any) -> str:
        """None-safe 문자열 변환"""
        return str(value) if value is not None else ""
    
    def join_list(items: List[str]) -> str:
        """리스트를 세미콜론으로 연결"""
        return "; ".join(items) if items else ""
    
    return {
        "filename": filename,
        "date": safe_str(parsed_data["date"]),
        "time": safe_str(parsed_data["time"]),
        "vehicle_no": safe_str(parsed_data["vehicle_no"]),
        "gross_weight_kg": safe_str(parsed_data["gross_weight_kg"]),
        "tare_weight_kg": safe_str(parsed_data["tare_weight_kg"]),
        "net_weight_kg": safe_str(parsed_data["net_weight_kg"]),
        "is_valid": "TRUE" if parsed_data["is_valid"] else "FALSE",
        "validation_errors": join_list(parsed_data["validation_errors"]),
        "parse_warnings": join_list(parsed_data["parse_warnings"]),
        "imputation_notes": join_list(parsed_data["imputation_notes"]),
    }


def write_summary_csv(
    output_path: Path,
    rows: List[CSVRowSchema]
) -> None:
    if not rows:
        return
    
    fieldnames = [
        "filename",
        "date",
        "time",
        "vehicle_no",
        "gross_weight_kg",
        "tare_weight_kg",
        "net_weight_kg",
        "is_valid",
        "validation_errors",
        "parse_warnings",
        "imputation_notes",
    ]
    
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


# 전체 산출물 목록 함수
def get_output_files(stem: str) -> List[str]:
    return [
        FileNamingConvention.preprocess_raw(stem),
        FileNamingConvention.preprocess_normalized(stem),
        FileNamingConvention.preprocess_log(stem),
        FileNamingConvention.extract_candidates(stem),
        FileNamingConvention.extract_log(stem),
        FileNamingConvention.resolve_result(stem),
        FileNamingConvention.parse_result(stem),
    ]