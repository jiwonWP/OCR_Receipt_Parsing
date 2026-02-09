# 프로젝트 구조

## Sprint 5 리팩토링 완료 상태

```
ocr-data-pipeline/
│
├── docs/                         #  문서
│   ├── architecture.md           # 시스템 아키텍처 설계
│   ├── CLI_GUIDE.md              # CLI 사용 가이드
│   ├── data_audit.md             # OCR 샘플 전수 조사 결과
│   ├── OUTPUT_SPEC.md            # 출력 파일 명세서
│   ├── preprocess_spec.md        # 전처리 규칙 명세서
│   ├── PROJECT_STRUCTURE.md      # 프로젝트 구조 (본 파일)
│   ├── README_docs.md            # 문서 인덱스
│   ├── README_TEST.md            # 테스트 실행 가이드
│   └── sprint.md                 # Sprint 계획
│
├── logs/                         #  로그 파일 (자동 생성)
│   ├── pipeline_YYYYMMDD_HHMMSS.log
│   └── error_report.txt          # 에러 발생 시 생성
│
├── outputs/                      #  출력 파일 (자동 생성)
│   ├── sample_01_raw.txt
│   ├── sample_01_normalized.txt
│   ├── sample_01_preprocess_log.json
│   ├── sample_01_candidates.json
│   ├── sample_01_extract_log.json
│   ├── sample_01_resolved.json
│   ├── sample_01_parsed.json
│   ├── ... (sample_02, 03, 04 ...)
│   └── summary.csv               # 전체 요약
│
├── src/                          #  소스 코드
│   ├── __pycache__/              # Python 캐시 (자동 생성)
│   ├── __init__.py
│   ├── config.py                 #  설정/정책 중앙화
│   ├── error_handler.py          #  에러 핸들링
│   ├── extractor.py              #  후보 추출 엔진
│   ├── loader.py                 #  JSON 로더
│   ├── logger.py                 #  로깅 시스템
│   ├── main.py                   #  메인 실행 엔트리포인트
│   ├── normalizers.py            #  정규화 함수
│   ├── output_formatters.py      #  출력 포맷터
│   ├── patterns.py               #  정규식 패턴 (config 사용)
│   ├── pipeline.py               #  파이프라인 오케스트레이션
│   ├── preprocessor.py           #  전처리 엔진
│   ├── progress.py               #  진행 상황 표시
│   ├── resolver.py               #  후보 선택 알고리즘
│   ├── schema.py                 #  데이터 스키마 (Pydantic)
│   ├── schemas.py                #  출력 스키마 정의 (TypedDict)
│   ├── utils.py                  #  순수 함수 유틸리티
│   └── validators.py             #  검증 및 복구 로직
│
├── tests/                        #  테스트 코드
│   ├── __pycache__/              # Python 캐시 (자동 생성)
│   ├── __init__.py
│   ├── conftest.py               # pytest fixture
│   ├── README.md                 # 테스트 가이드
│   ├── test_config.py            # 🟢 설정 테스트 (10+)
│   ├── test_normalizers.py       # 🔥 정규화 테스트 (30+)
│   ├── test_output_formatters.py # 🟢 포맷터 테스트 (20+)
│   ├── test_preprocessor.py      # 🟡 전처리 테스트 (15+)
│   ├── test_schemas.py           # 🟢 스키마 테스트 (20+)
│   ├── test_utils.py             # 🟡 유틸리티 테스트 (15+)
│   └── test_validators.py        # 🔥 검증 테스트 (15+)
│
├── venv/                         #  가상 환경 (선택적)
│
├── .gitignore                    # Git 무시 파일
├── pytest.ini                    # pytest 설정
├── README.md                     # 프로젝트 루트 README
├── requirements.txt              # 패키지 의존성
└── requirements-test.txt         # 테스트 의존성
```

---

## 모듈 책임 분리

### 1. 핵심 파이프라인 모듈 (Pipeline Modules)

