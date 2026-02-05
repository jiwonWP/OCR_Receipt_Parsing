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

    any_missing = False
    for filename in TARGET_FILES:
        input_path = RAW_DIR / filename
        if not input_path.exists():
            print(f"ERROR_입력 파일을 찾을 수 없습니다: {input_path}")
            any_missing = True
            continue
        # 실행
        preprocessed, extracted = run_full_pipeline(str(input_path))

        # 산출물 저장
        stem = input_path.stem
        # 전처리 산출물
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

        # Extractor 산출물
        extracted_dict = asdict(extracted)

        # candidates는 dataclass -> dict로 변환되어 있으니 그대로 저장 가능
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

        print(f"\n=== {filename} ===")
        print(f"- 전처리 적용 규칙: {preprocessed.applied_rules}")
        print(f"- 전처리 경고: {preprocessed.warnings}")
        print(f"- 후보 총개수: {summary['counts']['total']}")
        print(f"- 후보(필드별): {summary['counts']['by_field']}")
        print(f"- 후보(방법별): {summary['counts']['by_method']}")
        print(f"- 추출 경고: {extracted_dict.get('warnings', [])}")
        print(
            f"- 산출물: "
            f"{stem}_raw.txt / {stem}_normalized.txt / {stem}_preprocess_log.json / "
            f"{stem}_candidates.json / {stem}_extract_log.json"
        )
    print(f"\n[완료] 전처리 산출물 저장 위치: {PROCESSED_DIR}")
    if any_missing:
        print("[주의] 일부 입력 파일이 누락되어 처리하지 못했습니다.")


if __name__ == "__main__":
    main()
