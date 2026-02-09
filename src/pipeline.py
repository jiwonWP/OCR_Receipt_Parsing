from __future__ import annotations
from typing import Tuple

from .loader import load_ocr_json
from .preprocessor import preprocess
from .extractor import extract_candidates
from .resolver import resolve_candidates, ResolvedFields
from .normalizers import normalize_date, normalize_time, normalize_weight_kg
from .validators import validate_and_recover
from .schema import PreprocessedDocument, ExtractedCandidates, ParseResult


def run_preprocess_pipeline(input_path: str) -> PreprocessedDocument:
    # Loader -> Preprocessor 파이프라인 실행
    raw_doc = load_ocr_json(input_path)
    preprocessed = preprocess(raw_doc.raw_text)
    return preprocessed

def run_extract_pipeline(input_path: str) -> ExtractedCandidates:
    # Loader -> Preprocessor -> Extractor 파이프라인 실행
    preprocessed = run_preprocess_pipeline(input_path)
    extracted = extract_candidates(preprocessed)
    return extracted

def run_resolve_pipeline(input_path: str) -> Tuple[PreprocessedDocument, ExtractedCandidates, ResolvedFields]:
    # Loader -> Preprocessor -> Extractor -> Resolver 파이프라인 실행
    preprocessed = run_preprocess_pipeline(input_path)
    extracted = extract_candidates(preprocessed)
    resolved = resolve_candidates(extracted.candidates)
    return preprocessed, extracted, resolved

def run_normalize_pipeline(input_path: str) -> Tuple[PreprocessedDocument, ExtractedCandidates, ResolvedFields, ParseResult]:
    # Loader -> Preprocessor -> Extractor -> Resolver -> Normalizers 파이프라인 실행
    preprocessed, extracted, resolved = run_resolve_pipeline(input_path)

    parse_warnings = list(resolved.warnings)

    # date
    date_iso = None
    if resolved.date_raw:
        date_iso, date_warn = normalize_date(resolved.date_raw)
        if date_warn:
            parse_warnings.append(f"date:{date_warn}")
        if date_iso is None:
            if "date_parse_failed" not in parse_warnings:
                parse_warnings.append("date_parse_failed")

    # time
    time_iso = None
    if resolved.time_raw:
        time_iso = normalize_time(resolved.time_raw)
        if time_iso is None:
            parse_warnings.append("time_normalization_failed")

    # weights
    gross_kg = None
    if resolved.gross_weight_raw:
        gross_kg = normalize_weight_kg(resolved.gross_weight_raw)
        if gross_kg is None:
            parse_warnings.append("gross_weight_normalization_failed")

    tare_kg = None
    if resolved.tare_weight_raw:
        tare_kg = normalize_weight_kg(resolved.tare_weight_raw)
        if tare_kg is None:
            parse_warnings.append("tare_weight_normalization_failed")

    net_kg = None
    if resolved.net_weight_raw:
        net_kg = normalize_weight_kg(resolved.net_weight_raw)
        if net_kg is None:
            parse_warnings.append("net_weight_normalization_failed")

    weight_cands = []
    wk = resolved.evidence.get("weight_kg_candidates", {}).get("candidates", [])
    for item in wk:
        raw = item.get("value_raw")
        if raw:
            n = normalize_weight_kg(raw)
            if n is not None:
                weight_cands.append(n)
                
    # Validator 단계: 검증 및 실중량 복구
    v = validate_and_recover(
        date=date_iso,
        time=time_iso,
        vehicle_no=resolved.vehicle_no_raw,
        gross_weight_kg=gross_kg,
        tare_weight_kg=tare_kg,
        net_weight_kg=net_kg,
        weight_candidates_kg=weight_cands,
    )

    final_net = v.net_weight_kg if v.net_weight_kg is not None else net_kg

    result = ParseResult(
        date=date_iso,
        time=time_iso,
        vehicle_no=resolved.vehicle_no_raw,
        gross_weight_kg=gross_kg,
        tare_weight_kg=tare_kg,
        net_weight_kg=final_net,
        parse_warnings=parse_warnings,
        validation_errors=v.validation_errors,
        imputation_notes=v.imputation_notes,
        evidence={
            **resolved.evidence,
            "validation": {
                "is_valid": v.is_valid,
                "imputation_notes": v.imputation_notes,
                "error_count": len(v.validation_errors),
            },
        },
    )

    return preprocessed, extracted, resolved, result


def run_full_pipeline(input_path: str) -> Tuple[PreprocessedDocument, ExtractedCandidates, ResolvedFields, ParseResult]:
    """
    전체 파이프라인 실행: Loader -> Preprocessor -> Extractor -> Resolver -> Normalizer -> Validator
    
    최종 ParseResult에는 검증 및 복구가 완료된 데이터가 포함됨
    """
    return run_normalize_pipeline(input_path)