#### 1.1 `loader.py`
**책임**: OCR JSON 파일 로드 및 원문 보존

**주요 함수**:
- `load_ocr_json(filepath: str) -> RawDocument`
  - JSON 파일 읽기
  - `text` 필드 추출
  - 원문 보존 (변형 금지)

---

#### 1.2 `preprocessor.py`
**책임**: 원본 OCR 텍스트를 정규화하여 추출하기 좋은 형태로 변환

**주요 함수**:
- `preprocess(raw_text: str) -> PreprocessedDocument`
  - 11가지 전처리 규칙 순차 적용
  - 규칙 적용 이력 추적
  - 경고 메시지 기록

**전처리 규칙 순서** (`config.PreprocessRules.EXECUTION_ORDER`):
1. `collapsed_whitespace`: 연속 공백 제거
2. `normalized_punctuation_spacing`: 구두점 정규화
3. `normalized_character_visual_noise`: OCR 노이즈 보정 (I→1, O→0)
4. `standardized_labels`: 라벨 변형 통일
5. `converted_korean_time_to_colon_format`: 한글 시간 → 콜론 형식
6. `merged_split_numbers_before_kg`: kg 앞 분리된 숫자 병합
7. `split_date_suffix_to_doc_seq`: 날짜 suffix 분리
8. `preserved_ambiguous_date_tail_as_raw_tail`: 모호한 tail 보존
9. `split_vehicle_tail_keyword_as_category`: 차량 키워드 분리
10. `normalized_coordinates`: 좌표 정규화
11. `removed_symbol_only_lines`: 기호만 있는 줄 제거

**참고 문서**: [preprocess_spec.md](preprocess_spec.md)

---

#### 1.3 `extractor.py`
**책임**: 정규화된 텍스트에서 필드 후보들을 추출

**주요 함수**:
- `extract_candidates(normalized_text: str) -> ExtractedCandidates`
  - 3가지 추출 방법 통합
  - 후보별 신뢰도 점수 계산
  - 메타데이터 첨부

**추출 방법**:

| 방법 | 설명 | 신뢰도 점수 |
|------|------|------------|
| **Label-based** | 라벨 토큰 인식 (예: "총중량: 12,340 kg") | 85-100 |
| **Pattern-based** | 정규식 패턴 매칭 | 30-70 |
| **Heuristic** | 도메인 지식 활용 (예: 4자리 숫자 → 차량번호) | 10-40 |

**신뢰도 점수 규칙**:
- Label-based: 90점 기본 + 라벨 완전 일치 시 +10점
- Pattern-based: 50점 기본
- Heuristic: 30점 기본
- 라벨 토큰과 같은 줄에 있으면 +15점 보너스

---

#### 1.4 `resolver.py`
**책임**: 필드별로 최적의 후보 선택

**주요 함수**:
- `resolve_fields(candidates: List[Candidate]) -> ResolvedFields`
  - 필드별 최고 점수 후보 선택
  - Tie-breaking 규칙 적용
  - 선택 근거(evidence) 생성

**선택 규칙**:
1. **최고 점수 우선**: 신뢰도 점수가 가장 높은 후보
2. **동점 시**:
   - Label-based > Pattern-based > Heuristic
   - 같은 방법이면 줄 번호가 빠른 것 우선

---

#### 1.5 `normalizers.py`
**책임**: 원본 값을 표준 형식으로 변환

**주요 함수**:
- `normalize_date(raw: str) -> Tuple[str, Optional[str]]`
  - 다양한 구분자 처리 (-, ., /)
  - 연속된 숫자 파싱 (20260202)
  - YYYY-MM-DD 형식 출력
  
- `normalize_time(raw: str) -> Optional[str]`
  - HH:MM 형식 출력
  - 한글 시간 처리 (11시 33분)
  - 괄호 제거
  
- `normalize_weight_kg(raw: str) -> Optional[int]`
  - 쉼표, 공백, 괄호 제거
  - OCR 공백 분리 보정 (5 900 kg → 5,900)
  - kg 접미사 제거
  - **최대 10회 반복** (무한루프 방지)

