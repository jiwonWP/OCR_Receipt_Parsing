from __future__ import annotations
from pathlib import Path
import json

from .pipeline import run_full_pipeline
from dataclasses import asdict
from collections import Counter, defaultdict
from typing import Any, Dict, List

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

# 텍스트/JSON 파일 쓰기
def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def _summarize_candidates(candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    # 후보 요약 통계 생성
    # 필드별 상위 후보 3개 + 메서드/필드별 건수
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

def main() -> None:
    # 출력 디렉토리 준비
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    results = []
    
    for filename in TARGET_FILES:
        input_path = RAW_DIR / filename
        if not input_path.exists():
            print(f"ERROR: 입력 파일을 찾을 수 없습니다: {input_path}")
            results.append(("MISSING", filename))
            continue
        
        try:
            # 실행
            preprocessed, extracted, resolved, parsed = run_full_pipeline(str(input_path))

            # 산출물 저장
            stem = input_path.stem
            
            # 1. 전처리 산출물
            _write_text(PROCESSED_DIR / f"{stem}_raw.txt", preprocessed.raw_text)
            _write_text(PROCESSED_DIR / f"{stem}_normalized.txt", preprocessed.normalized_text)

            _write_json(
                PROCESSED_DIR / f"{stem}_preprocess_log.json",
                {
                    "source": str(input_path),
                    "applied_rules": preprocessed.applied_rules,
                    "warnings": preprocessed.warnings,
                    "raw_line_count": len(preprocessed.raw_text.splitlines()),
                    "normalized_line_count": len(preprocessed.normalized_text.splitlines()),
                },
            )

            # 2. Extractor 산출물
            extracted_dict = asdict(extracted)

            _write_json(
                PROCESSED_DIR / f"{stem}_candidates.json",
                {
                    "source": str(input_path),
                    "candidates": extracted_dict.get("candidates", []),
                },
            )

            summary = _summarize_candidates(extracted_dict.get("candidates", []))

            _write_json(
                PROCESSED_DIR / f"{stem}_extract_log.json",
                {
                    "source": str(input_path),
                    "warnings": extracted_dict.get("warnings", []),
                    "candidate_summary": summary,
                },
            )

            # 3. Resolver 산출물
            resolved_dict = asdict(resolved)
            _write_json(
                PROCESSED_DIR / f"{stem}_resolved.json",
                {
                    "source": str(input_path),
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
                },
            )

            # 4. 최종 ParseResult 산출물
            parsed_dict = asdict(parsed)
            _write_json(
                PROCESSED_DIR / f"{stem}_parsed.json",
                parsed_dict,
            )

            # 검증 결과 판정
            validation_info = parsed_dict.get("evidence", {}).get("validation", {})
            is_valid = validation_info.get("is_valid", False)
            has_imputation = validation_info.get("has_imputation", False)
            
            status_symbol = "✓" if is_valid else "✗"
            status_text = "VALID" if is_valid else "INVALID"

            # 콘솔 출력
            print(f"\n{'='*60}")
            print(f"파일: {filename} [{status_symbol} {status_text}]")
            print(f"{'='*60}")
            print(f"\n[1] 전처리 단계")
            print(f"  - 적용 규칙: {len(preprocessed.applied_rules)}개")
            if preprocessed.applied_rules:
                print(f"    · {', '.join(preprocessed.applied_rules[:5])}")
                if len(preprocessed.applied_rules) > 5:
                    print(f"    · ... 외 {len(preprocessed.applied_rules) - 5}개")
            print(f"  - 경고: {len(preprocessed.warnings)}개")
            if preprocessed.warnings:
                for w in preprocessed.warnings[:3]:
                    print(f"    · {w}")
            
            print(f"\n[2] 추출 단계")
            print(f"  - 후보 총개수: {summary['counts']['total']}")
            print(f"  - 필드별 후보: {summary['counts']['by_field']}")
            print(f"  - 방법별 후보: {summary['counts']['by_method']}")
            print(f"  - 추출 경고: {len(extracted_dict.get('warnings', []))}개")
            
            print(f"\n[3] 후보 선택 단계")
            print(f"  - 선택된 필드:")
            for field_name in ["date_raw", "time_raw", "vehicle_no_raw", 
                              "gross_weight_raw", "tare_weight_raw", "net_weight_raw"]:
                value = resolved_dict.get(field_name)
                print(f"    · {field_name:20s}: {value if value else '(없음)'}")
            print(f"  - 선택 경고: {len(resolved_dict.get('warnings', []))}개")
            
            print(f"\n[4] 정규화 단계")
            print(f"  - 최종 결과:")
            print(f"    · 날짜:     {parsed_dict.get('date', '(없음)')}")
            print(f"    · 시간:     {parsed_dict.get('time', '(없음)')}")
            print(f"    · 차량번호: {parsed_dict.get('vehicle_no', '(없음)')}")
            
            gross = parsed_dict.get('gross_weight_kg')
            tare = parsed_dict.get('tare_weight_kg')
            net = parsed_dict.get('net_weight_kg')
            
            print(f"    · 총중량:   {f'{gross:,} kg' if gross is not None else '(없음)'}")
            print(f"    · 차중량:   {f'{tare:,} kg' if tare is not None else '(없음)'}")
            print(f"    · 실중량:   {f'{net:,} kg' if net is not None else '(없음)'}", end="")
            if has_imputation:
                print(" [계산됨]")
            else:
                print()
            
            print(f"  - 정규화 경고: {len(parsed_dict.get('parse_warnings', []))}개")
            if parsed_dict.get('parse_warnings'):
                for w in parsed_dict.get('parse_warnings', [])[:3]:
                    print(f"    · {w}")
            
            print(f"\n[5] 검증 단계")
            print(f"  - 검증 결과: {status_text}")
            print(f"  - 검증 오류: {len(parsed_dict.get('validation_errors', []))}개")
            if parsed_dict.get('validation_errors'):
                for e in parsed_dict.get('validation_errors', []):
                    print(f"    ✗ {e}")
            
            # 중량 관계 검증 결과 요약
            if gross is not None and tare is not None and net is not None:
                calc_net = gross - tare
                match = "일치" if calc_net == net else f"불일치 (계산={calc_net:,}kg)"
                print(f"  - 중량 관계: {gross:,} - {tare:,} = {net:,} [{match}]")
            
            print(f"\n[산출물]")
            files = [
                f"{stem}_raw.txt",
                f"{stem}_normalized.txt",
                f"{stem}_preprocess_log.json",
                f"{stem}_candidates.json",
                f"{stem}_extract_log.json",
                f"{stem}_resolved.json",
                f"{stem}_parsed.json",
            ]
            for f in files:
                print(f"  - {f}")
            
            results.append(("SUCCESS", filename, is_valid))
            
        except Exception as e:
            print(f"\nERROR: {filename} 처리 중 오류 발생")
            print(f"  {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            results.append(("FAILED", filename, False))
            continue

    # 최종 요약
    print(f"\n{'='*60}")
    print(f"처리 완료")
    print(f"{'='*60}")
    print(f"저장 위치: {PROCESSED_DIR}")
    print(f"\n결과 요약:")
    
    success_count = sum(1 for r in results if r[0] == "SUCCESS")
    valid_count = sum(1 for r in results if r[0] == "SUCCESS" and len(r) > 2 and r[2])
    
    for result in results:
        if len(result) == 2:
            status, name = result
            is_valid = False
        else:
            status, name, is_valid = result
        
        if status == "SUCCESS":
            symbol = "✓" if is_valid else "⚠"
            detail = "VALID" if is_valid else "INVALID"
            print(f"  {symbol} {status:7s} ({detail:7s}) : {name}")
        elif status == "FAILED":
            print(f"  ✗ {status:7s}             : {name}")
        else:
            print(f"  − {status:7s}             : {name}")
    
    print(f"\n통계:")
    print(f"  - 전체:     {len(results)}개")
    print(f"  - 성공:     {success_count}개")
    print(f"  - 검증통과: {valid_count}개")


if __name__ == "__main__":
    main()