from __future__ import annotations

import json
import logging
from pathlib import Path
from dataclasses import asdict
from typing import Any, Dict, List, Tuple

from .pipeline import run_full_pipeline
from .utils import (
    summarize_candidates,
    build_processing_summary,
    format_console_output,
)
from .config import Constants
from .output_formatters import (
    FileNamingConvention,
    format_preprocess_log,
    format_extract_log,
    format_candidates_output,
    format_resolved_output,
    format_parsed_output,
    format_csv_row,
    write_summary_csv,
    get_output_files,
)
from .schemas import CSVRowSchema
from .logger import setup_logger, log_step
from .progress import ProgressBar, print_section_header, print_status, Colors
from .error_handler import ErrorHandler, FileReadError, safe_execute

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
LOG_DIR = ROOT / "logs"

# 처리할 대상 파일 목록
TARGET_FILES = [
    "sample_01.json",
    "sample_02.json",
    "sample_03.json",
    "sample_04.json",
]

# 글로벌 로거 및 에러 핸들러
logger = None
error_handler = None


# ============================================================================
# 파일 I/O 함수 (순수 I/O만 담당)
# ============================================================================

def write_text(path: Path, content: str) -> None:
    """텍스트 파일 쓰기"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding=Constants.DEFAULT_ENCODING)


def write_json(path: Path, data: dict) -> None:
    """JSON 파일 쓰기"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=Constants.JSON_INDENT),
        encoding=Constants.DEFAULT_ENCODING
    )


# ============================================================================
# 산출물 생성 함수 (I/O 없는 순수 함수)
# ============================================================================

def create_preprocess_outputs(
    stem: str,
    preprocessed_dict: Dict[str, Any],
    raw_text: str,
    normalized_text: str
) -> Dict[str, Any]:
    """
    전처리 단계 산출물 데이터 생성
    
    Returns:
        {
            "log": {...},  # JSON 로그 데이터
            "raw": str,    # 원문
            "normalized": str  # 정규화 텍스트
        }
    """
    log_data = format_preprocess_log(
        source=f"{stem}.json",
        applied_rules=preprocessed_dict.get("applied_rules", []),
        warnings=preprocessed_dict.get("warnings", []),
        raw_line_count=len(raw_text.splitlines()),
        normalized_line_count=len(normalized_text.splitlines()),
    )
    
    return {
        "log": log_data,
        "raw": raw_text,
        "normalized": normalized_text,
    }


