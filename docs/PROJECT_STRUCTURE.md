# 프로젝트 구조

## 디렉토리 구조

```
ocr-parsing-pipeline/
├── data/
│   ├── raw/                      # OCR 입력 파일 (JSON)
│   │   ├── sample_01.json
│   │   ├── sample_02.json
│   │   ├── sample_03.json
│   │   └── sample_04.json
│   └── processed/                # 파이프라인 출력 파일
│       ├── sample_XX_raw.txt
│       ├── sample_XX_normalized.txt
│       ├── sample_XX_preprocess_log.json
│       ├── sample_XX_candidates.json
│       ├── sample_XX_extract_log.json
│       ├── sample_XX_resolved.json
│       ├── sample_XX_parsed.json
│       └── summary.csv
│
├── logs/                         # 실행 로그
│   ├── pipeline_YYYYMMDD_HHMMSS.log
│   └── error_report.txt
│
├── src/
│   ├── __init__.py
│   ├── main.py                   # 실행 엔트리포인트
│   ├── pipeline.py               # 파이프라인 오케스트레이션
│   │
│   ├── loader.py                 # [1단계] JSON 파일 로드
│   ├── preprocessor.py           # [2단계] 텍스트 정규화
│   ├── extractor.py              # [3단계] 후보 추출
│   ├── resolver.py               # [4단계] 후보 선택
│   ├── normalizers.py            # [5단계] 타입 정규화
│   ├── validators.py             # [6단계] 검증 및 복구
│   │
│   ├── config.py                 # 정책 및 상수
│   ├── patterns.py               # 정규식 패턴
│   ├── schema.py                 # 내부 데이터 모델 (dataclass)
│   ├── schemas.py                # 출력 스키마 (TypedDict)
│   │
│   ├── output_formatters.py     # 출력 파일 생성
│   ├── utils.py                  # 유틸리티 함수
│   │
│   ├── error_handler.py          # 에러 처리
│   ├── logger.py                 # 로깅 시스템
│   └── progress.py               # 진행 상황 표시
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py               # pytest fixtures
│   ├── test_config.py
│   ├── test_normalizers.py
│   ├── test_validators.py
│   ├── test_utils.py
│   ├── test_preprocessor.py
│   ├── test_schemas.py
│   └── test_output_formatters.py
│
├── docs/
│   ├── architecture.md           # 시스템 아키텍처
│   ├── preprocess_spec.md        # 전처리 규칙 명세
│   ├── data_audit.md             # OCR 샘플 분석
│   ├── sprint.md                 # Sprint 계획
│   ├── CLI_GUIDE.md              # CLI 사용 가이드
│   ├── OUTPUT_SPEC.md            # 출력 파일 명세
│   ├── README_TEST.md            # 테스트 가이드
│   └── README_docs.md            # 문서 인덱스
│
├── .gitignore
├── pytest.ini
├── requirements.txt
├── requirements-test.txt
└── README.md
```

---

## 파이프라인 흐름

```
[입력] sample_XX.json
    ↓
[1] loader.py          → RawDocument
    ↓
[2] preprocessor.py    → PreprocessedDocument
    ↓
[3] extractor.py       → ExtractedCandidates
    ↓
[4] resolver.py        → ResolvedFields
    ↓
[5] normalizers.py     → 타입 변환 (str→int, date, time)
    ↓
[6] validators.py      → ValidationResult (검증 + 복구)
    ↓
[7] output_formatters.py → JSON, CSV 파일 생성
    ↓
[출력] data/processed/
```

---

## 핵심 모듈 설명

### 파이프라인 단계

| 모듈 | 책임 | 입력 | 출력 |
|------|------|------|------|
| **loader.py** | JSON 파일 읽기 | 파일 경로 | `RawDocument` |
| **preprocessor.py** | 텍스트 정규화 | `raw_text` | `PreprocessedDocument` |
| **extractor.py** | 후보 추출 (라벨/패턴) | `normalized_text` | `ExtractedCandidates` |
| **resolver.py** | 최적 후보 선택 | `candidates` | `ResolvedFields` |
| **normalizers.py** | 타입 변환 | 원본 문자열 | int, date, time |
| **validators.py** | 검증 및 복구 | 정규화된 필드 | `ValidationResult` |

### 지원 모듈

