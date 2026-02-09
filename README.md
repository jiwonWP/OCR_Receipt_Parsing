#  OCR Text Parsing

계근지(차량 중량 영수증)의 OCR 결과를 구조화된 데이터로 변환하는 파이프라인

## 특징

- **원문 보존:** OCR 원본은 절대 변형하지 않고 보존
- **보수적 정규화:** 삭제보다 분리/보존 우선
- **후보 기반 추출:** 의미 확정을 최대한 뒤로 미룸
- **자동 복구:** 실중량 계산 및 중량 불일치 복구
- **추적 가능성:** 모든 처리 과정 기록

> 설계 의도, 단계별 책임 범위, 전처리 규칙 명세, 샘플 전수 분석 등  
> **상세한 근거/설명은 `docs/` 폴더에 모두 정리되어 있습니다.**

특히 다음 문서를 중심으로 확인할 수 있습니다.

- `docs/architecture.md`
- `docs/CLI_GUIDE.md`
- `docs/data_audit.md`
- `docs/OUTPUT_SPEC.md`
- `docs/preprocess_spec.md`
- `docs/PROJECT_STRUCTURE.md`
- `docs/README_docs.md`
- `docs/README_TEST.md`
- `docs/sprint.md`

---

## 빠른 시작

### 1. 설치

```bash
# 가상환경 생성 (선택)
python -m venv venv
source venv/Scripts/activate  # Windows Git Bash

# 의존성 설치
pip install -r requirements.txt
```

### 2. 실행

```bash
python -m src.main
```

### 3. 결과 확인

```bash
# 출력 디렉토리
ls data/processed/

# 요약 CSV
cat data/processed/summary.csv
```

---

## 파이프라인 구조

```
입력 (OCR JSON) → Loader → Preprocessor → Extractor → Resolver → Normalizer → Validator → 출력 (JSON/CSV)
```

### 단계별 역할

| 단계 | 역할 | 입력 | 출력 |
|------|------|------|------|
| **Loader** | JSON 읽기, 원문 보존 | 파일 경로 | `RawDocument` |
| **Preprocessor** | 텍스트 정규화 | OCR 텍스트 | `PreprocessedDocument` |
| **Extractor** | 후보 추출 (라벨/패턴) | 정규화 텍스트 | `ExtractedCandidates` |
| **Resolver** | 최적 후보 선택 | 후보 목록 | `ResolvedFields` |
| **Normalizer** | 타입 변환 (str→int, date) | 원본 문자열 | 정규화된 값 |
| **Validator** | 검증 및 복구 | 정규화된 필드 | `ValidationResult` |

---

## 입출력

### 입력
```
data/raw/
├── sample_01.json
├── sample_02.json
├── sample_03.json
└── sample_04.json
```

**JSON 형식:**
```json
{
  "text": "계량일자: 2026-02-02\n차량번호: 80구8713\n총중량: 12,480 kg\n...",
  "other_fields": "..."
}
```

### 출력

각 입력 파일당 **7개 산출물** 생성:

```
data/processed/
├── sample_01_raw.txt               # OCR 원문
├── sample_01_normalized.txt        # 정규화 텍스트
├── sample_01_preprocess_log.json   # 전처리 로그
├── sample_01_candidates.json       # 추출 후보 목록
├── sample_01_extract_log.json      # 추출 로그
├── sample_01_resolved.json         # 후보 선택 결과
├── sample_01_parsed.json           # 최종 파싱 결과
└── summary.csv                     # 전체 요약 CSV
```

**최종 결과 예시 (`sample_01_parsed.json`):**
```json
{
  "source": "sample_01.json",
  "date": "2026-02-02",
  "time": "09:12",
  "vehicle_no": "8713",
  "gross_weight_kg": 12480,
  "tare_weight_kg": 7470,
  "net_weight_kg": 5010,
  "is_valid": true,
  "validation_errors": [],
  "parse_warnings": [],
  "imputation_notes": []
}
```

---

## 주요 기능

### 1. 전처리 (Preprocessor)

