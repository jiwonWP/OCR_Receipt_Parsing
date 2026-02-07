from __future__ import annotations

import json
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

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

# 처리할 대상 파일 목록
TARGET_FILES = [
    "sample_01.json",
    "sample_02.json",
    "sample_03.json",
    "sample_04.json",
]


# 텍스트 파일 쓰기
def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding=Constants.DEFAULT_ENCODING)

# JSON 파일 쓰기
def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=Constants.JSON_INDENT),
        encoding=Constants.DEFAULT_ENCODING
    )


def create_preprocess_outputs(
    stem: str,
    preprocessed_dict: Dict[str, Any],
    raw_text: str,
    normalized_text: str
) -> Dict[str, Any]:
    # 전처리 단계 산출물 데이터 생성
    return {
        "log": {
            "applied_rules": preprocessed_dict.get("applied_rules", []),
            "warnings": preprocessed_dict.get("warnings", []),
            "raw_line_count": len(raw_text.splitlines()),
            "normalized_line_count": len(normalized_text.splitlines()),
        },
        "raw": raw_text,
        "normalized": normalized_text,
    }


def create_extract_outputs(
    extracted_dict: Dict[str, Any]
) -> Dict[str, Any]:
    
    # 추출 단계 산출물 데이터 생성
    candidates = extracted_dict.get("candidates", [])
    summary = summarize_candidates(candidates)
    
    return {
        "candidates": candidates,
        "log": {
            "warnings": extracted_dict.get("warnings", []),
            "candidate_summary": summary,
        },
        "summary": summary,
    }


def create_resolve_outputs(
    resolved_dict: Dict[str, Any]
) -> Dict[str, Any]:
    # 후보 선택 단계 산출물 데이터 생성
    
    return {
        "resolved_fields": {
            "date_raw": resolved_dict.get("date_raw"),
            "time_raw": resolved_dict.get("time_raw"),
            "vehicle_no_raw": resolved_dict.get("vehicle_no_raw"),
            "gross_weight_raw": resolved_dict.get("gross_weight_raw"),
            "tare_weight_raw": resolved_dict.get("tare_weight_raw"),
            "net_weight_raw": resolved_dict.get("net_weight_raw"),
        },
        "evidence": resolved_dict.get("evidence", {}),
        "warnings": resolved_dict.get("warnings", []),
    }

# 단일 파일 처리 함수
def process_single_file(input_path: Path) -> Tuple[str, bool, str]:

    if not input_path.exists():
        return "MISSING", False, ""
    
    try:
        # 파이프라인 실행
        preprocessed, extracted, resolved, parsed = run_full_pipeline(str(input_path))
        
        stem = input_path.stem
        
        # 데이터를 dict로 변환
        preprocessed_dict = asdict(preprocessed)
        extracted_dict = asdict(extracted)
        resolved_dict = asdict(resolved)
        parsed_dict = asdict(parsed)
        
        # 1) 전처리 산출물
        preprocess_out = create_preprocess_outputs(
            stem=stem,
            preprocessed_dict=preprocessed_dict,
            raw_text=preprocessed.raw_text,
            normalized_text=preprocessed.normalized_text
        )
        
        write_text(PROCESSED_DIR / f"{stem}_raw.txt", preprocess_out["raw"])
        write_text(PROCESSED_DIR / f"{stem}_normalized.txt", preprocess_out["normalized"])
        write_json(PROCESSED_DIR / f"{stem}_preprocess_log.json", {
            "source": str(input_path),
            **preprocess_out["log"]
        })
        
        # 2) Extractor 산출물
        extract_out = create_extract_outputs(extracted_dict)
        
        write_json(PROCESSED_DIR / f"{stem}_candidates.json", {
            "source": str(input_path),
            "candidates": extract_out["candidates"],
        })
        write_json(PROCESSED_DIR / f"{stem}_extract_log.json", {
            "source": str(input_path),
            **extract_out["log"]
        })
        
        # 3) Resolver 산출물
        resolve_out = create_resolve_outputs(resolved_dict)
        write_json(PROCESSED_DIR / f"{stem}_resolved.json", {
            "source": str(input_path),
            **resolve_out
        })
        
        # 4) ParseResult 산출물
        write_json(PROCESSED_DIR / f"{stem}_parsed.json", parsed_dict)
        
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
        files = [
            f"{stem}_raw.txt",
            f"{stem}_normalized.txt",
            f"{stem}_preprocess_log.json",
            f"{stem}_candidates.json",
            f"{stem}_extract_log.json",
            f"{stem}_resolved.json",
            f"{stem}_parsed.json",
        ]
        console_output += f"\n\n[산출물]"
        for f in files:
            console_output += f"\n  - {f}"
        
        status_text = "VALID" if is_valid else "INVALID"
        console_output += f"\n파일: {input_path.name} [SUCCESS ({status_text})]"
        
        return "SUCCESS", is_valid, console_output
        
    except Exception as e:
        error_msg = f"\nERROR: {input_path.name} 처리 중 오류 발생\n"
        error_msg += f"  {type(e).__name__}: {e}\n"
        
        import traceback
        error_msg += traceback.format_exc()
        
        return "FAILED", False, error_msg


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    results: List[Tuple[str, str, bool]] = []

    for filename in TARGET_FILES:
        input_path = RAW_DIR / filename
        
        status, is_valid, console_output = process_single_file(input_path)
        
        # 콘솔 출력
        print(console_output)
        
        results.append((status, filename, is_valid))

    # 최종 요약
    print(f"\n{'='*60}")
    print("처리 완료")
    print(f"{'='*60}")
    print(f"저장 위치: {PROCESSED_DIR}")

    success_count = sum(1 for r in results if r[0] == "SUCCESS")
    valid_count = sum(1 for r in results if r[0] == "SUCCESS" and r[2] is True)

    print("\n결과 요약:")
    for status, name, is_valid in results:
        if status == "SUCCESS":
            symbol = "✓" if is_valid else "✗"
            detail = "VALID" if is_valid else "INVALID"
            print(f"  {symbol} {status:7s} ({detail:7s}) : {name}")
        elif status == "MISSING":
            print(f"  ! {status:7s} (N/A    ) : {name}")
        else:
            print(f"  ✗ {status:7s} (N/A    ) : {name}")

    print("\n통계:")
    print(f"  - 전체:        {len(results)}개")
    print(f"  - 성공(실행):  {success_count}개")
    print(f"  - 검증통과:    {valid_count}개")


if __name__ == "__main__":
    main()