---

#### 1.6 `validators.py`
**책임**: 비즈니스 규칙 검증 및 자동 복구

**주요 함수**:
- `validate_and_recover(...) -> ParseResult`
  - 필수 필드 검증
  - 중량 관계식 검증
  - 자동 복구 시도

**검증 규칙** (`config.ValidationPolicy`):

| 규칙 | 내용 |
|------|------|
| 필수 필드 | `date`, `vehicle_no` |
| 중량 범위 | 0 < 중량 ≤ 100,000 kg |
| 중량 관계 | 총중량 - 차중량 = 실중량 |
| 허용 오차 | max(10kg, 중량 × 2%) |

**자동 복구**:
1. **실중량 누락** → 총중량 - 차중량으로 계산
2. **중량 불일치** → 후보 풀에서 올바른 값 찾기

---

#### 1.7 `pipeline.py`
**책임**: 전체 파이프라인 오케스트레이션

**주요 함수**:
- `run_full_pipeline(raw_text: str, source: str) -> Dict`
  - Loader → Preprocessor → Extractor → Resolver → Validator 순차 실행
  - 각 단계별 산출물 생성
  - 에러 핸들링

---

### 2. 설정 및 지원 모듈 (Support Modules)

#### 2.1 `config.py`
**책임**: 모든 정책, 패턴, 상수 중앙 관리

**클래스**:
- `ValidationPolicy`: 검증 정책 (허용 오차, 필수 필드)
- `LabelTokens`: 라벨 토큰 정의
- `Patterns`: 정규식 패턴
- `PreprocessRules`: 전처리 규칙 순서
- `Constants`: 기타 상수 (반복 횟수, 인코딩 등)

**장점**:
- 정책 변경 시 config.py만 수정
- 매직넘버 제거
- 테스트 용이

---

#### 2.2 `schema.py`
**책임**: 데이터 타입 정의 (Pydantic)

**모델**:
- `RawDocument`
- `PreprocessedDocument`
- `Candidate`
- `ExtractedCandidates`
- `ResolvedFields`
- `ParseResult`

---

#### 2.3 `schemas.py`
**책임**: 출력 데이터 타입 정의 (TypedDict)

**스키마**:
- `PreprocessLogSchema`
- `CandidateSchema`
- `ResolvedOutputSchema`
- `ParsedOutputSchema`
- `CSVRowSchema`

---

#### 2.4 `output_formatters.py`
**책임**: 출력 파일 생성 및 포맷팅

**주요 함수**:
- `format_preprocess_log()`, `format_extract_log()`, ...
- `format_csv_row()`: 파싱 결과를 CSV 행으로 변환
- `write_summary_csv()`: 요약 CSV 생성

**파일명 규칙** (`FileNamingConvention`):
- `{stem}_raw.txt`
- `{stem}_normalized.txt`
- `{stem}_preprocess_log.json`
- `{stem}_candidates.json`
- `{stem}_extract_log.json`
- `{stem}_resolved.json`
- `{stem}_parsed.json`
- `summary.csv`

**참고 문서**: [OUTPUT_SPEC.md](OUTPUT_SPEC.md)

---

#### 2.5 `patterns.py`
**책임**: 정규식 패턴 (하위 호환성)

`config.Patterns`를 재노출하여 기존 코드와 호환성 유지.

---

#### 2.6 `utils.py`
**책임**: 순수 함수 유틸리티

**주요 함수**:
- `format_weight_kg()`: 중량 포맷팅
- `summarize_candidates()`: 후보 통계
- `compute_weight_relation_summary()`: 중량 관계식 요약
- `build_processing_summary()`: 전체 처리 요약
- `format_console_output()`: 콘솔 출력 포맷팅

**특징**:
- 순수 함수 (사이드 이펙트 없음)
- 테스트 용이
- I/O와 분리

---

