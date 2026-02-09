# CLI 실행 가이드

## 개요

OCR 데이터 처리 파이프라인은 명령줄 인터페이스(CLI)로 실행됩니다.

---

## 기본 실행

```bash
# 파이썬 모듈로 실행
python -m src.main

# 또는 직접 실행
python src/main.py
```

---

## 실행 흐름

### 1. 초기화 단계
```
==============================================================
            OCR 데이터 처리 파이프라인
==============================================================
INFO | 처리 대상: 4개 파일
INFO | 입력 경로: /path/to/data/raw
INFO | 출력 경로: /path/to/data/processed
INFO | 로그 파일: /path/to/logs/pipeline_20260209_143022.log
```

### 2. 파일 처리 단계
```
[1/4] sample_01.json 처리 중...
INFO | ▶ sample_01.json 파이프라인 시작...
INFO | ▶ 전처리 산출물 생성 시작...
INFO | ✓ 전처리 산출물 생성 완료 (0.12초)
INFO | ▶ 추출 산출물 생성 시작...
INFO | ✓ 추출 산출물 생성 완료 (0.23초)
INFO | ▶ 후보 선택 산출물 생성 시작...
INFO | ✓ 후보 선택 산출물 생성 완료 (0.08초)
INFO | ▶ 최종 파싱 결과 생성 시작...
INFO | ✓ 최종 파싱 결과 생성 완료 (0.05초)
INFO | ✓ sample_01.json 파이프라인 완료 (0.48초)
INFO | ✓ sample_01.json: 검증 통과
  ✓ sample_01.json: 검증 통과

진행률 |██████████████████████████████████████████████████| 100% 완료
```

### 3. 요약 단계
```
INFO | ▶ 요약 CSV 생성 시작...
INFO | CSV 파일 생성: /path/to/data/processed/summary.csv
INFO | ✓ 요약 CSV 생성 완료 (0.03초)
  ✓ 요약 CSV 생성: summary.csv

==============================================================
                     처리 완료
==============================================================
저장 위치: /path/to/data/processed

결과 요약:
  전체:        4개
  성공(실행):  4개
  검증통과:    3개
  실패:        0개
  파일 없음:   0개

INFO | 처리 완료: 전체 4개, 성공 4개, 검증통과 3개

처리가 완료되었습니다.
```

---

## 상태 심볼

| 심볼 | 의미 | 색상 |
|------|------|------|
| ✓ | 성공 | 초록색 |
| ✗ | 실패 | 빨간색 |
| ! | 경고 | 노란색 |
| ▶ | 시작 | 파란색 |

---

## 출력 파일

### 디렉토리 구조
```
project/
├── data/
│   ├── raw/                  # 입력 파일
│   │   ├── sample_01.json
│   │   ├── sample_02.json
│   │   └── ...
│   └── processed/            # 출력 파일
│       ├── sample_01_raw.txt
│       ├── sample_01_normalized.txt
│       ├── sample_01_preprocess_log.json
│       ├── sample_01_candidates.json
│       ├── sample_01_extract_log.json
│       ├── sample_01_resolved.json
│       ├── sample_01_parsed.json
│       ├── ... (sample_02, 03, 04)
│       └── summary.csv       # 전체 요약
│
└── logs/                     # 로그 파일
    ├── pipeline_20260209_143022.log
    └── error_report.txt      # 에러 발생 시
```

---

## 로그 레벨

### 콘솔 출력 (INFO 이상)
- **INFO**: 정상 진행 상황
- **WARNING**: 경고 (처리는 계속)
- **ERROR**: 에러 (해당 파일 실패)

### 파일 로그 (DEBUG 이상)
- **DEBUG**: 상세 디버깅 정보
- **INFO**: 정상 진행 상황
- **WARNING**: 경고
- **ERROR**: 에러
- **CRITICAL**: 치명적 에러

