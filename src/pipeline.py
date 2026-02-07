from __future__ import annotations
from typing import Tuple

from .loader import load_ocr_json
from .preprocessor import preprocess
from .extractor import extract_candidates
from .resolver import resolve_candidates, ResolvedFields
from .normalizers import normalize_date, normalize_time, normalize_weight_kg
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
    """Loader -> Preprocessor -> Extractor -> Resolver -> Normalizers 파이프라인 실행"""
    preprocessed, extracted, resolved = run_resolve_pipeline(input_path)

    parse_warnings = list(resolved.warnings)

    # date
    date_iso = None
    if resolved.date_raw:
        date_iso, date_warn = normalize_date(resolved.date_raw)
        if date_warn:
            parse_warnings.append(f"date:{date_warn}")
        if date_iso is None:
            parse_warnings.append("date_normalization_failed")

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

    result = ParseResult(
        date=date_iso,
        time=time_iso,
        vehicle_no=resolved.vehicle_no_raw,
        gross_weight_kg=gross_kg,
        tare_weight_kg=tare_kg,
        net_weight_kg=net_kg,
        parse_warnings=parse_warnings,
        validation_errors=[],
        evidence=resolved.evidence,
    )

    return preprocessed, extracted, resolved, result


def run_full_pipeline(input_path: str) -> Tuple[PreprocessedDocument, ExtractedCandidates, ResolvedFields, ParseResult]:
    # 전처리 -> 추출 -> 선택 -> 정규화를 모두 수행
    return run_normalize_pipeline(input_path)