def create_extract_outputs(
    stem: str,
    extracted_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """
    추출 단계 산출물 데이터 생성
    
    Returns:
        {
            "candidates": {...},
            "log": {...},
            "summary": {...}
        }
    """
    candidates = extracted_dict.get("candidates", [])
    summary = summarize_candidates(candidates)
    
    candidates_output = format_candidates_output(
        source=f"{stem}.json",
        candidates=candidates,
    )
    
    log_data = format_extract_log(
        source=f"{stem}.json",
        warnings=extracted_dict.get("warnings", []),
        candidate_summary=summary,
    )
    
    return {
        "candidates": candidates_output,
        "log": log_data,
        "summary": summary,
    }


def create_resolve_outputs(
    stem: str,
    resolved_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """
    후보 선택 단계 산출물 데이터 생성
    """
    resolved_fields = {
        "date_raw": resolved_dict.get("date_raw"),
        "time_raw": resolved_dict.get("time_raw"),
        "vehicle_no_raw": resolved_dict.get("vehicle_no_raw"),
        "gross_weight_raw": resolved_dict.get("gross_weight_raw"),
        "tare_weight_raw": resolved_dict.get("tare_weight_raw"),
        "net_weight_raw": resolved_dict.get("net_weight_raw"),
    }
    
    output_data = format_resolved_output(
        source=f"{stem}.json",
        resolved_fields=resolved_fields,
        evidence=resolved_dict.get("evidence", {}),
        warnings=resolved_dict.get("warnings", []),
    )
    
    return output_data


# ============================================================================
# 단일 파일 처리 함수
# ============================================================================

def process_single_file(input_path: Path) -> Tuple[str, bool, str, Dict[str, Any]]:
    """
    단일 파일 처리 (테스트 가능한 순수 로직)
    
    Args:
        input_path: 입력 파일 경로
    
    Returns:
        (status, is_valid, console_output, parsed_data)
        status: "SUCCESS" | "FAILED" | "MISSING"
        is_valid: 검증 통과 여부
        console_output: 콘솔 출력 문자열
        parsed_data: 파싱 결과 딕셔너리 (CSV 생성용)
    """
    global logger, error_handler
    
    if not input_path.exists():
        if logger:
            logger.warning(f"파일 없음: {input_path.name}")
        return "MISSING", False, "", {}
    
    try:
        if logger:
            logger.info(f"파일 처리 시작: {input_path.name}")
        
        # 파이프라인 실행
        with log_step(logger, f"{input_path.name} 파이프라인"):
            preprocessed, extracted, resolved, parsed = run_full_pipeline(str(input_path))
        
        stem = input_path.stem
        
        # 데이터를 dict로 변환
        preprocessed_dict = asdict(preprocessed)
        extracted_dict = asdict(extracted)
        resolved_dict = asdict(resolved)
        parsed_dict = asdict(parsed)
        
        # 1) 전처리 산출물
        with log_step(logger, "전처리 산출물 생성"):
            preprocess_out = create_preprocess_outputs(
                stem=stem,
                preprocessed_dict=preprocessed_dict,
                raw_text=preprocessed.raw_text,
                normalized_text=preprocessed.normalized_text
            )
            
            write_text(
                PROCESSED_DIR / FileNamingConvention.preprocess_raw(stem),
                preprocess_out["raw"]
            )
            write_text(
                PROCESSED_DIR / FileNamingConvention.preprocess_normalized(stem),
                preprocess_out["normalized"]
            )
            write_json(
                PROCESSED_DIR / FileNamingConvention.preprocess_log(stem),
                preprocess_out["log"]
            )
        
        # 2) Extractor 산출물
        with log_step(logger, "추출 산출물 생성"):
            extract_out = create_extract_outputs(
                stem=stem,
                extracted_dict=extracted_dict
            )
            
            write_json(
                PROCESSED_DIR / FileNamingConvention.extract_candidates(stem),
                extract_out["candidates"]
            )
            write_json(
                PROCESSED_DIR / FileNamingConvention.extract_log(stem),
                extract_out["log"]
            )
        
        # 3) Resolver 산출물
        with log_step(logger, "후보 선택 산출물 생성"):
            resolve_out = create_resolve_outputs(
                stem=stem,
                resolved_dict=resolved_dict
            )
            write_json(
                PROCESSED_DIR / FileNamingConvention.resolve_result(stem),
                resolve_out
            )
        
        # 4) ParseResult 산출물 (포맷터 사용)
        with log_step(logger, "최종 파싱 결과 생성"):
            parsed_output = format_parsed_output(
                source=f"{stem}.json",
                date=parsed_dict.get("date"),
                time=parsed_dict.get("time"),
                vehicle_no=parsed_dict.get("vehicle_no"),
                gross_weight_kg=parsed_dict.get("gross_weight_kg"),
                tare_weight_kg=parsed_dict.get("tare_weight_kg"),
                net_weight_kg=parsed_dict.get("net_weight_kg"),
                parse_warnings=parsed_dict.get("parse_warnings", []),
                validation_errors=parsed_dict.get("validation_errors", []),
                imputation_notes=parsed_dict.get("imputation_notes", []),
                is_valid=len(parsed_dict.get("validation_errors", [])) == 0,
            )
            
            write_json(
                PROCESSED_DIR / FileNamingConvention.parse_result(stem),
                parsed_output
            )
        
        # 5) 요약 생성
        summary = build_processing_summary(
            preprocessed_dict=preprocessed_dict,
            extracted_dict=extracted_dict,
            resolved_dict=resolved_dict,
            parsed_dict=parsed_dict,
            candidate_summary=extract_out["summary"]
        )
        
        is_valid = summary["is_valid"]
        
        # 6) 콘솔 출력 생성
        console_output = format_console_output(input_path.name, summary)
        
        # 7) 산출물 목록 추가
        files = get_output_files(stem)
        console_output += f"\n\n[산출물]"
        for f in files:
            console_output += f"\n  - {f}"
        
        status_text = "VALID" if is_valid else "INVALID"
        console_output += f"\n파일: {input_path.name} [SUCCESS ({status_text})]"
        
        if logger:
            if is_valid:
                logger.info(f"✓ {input_path.name}: 검증 통과")
            else:
                logger.warning(f"✗ {input_path.name}: 검증 실패")
        
        return "SUCCESS", is_valid, console_output, parsed_output
        
    except Exception as e:
        error_msg = f"\nERROR: {input_path.name} 처리 중 오류 발생\n"
        error_msg += f"  {type(e).__name__}: {e}\n"
        
        if error_handler:
            error_handler.handle_error(
                error=e,
                context=f"파일 처리: {input_path.name}",
                recoverable=False
            )
        
        if logger:
            logger.error(f"파일 처리 실패: {input_path.name}", exc_info=True)
        
        import traceback
        error_msg += traceback.format_exc()
        
        return "FAILED", False, error_msg, {}


# ============================================================================
# 메인 함수
# ============================================================================

def main() -> None:
    """메인 실행 함수"""
    global logger, error_handler
    
    # 로거 및 에러 핸들러 초기화
    logger = setup_logger(
        name="ocr_pipeline",
        log_dir=LOG_DIR,
        console_level=logging.INFO
    )
    error_handler = ErrorHandler(logger)
    
    # 헤더 출력
    print_section_header("OCR 데이터 처리 파이프라인")
    
    logger.info(f"처리 대상: {len(TARGET_FILES)}개 파일")
    logger.info(f"입력 경로: {RAW_DIR}")
    logger.info(f"출력 경로: {PROCESSED_DIR}")
    
    # 디렉토리 생성
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # results: (status, filename, is_valid)
    results: List[Tuple[str, str, bool]] = []
    
    # CSV 행 수집
    csv_rows: List[CSVRowSchema] = []
    
    # 프로그레스 바
    progress = ProgressBar(
        total=len(TARGET_FILES),
        prefix="진행률",
        suffix="완료"
    )

    for i, filename in enumerate(TARGET_FILES, 1):
        input_path = RAW_DIR / filename
        
        logger.info(f"\n[{i}/{len(TARGET_FILES)}] {filename} 처리 중...")
        
        status, is_valid, console_output, parsed_data = process_single_file(input_path)
        
        # 콘솔 출력 (상세 정보는 디버그 모드에서만)
        if status == "SUCCESS":
            if is_valid:
                print_status("✓", filename, "검증 통과", Colors.GREEN)
            else:
                print_status("✗", filename, "검증 실패", Colors.YELLOW)
        elif status == "MISSING":
            print_status("!", filename, "파일 없음", Colors.YELLOW)
        else:
            print_status("✗", filename, "처리 실패", Colors.RED)
        
        results.append((status, filename, is_valid))
        
        # CSV 행 추가
        if status == "SUCCESS" and parsed_data:
            csv_row = format_csv_row(filename, parsed_data)
            csv_rows.append(csv_row)
        
        # 프로그레스 바 업데이트
        progress.update()

    # CSV 파일 생성
    if csv_rows:
        with log_step(logger, "요약 CSV 생성"):
            csv_path = PROCESSED_DIR / FileNamingConvention.summary_csv()
            write_summary_csv(csv_path, csv_rows)
            logger.info(f"CSV 파일 생성: {csv_path}")
            print(f"  ✓ 요약 CSV 생성: {csv_path.name}")

    # 최종 요약
    print_section_header("처리 완료")
    
    logger.info(f"저장 위치: {PROCESSED_DIR}")
    print(f"저장 위치: {PROCESSED_DIR}\n")

    success_count = sum(1 for r in results if r[0] == "SUCCESS")
    valid_count = sum(1 for r in results if r[0] == "SUCCESS" and r[2] is True)
    failed_count = sum(1 for r in results if r[0] == "FAILED")
    missing_count = sum(1 for r in results if r[0] == "MISSING")

    print("결과 요약:")
    print(f"  전체:        {len(results)}개")
    print(f"  성공(실행):  {success_count}개")
    print(f"  검증통과:    {valid_count}개")
    print(f"  실패:        {failed_count}개")
    print(f"  파일 없음:   {missing_count}개")
    
    logger.info(f"처리 완료: 전체 {len(results)}개, 성공 {success_count}개, 검증통과 {valid_count}개")
    
    # 에러 리포트
    if error_handler.has_critical_errors():
        logger.warning("\n치명적 에러가 발생했습니다.")
        error_summary = error_handler.get_error_summary()
        logger.warning(f"총 에러: {error_summary['total']}개 (치명적: {error_summary['critical']}개)")
        
        # 에러 리포트 파일 생성
        error_report_path = LOG_DIR / "error_report.txt"
        error_report = error_handler.generate_error_report()
        error_report_path.write_text(error_report, encoding="utf-8")
        logger.info(f"에러 리포트: {error_report_path}")
    
    print("\n처리가 완료되었습니다.")


if __name__ == "__main__":
    main()