**목표:** 형태 통일, 노이즈 분리/보존

**수행 작업:**
- 라벨 표준화: `날 짜` → `날짜`
- 공백 정리: `02 : 13` → `02:13`
- 한글 시간: `11시 33분` → `11:33`
- 숫자 결합: `5 900 kg` → `5,900 kg`
- suffix 분리: `2026-02-02-00004` → `2026-02-02 doc_seq:00004`
- 꼬리 보존: `2026-02-02 0016` → `2026-02-02 raw_tail:0016`

**원칙:**
- 의미를 확정하지 않음
- 삭제보다 분리/보존
- 과치환 방지

### 2. 추출 (Extractor)

**전략:**
1. **라벨 기반** (우선) - 라벨 토큰 발견 시 근처 값 추출
2. **패턴 기반** (fallback) - 정규식 패턴으로 추출

**예시:**
```python
# 라벨 기반 (score: 90)
"총중량: 12,480 kg" → Candidate(field="gross_weight_kg", value_raw="12,480 kg", method="label")

# 패턴 기반 (score: 50)
"2026-02-02 09:12" → Candidate(field="date", value_raw="2026-02-02", method="pattern")
```

### 3. 검증 및 복구 (Validator)

**검증 규칙:**
- 필수 필드: `date`, `vehicle_no`
- 중량 범위: 음수 불가, 100톤 초과 불가
- 중량 관계: `총중량 >= 차중량`, `실중량 ≈ 총중량 - 차중량` (±2% 또는 ±10kg)

**자동 복구:**
1. **실중량 계산:**
   ```
   if 총중량 and 차중량 and not 실중량:
       실중량 = 총중량 - 차중량
   ```

2. **중량 불일치 복구:**
   ```
   후보 풀에서 올바른 (총, 차, 실) 조합 탐색
   ```

**복구 기록:**
```json
{
  "imputation_notes": [
    "imputed:net_weight=5010 (gross=12480 - tare=7470)",
    "recovered:net=130 (from weight_candidates, expected=130, diff=0, tol=10)"
  ]
}
```

---

## 핵심 설계 원칙

### 1. 원문 보존
```
Loader 단계에서 OCR 원문을 절대 변형하지 않음
→ 디버깅, 규칙 개선의 기준 데이터
```

### 2. 의미 확정 지연
```
Preprocessor: 형태만 통일
Extractor: 후보 수집
Resolver: 후보 선택
Validator: 최종 확정/거부
```

### 3. 분리/보존 우선
```
삭제 ❌  날짜 뒤 '0016' 제거
분리 ✅  '2026-02-02 raw_tail:0016'

삭제 ❌  날짜 suffix '-00004' 제거
분리 ✅  '2026-02-02 doc_seq:00004'
```

### 4. 추적 가능성
모든 처리 과정 기록:
- `applied_rules`: 적용된 전처리 규칙
- `warnings`: 애매한 상황 경고
- `evidence`: 후보 선택 근거
- `imputation_notes`: 복구 이력

---

## 파일 구조

```
ocr-parsing-pipeline/
├── data/
│   ├── raw/              # OCR 입력 파일
│   └── processed/        # 파이프라인 출력
├── logs/                 # 실행 로그
├── src/
│   ├── main.py           # 실행 엔트리포인트
│   ├── pipeline.py       # 파이프라인 오케스트레이션
│   ├── loader.py         # [1] JSON 로드
│   ├── preprocessor.py   # [2] 텍스트 정규화
│   ├── extractor.py      # [3] 후보 추출
│   ├── resolver.py       # [4] 후보 선택
│   ├── normalizers.py    # [5] 타입 변환
│   ├── validators.py     # [6] 검증 및 복구
│   ├── config.py         # 정책 및 상수
│   ├── patterns.py       # 정규식 패턴
│   ├── schema.py         # 내부 데이터 모델
│   ├── schemas.py        # 출력 스키마
│   ├── output_formatters.py  # 파일 생성
│   ├── utils.py          # 유틸리티
│   ├── error_handler.py  # 에러 처리
│   ├── logger.py         # 로깅
│   └── progress.py       # 진행 표시
├── tests/                # 단위 테스트 (85+)
├── docs/                 # 문서
│   ├── architecture.md
│   ├── preprocess_spec.md
│   ├── data_audit.md
│   ├── CLI_GUIDE.md
│   ├── OUTPUT_SPEC.md
│   └── README_TEST.md
├── requirements.txt
└── README.md
```