| 모듈 | 역할 |
|------|------|
| **config.py** | 검증 정책, 라벨 토큰, 전처리 규칙 순서, 상수 |
| **patterns.py** | 날짜/시간/중량/차량번호 정규식 패턴 |
| **schema.py** | 내부 데이터 모델 (dataclass) |
| **schemas.py** | 출력 파일 스키마 (TypedDict) |
| **output_formatters.py** | JSON/CSV 포맷팅 및 파일명 규칙 |
| **utils.py** | 후보 요약, 중량 포맷팅, 콘솔 출력 생성 |
| **error_handler.py** | 에러 수집, 복구 전략, 에러 리포트 생성 |
| **logger.py** | 컬러 로깅, 파일 로깅, 컨텍스트 로깅 |
| **progress.py** | 프로그레스 바, 상태 심볼, 섹션 헤더 |

---

## 데이터 모델

### 내부 모델 (schema.py - dataclass)

파이프라인 단계 간 데이터 전달용

```python
@dataclass
class RawDocument:
    source_path: str
    raw_text: str
    meta: Dict

@dataclass
class PreprocessedDocument:
    raw_text: str
    normalized_text: str
    applied_rules: List[str]
    warnings: List[str]

@dataclass
class Candidate:
    field: str
    value_raw: str
    source_line: str
    method: str  # "label" | "pattern"
    score: int
    meta: Dict

@dataclass
class ExtractedCandidates:
    raw_text: str
    normalized_text: str
    candidates: List[Candidate]
    warnings: List[str]

@dataclass
class ResolvedFields:
    date_raw: Optional[str]
    time_raw: Optional[str]
    vehicle_no_raw: Optional[str]
    gross_weight_raw: Optional[str]
    tare_weight_raw: Optional[str]
    net_weight_raw: Optional[str]
    evidence: Dict
    warnings: List[str]

@dataclass
class ParseResult:
    date: Optional[str]
    time: Optional[str]
    vehicle_no: Optional[str]
    gross_weight_kg: Optional[int]
    tare_weight_kg: Optional[int]
    net_weight_kg: Optional[int]
    parse_warnings: List[str]
    validation_errors: List[str]
    imputation_notes: List[str]
    evidence: Dict
```

### 출력 스키마 (schemas.py - TypedDict)

JSON/CSV 출력 파일용

```python
class PreprocessLogSchema(TypedDict):
    source: str
    applied_rules: List[str]
    warnings: List[str]
    raw_line_count: int
    normalized_line_count: int

class CandidatesOutputSchema(TypedDict):
    source: str
    candidates: List[Dict]

class ResolvedOutputSchema(TypedDict):
    source: str
    resolved_fields: Dict
    evidence: Dict
    warnings: List[str]

class ParsedOutputSchema(TypedDict):
    source: str
    date: Optional[str]
    time: Optional[str]
    vehicle_no: Optional[str]
    gross_weight_kg: Optional[int]
    tare_weight_kg: Optional[int]
    net_weight_kg: Optional[int]
    parse_warnings: List[str]
    validation_errors: List[str]
    imputation_notes: List[str]
    is_valid: bool

class CSVRowSchema(TypedDict):
    filename: str
    date: str
    time: str
    vehicle_no: str
    gross_weight_kg: str
    tare_weight_kg: str
    net_weight_kg: str
    is_valid: str
    validation_errors: str
    parse_warnings: str
    imputation_notes: str
```

---

## 설정 및 정책 (config.py)

### ValidationPolicy
```python
MIN_TOLERANCE_KG = 10           # 최소 허용 오차
TOLERANCE_PERCENT = 0.02        # 2% 허용 오차
MAX_REALISTIC_WEIGHT_KG = 100000  # 100톤 상한
REQUIRED_FIELDS = ["date", "vehicle_no"]
```

### LabelTokens
```python
GROSS_WEIGHT = ["총중량", "총 중량", ...]
TARE_WEIGHT = ["차중량", "공차", "공차중량", ...]
NET_WEIGHT = ["실중량", "적재중량", ...]
DATE = ["일자", "날짜", "DATE"]
TIME = ["시간", "TIME"]
VEHICLE_NO = ["차량번호", "차 번", ...]
```