#### 2.7 `logger.py`
**책임**: 로깅 시스템

**기능**:
- 파일 + 콘솔 로깅
- 컬러 출력
- 단계별 시간 측정
- 로그 레벨 관리

**로그 레벨**:
- **DEBUG**: 상세 디버깅 정보
- **INFO**: 정상 진행 상황
- **WARNING**: 경고 (처리는 계속)
- **ERROR**: 에러 (해당 파일 실패)
- **CRITICAL**: 치명적 에러

**참고 문서**: [CLI_GUIDE.md](CLI_GUIDE.md)

---

#### 2.8 `progress.py`
**책임**: 진행 상황 표시

**기능**:
- 프로그레스 바
- 상태 심볼 (✓, ✗, !, ▶)
- 테이블 출력

---

#### 2.9 `error_handler.py`
**책임**: 에러 핸들링 및 리포트

**기능**:
- 커스텀 예외 클래스
- 에러 정보 수집
- 에러 리포트 생성
- 복구 가능 여부 판단

**에러 타입**:
- `RecoverableError`: 복구 가능한 에러 (계속 진행)
- `CriticalError`: 치명적 에러 (처리 실패)

---

### 3. 실행 엔트리포인트

#### 3.1 `main.py`
**책임**: 파일 I/O 및 파이프라인 오케스트레이션

**주요 함수**:
- `process_single_file()`: 단일 파일 처리
- `main()`: 메인 실행 함수
  - 로거 초기화
  - 진행 상황 표시
  - CSV 생성
  - 에러 리포트

**실행 방법**:
```bash
# 파이썬 모듈로 실행 (권장)
python -m src.main

# 또는 직접 실행
python src/main.py
```

**참고 문서**: [CLI_GUIDE.md](CLI_GUIDE.md)

---

## 테스트 구조

### 테스트 커버리지

| 모듈 | 테스트 대상 | 테스트 개수 | 우선순위 |
|------|------------|------------|---------|
| `normalizers.py` | 정규화 함수 | 30+ | 🔥 High |
| `validators.py` | 검증/복구 로직 | 15+ | 🔥 High |
| `utils.py` | 유틸리티 함수 | 15+ | 🟡 Medium |
| `preprocessor.py` | 전처리 엔진 | 15+ | 🟡 Medium |
| `config.py` | 설정/정책 | 10+ | 🟢 Low |
| `schemas.py` | 스키마 | 20+ | 🟢 Low |
| `output_formatters.py` | 포맷터 | 20+ | 🟢 Low |

**총 테스트 개수: 125+**

### 테스트 실행

```bash
# 전체 테스트
pytest tests/

# 커버리지 포함
pytest --cov=src tests/

# 상세 출력
pytest -v tests/

# 특정 파일만
pytest tests/test_normalizers.py
```

**참고 문서**: [README_TEST.md](README_TEST.md)

---

## 데이터 흐름

```python
# 1. 로드
raw_text = load_ocr_json(input_file)
# → RawDocument(source_path, raw_text, meta)

# 2. 전처리
preprocessed = preprocess(raw_text)
# → PreprocessedDocument(normalized_text, applied_rules, warnings)

# 3. 추출
extracted = extract_candidates(preprocessed.normalized_text)
# → ExtractedCandidates(candidates, warnings)

# 4. 후보 선택
resolved = resolve_fields(extracted.candidates)
# → ResolvedFields(date_raw, time_raw, ..., evidence, warnings)

# 5. 정규화 및 검증
parsed = validate_and_recover(
    date=normalize_date(resolved.date_raw),
    time=normalize_time(resolved.time_raw),
    ...
)
# → ParseResult(date, time, ..., validation_errors, is_valid)
```

---

## 설계 원칙

### 1. 단일 책임 원칙 (SRP)
- 각 모듈은 하나의 명확한 책임만 가짐
- Preprocessor는 텍스트 정규화만
- Extractor는 후보 추출만
- Validator는 검증만