---

## 테스트

```bash
# 전체 테스트 (85+ 테스트)
pytest tests/

# 특정 모듈
pytest tests/test_normalizers.py
pytest tests/test_validators.py

# 커버리지
pytest --cov=src tests/
```

**테스트 구성:**
- `test_normalizers.py` (30+) - 중량/시간/날짜 정규화
- `test_validators.py` (15+) - 검증 및 복구 로직
- `test_preprocessor.py` (15+) - 전처리 규칙
- `test_utils.py` (15+) - 유틸리티 함수
- `test_config.py` (10+) - 정책 및 상수

---

## 의존성

**Python:** 3.10+

**라이브러리:**
```
pydantic        # 데이터 검증
regex           # 정규식 패턴
python-dateutil # 날짜 파싱
pandas          # CSV 처리
pytest          # 테스트
```

---

## 문서

| 문서 | 내용 |
|------|------|
| [architecture.md](docs/architecture.md) | 시스템 아키텍처 상세 설명 |
| [preprocess_spec.md](docs/preprocess_spec.md) | 전처리 규칙 명세 (11개 규칙) |
| [data_audit.md](docs/data_audit.md) | OCR 샘플 전수 조사 결과 |
| [CLI_GUIDE.md](docs/CLI_GUIDE.md) | CLI 실행 및 로그 가이드 |
| [OUTPUT_SPEC.md](docs/OUTPUT_SPEC.md) | 출력 파일 형식 명세 |
| [README_TEST.md](docs/README_TEST.md) | 테스트 실행 가이드 |
| [README_docs.md](docs/README_docs.md) | 문서 인덱스 |

---

## 실행 예시

```bash
$ python -m src.main

==============================================================
            OCR 데이터 처리 파이프라인
==============================================================
INFO | 처리 대상: 4개 파일
INFO | 입력 경로: data/raw
INFO | 출력 경로: data/processed

[1/4] sample_01.json 처리 중...
  ✓ sample_01.json: 검증 통과

[2/4] sample_02.json 처리 중...
  ✓ sample_02.json: 검증 통과

[3/4] sample_03.json 처리 중...
  ✓ sample_03.json: 검증 통과

[4/4] sample_04.json 처리 중...
  ✗ sample_04.json: 검증 실패

진행률 |██████████████████████████████████████████████████| 100% 완료

==============================================================
                     처리 완료
==============================================================
저장 위치: data/processed

결과 요약:
  전체:        4개
  성공(실행):  4개
  검증통과:    3개
  실패:        0개
  파일 없음:   0개

처리가 완료되었습니다.
```

---

## 예제: 샘플 처리 흐름

**입력 (OCR):**
```
날 짜: 2026-02-02-00004
차번호: 80구8713
총중량: 02 : 07 13 460 kg
차중량: 02 : 13 7 560 kg
실중량: 5 900 kg
```

**전처리:**
```
날짜: 2026-02-02 doc_seq:00004
차량번호: 80구8713
총중량: 02:07 13,460 kg
차중량: 02:13 7,560 kg
실중량: 5,900 kg
```

**추출:**
```
date: "2026-02-02" (label, score=90)
vehicle_no: "80구8713" (label, score=90)
gross_weight_kg: "13,460 kg" (label, score=90)
tare_weight_kg: "7,560 kg" (label, score=90)
net_weight_kg: "5,900 kg" (label, score=90)
```

**정규화 + 검증:**
```json
{
  "date": "2026-02-02",
  "vehicle_no": "80구8713",
  "gross_weight_kg": 13460,
  "tare_weight_kg": 7560,
  "net_weight_kg": 5900,
  "is_valid": true
}
```

---