### 로그 파일 형식
```
2026-02-09 14:30:22 | INFO     | ocr_pipeline | 처리 대상: 4개 파일
2026-02-09 14:30:22 | INFO     | ocr_pipeline | ▶ sample_01.json 파이프라인 시작...
2026-02-09 14:30:22 | DEBUG    | ocr_pipeline | 전처리 규칙 적용: remove_empty_lines
2026-02-09 14:30:23 | INFO     | ocr_pipeline | ✓ sample_01.json 파이프라인 완료 (0.48초)
```

---

## 에러 처리

### 복구 가능한 에러
```
WARNING | 복구 가능한 에러 [파일 읽기: sample_02.json]: FileNotFoundError - 파일을 찾을 수 없습니다
INFO    | 복구 액션: 건너뛰기
  ! sample_02.json: 파일 없음
```

### 치명적 에러
```
ERROR | 치명적 에러 [파일 처리: sample_03.json]: ValueError - 잘못된 데이터 형식
  ✗ sample_03.json: 처리 실패

WARNING | 치명적 에러가 발생했습니다.
WARNING | 총 에러: 1개 (치명적: 1개)
INFO    | 에러 리포트: /path/to/logs/error_report.txt
```

### 에러 리포트 (error_report.txt)
```
============================================================
에러 리포트
============================================================

총 에러: 1개
  - 복구 가능: 0개
  - 치명적: 1개

에러 유형별:
  - ValueError: 1개

상세 내역:
------------------------------------------------------------

[1] ValueError
  컨텍스트: 파일 처리: sample_03.json
  메시지: 잘못된 데이터 형식
  상태: 치명적
  스택 트레이스: (마지막 3줄)
    File "src/main.py", line 123, in process_single_file
    File "src/pipeline.py", line 45, in run_full_pipeline
    ValueError: 잘못된 데이터 형식
```

---

## 고급 설정

### 로그 레벨 변경
main.py 수정:
```python
logger = setup_logger(
    name="ocr_pipeline",
    log_dir=LOG_DIR,
    console_level=logging.DEBUG,  # DEBUG로 변경
    file_level=logging.DEBUG
)
```

### 컬러 출력 비활성화
```python
logger = setup_logger(
    name="ocr_pipeline",
    log_dir=LOG_DIR,
    enable_color=False  # 컬러 비활성화
)
```

### 파일 로깅 비활성화
```python
logger = setup_logger(
    name="ocr_pipeline",
    log_dir=None,  # 파일 로깅 안 함
    console_level=logging.INFO
)
```

---

## 문제 해결

### 1. "ModuleNotFoundError" 발생
```bash
# PYTHONPATH 설정
export PYTHONPATH=/path/to/project:$PYTHONPATH
python -m src.main
```

### 2. 로그 파일이 생성되지 않음
- `logs/` 디렉토리 쓰기 권한 확인
- `log_dir=None`으로 설정되어 있는지 확인

### 3. 진행 상황이 표시되지 않음
- 터미널이 ANSI 코드를 지원하는지 확인
- Windows: `colorama` 패키지 설치 권장

### 4. 메모리 부족
- 대용량 파일 처리 시 배치 크기 조정
- 청크 단위 처리로 변경 고려

---

## 성능 최적화

### 처리 시간 분석
로그 파일에서 단계별 소요 시간 확인:
```
✓ 전처리 산출물 생성 완료 (0.12초)
✓ 추출 산출물 생성 완료 (0.23초)
✓ 후보 선택 산출물 생성 완료 (0.08초)
✓ 최종 파싱 결과 생성 완료 (0.05초)
```

### 병렬 처리 (향후 계획)
```python
# 멀티프로세싱으로 여러 파일 동시 처리
from multiprocessing import Pool

with Pool(processes=4) as pool:
    results = pool.map(process_single_file, input_files)
```

---

## 참고 문서

- [OUTPUT_SPEC.md](OUTPUT_SPEC.md): 출력 파일 형식 명세
- [README_TEST.md](README_TEST.md): 테스트 실행 가이드
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md): 프로젝트 구조