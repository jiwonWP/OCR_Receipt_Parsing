from pathlib import Path
import json

from .pipeline import run_preprocess_pipeline


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
        result = run_preprocess_pipeline(str(input_path))

        # 산출물 저장
        stem = input_path.stem
        _write_text(PROCESSED_DIR / f"{stem}_raw.txt", result.raw_text)
        _write_text(PROCESSED_DIR / f"{stem}_normalized.txt", result.normalized_text)

        _write_json(
            PROCESSED_DIR / f"{stem}_preprocess_log.json",
            {
                "source": str(input_path),
                "applied_rules": result.applied_rules,
                "warnings": result.warnings,
                "raw_line_count": len(result.raw_text.splitlines()),
                "normalized_line_count": len(result.normalized_text.splitlines()),
            },
        )

        print(f"\n=== {filename} ===")
        print(f"- 적용 규칙: {result.applied_rules}")
        print(f"- 경고: {result.warnings}")
        print(f"- raw lines: {len(result.raw_text.splitlines())}")
        print(f"- normalized lines: {len(result.normalized_text.splitlines())}")
        print(f"- 산출물: {stem}_raw.txt / {stem}_normalized.txt / {stem}_preprocess_log.json")

    print(f"\n[완료] 전처리 산출물 저장 위치: {PROCESSED_DIR}")
    if any_missing:
        print("[주의] 일부 입력 파일이 누락되어 처리하지 못했습니다.")


if __name__ == "__main__":
    main()