### 2. 관심사 분리 (SoC)
- 비즈니스 로직 vs 파일 I/O 분리
- 순수 함수 vs 사이드 이펙트 분리
- 정책(config) vs 구현(logic) 분리

### 3. 의존성 역전 (DIP)
- 모듈이 설정(config)에 의존
- 설정 변경 시 코드 수정 불필요

### 4. 테스트 가능성
- 순수 함수 중심 설계
- I/O 분리로 모킹 불필요
- 125+ 단위 테스트

---

## Sprint 5 성과

###  완료된 작업

#### Step 1: 패턴/라벨/정책 상수 중앙화
- [x] config.py 생성
- [x] ValidationPolicy 클래스
- [x] LabelTokens 클래스
- [x] Patterns 클래스
- [x] PreprocessRules 클래스
- [x] 관련 모듈 리팩토링

#### Step 2: main.py 로직 분리
- [x] utils.py 생성 (순수 함수)
- [x] main.py 리팩토링 (I/O 분리)
- [x] 테스트 가능성 개선

#### Step 3: 단위 테스트 작성
- [x] test_normalizers.py (30+ 테스트)
- [x] test_validators.py (15+ 테스트)
- [x] test_utils.py (15+ 테스트)
- [x] test_preprocessor.py (15+ 테스트)
- [x] test_config.py (10+ 테스트)
- [x] pytest 설정 및 구조화

#### Step 4: 결과 파일 출력 고정
- [x] schemas.py (출력 스키마)
- [x] output_formatters.py (포맷터)
- [x] test_schemas.py (20+ 테스트)
- [x] test_output_formatters.py (20+ 테스트)
- [x] OUTPUT_SPEC.md (명세서)
- [x] summary.csv 자동 생성

#### Step 5: CLI 실행 흐름 안정화
- [x] logger.py (로깅 시스템)
- [x] progress.py (진행 상황 표시)
- [x] error_handler.py (에러 핸들링)
- [x] main.py에 적용
- [x] CLI_GUIDE.md (사용 가이드)

###  완료 상태

모든 단계가 완료되었습니다.

---

## 확장 가능성

### 새로운 필드 추가
1. `config.LabelTokens`에 라벨 토큰 추가
2. `extractor.py`에 추출 로직 추가
3. `normalizers.py`에 정규화 함수 추가
4. `schemas.py`에 스키마 필드 추가

### 새로운 검증 규칙 추가
1. `config.ValidationPolicy`에 정책 추가
2. `validators.py`에 검증 로직 추가

### 새로운 전처리 규칙 추가
1. `preprocessor.py`에 규칙 함수 작성
2. `config.PreprocessRules.EXECUTION_ORDER`에 추가

**참고 문서**: [preprocess_spec.md](preprocess_spec.md)

---

## 성능 고려사항

### 현재 구현
- 단일 스레드 순차 처리
- 파일당 평균 처리 시간: ~0.5초
- 메모리 사용량: 파일당 ~10MB

### 향후 개선 방향
1. **병렬 처리**: 멀티프로세싱으로 파일 동시 처리
2. **캐싱**: 정규식 컴파일 결과 캐싱
3. **스트리밍**: 대용량 파일 청크 단위 처리
4. **배치 처리**: 데이터베이스 bulk insert

---

## 참고 문서

### 설계 및 명세
- [architecture.md](architecture.md): 시스템 아키텍처
- [preprocess_spec.md](preprocess_spec.md): 전처리 규칙 명세
- [OUTPUT_SPEC.md](OUTPUT_SPEC.md): 출력 파일 명세
- [data_audit.md](data_audit.md): OCR 샘플 전수 조사

### 실행 및 테스트
- [CLI_GUIDE.md](CLI_GUIDE.md): CLI 사용 가이드
- [README_TEST.md](README_TEST.md): 테스트 실행 가이드

### 계획
- [sprint.md](sprint.md): Sprint 계획
- [README_docs.md](README_docs.md): 문서 인덱스

---