### PreprocessRules
전처리 규칙 실행 순서 정의
```python
EXECUTION_ORDER = [
    "collapsed_whitespace",
    "normalized_punctuation_spacing",
    "normalized_character_visual_noise",
    "standardized_labels",
    "converted_korean_time_to_colon_format",
    "merged_split_numbers_before_kg",
    "split_date_suffix_to_doc_seq",
    "preserved_ambiguous_date_tail_as_raw_tail",
    "split_vehicle_tail_keyword_as_category",
    "normalized_coordinates",
    "removed_symbol_only_lines",
]
```

---

## 에러 처리 시스템

### ErrorHandler (error_handler.py)

```python
class ErrorHandler:
    def handle_error(error, context, recoverable, recovery_action)
    def get_error_summary() -> Dict
    def has_critical_errors() -> bool
    def generate_error_report() -> str
```

**에러 분류:**
- `PipelineError` - 파이프라인 기본 예외
- `FileReadError` - 파일 읽기 실패
- `PreprocessError` - 전처리 실패
- `ExtractError` - 추출 실패
- `ResolveError` - 후보 선택 실패
- `ValidationError` - 검증 실패
- `OutputError` - 출력 생성 실패

**유틸리티:**
- `safe_execute()` - 기본값 반환
- `retry_on_error()` - 재시도 로직

---

## 로깅 시스템

### Logger (logger.py)

**기능:**
- 컬러 콘솔 출력
- 파일 로깅 (타임스탬프 포함)
- 로그 레벨: DEBUG, INFO, WARNING, ERROR, CRITICAL

**사용법:**
```python
from logger import setup_logger, log_step

logger = setup_logger(
    name="ocr_pipeline",
    log_dir=Path("logs"),
    console_level=logging.INFO,
    file_level=logging.DEBUG,
    enable_color=True
)

with log_step(logger, "전처리 단계"):
    # 작업 수행
    pass
```

---

## 진행 상황 표시 (progress.py)

**컴포넌트:**
- `ProgressBar` - 프로그레스 바
- `StepProgress` - 단계별 진행 표시
- `Spinner` - 로딩 스피너
- `print_section_header()` - 섹션 헤더
- `print_status()` - 상태 메시지 (✓/✗/!)
- `Colors` - ANSI 색상 코드

---

## 테스트 구조

```
tests/
├── conftest.py              # 공통 fixtures
├── test_config.py           # 정책 및 상수
├── test_normalizers.py      # 정규화 함수 (30+ 테스트)
├── test_validators.py       # 검증 로직 (15+ 테스트)
├── test_utils.py            # 유틸리티 (15+ 테스트)
├── test_preprocessor.py     # 전처리 엔진 (15+ 테스트)
├── test_schemas.py          # 스키마 검증
└── test_output_formatters.py # 출력 포맷팅
```

**총 테스트 개수: 85+**

---

## 실행 방법

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 실행
python -m src.main

# 3. 테스트
pytest tests/

# 4. 커버리지
pytest --cov=src tests/
```

---

## 출력 파일

**개별 파일당 7개 산출물:**
1. `{stem}_raw.txt` - 원문
2. `{stem}_normalized.txt` - 정규화 텍스트
3. `{stem}_preprocess_log.json` - 전처리 로그
4. `{stem}_candidates.json` - 후보 목록
5. `{stem}_extract_log.json` - 추출 로그
6. `{stem}_resolved.json` - 후보 선택 결과
7. `{stem}_parsed.json` - 최종 파싱 결과

**전체 요약:**
8. `summary.csv` - 전체 파일 요약

---

## 설계 원칙

1. **단계별 책임 분리** - 각 모듈은 명확한 단일 책임
2. **원문 보존** - 원본 데이터는 절대 변형하지 않음
3. **보수적 정규화** - 삭제보다 분리/보존 우선
4. **추적 가능성** - 모든 처리 과정 기록
5. **테스트 가능성** - 순수 함수 중심 설계
6. **확장 가능성** - 새로운 규칙/정책 추가 용이

---

## 의존성

**핵심:**
- Python 3.10+

**라이브러리:**
```
pydantic        # 데이터 검증
regex           # 정규식
python-dateutil # 날짜 파싱
pandas          # CSV 처리
```

**테스트:**
```
pytest          # 테스트 프레임워크
pytest-cov      # 커버리지
pytest-mock     # 모킹
```