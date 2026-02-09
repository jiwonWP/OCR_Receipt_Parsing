# OCR 데이터 처리 파이프라인 아키텍처

## 설계 목적

OCR 결과(JSON)의 `text` 필드를 입력으로 받아 날짜, 차량번호, 중량(총/차/실) 등 핵심 정보를 구조화된 데이터로 추출한다.

**OCR 입력 특성:**
- 형식적 일관성 없음
- 동일 정보가 다양한 표현으로 등장
- 정보 불완전/중복/노이즈 혼재

**설계 전략:**
단일 단계 처리가 아닌, **책임이 명확히 분리된 파이프라인 구조** 채택

---

## 파이프라인 구조

```
Loader → Preprocessor → Extractor → Resolver → Normalizer → Validator
```

각 단계는 **명확한 책임 범위**를 가지며, 앞 단계의 출력이 다음 단계의 입력이 된다.

---

## 1. Loader

**역할:** OCR JSON 파일을 읽고 원문을 보존

**책임:**
- 파일 I/O 및 JSON 파싱
- `text` 필드 추출
- **원문 텍스트를 변형하지 않고 그대로 보존**

**제외:**
- 공백 정리, 문자 치환, 의미 해석, 패턴 추출

**설계 근거:**
- OCR 원문은 규칙 개선, 오류 재현의 기준 데이터
- Loader에서 변형 시 디버깅과 검증 불가
- "읽기 전용 단계"로 유지

**출력:**
```python
RawDocument(
    source_path: str,
    raw_text: str,
    meta: Dict
)
```

---

## 2. Preprocessor

**역할:** OCR 텍스트의 **형태를 통일**하고 노이즈를 **분리/보존**

**핵심 원칙:**
1. **의미를 확정하지 않는다**
2. **삭제보다 분리/보존을 우선한다**
3. **과치환은 피한다**

**수행 작업:**
- 라벨 표준화: `날 짜` → `날짜`
- 구두점 공백 제거: `02 : 13` → `02:13`
- 한글 시간 정규화: `11시 33분` → `11:33`
- 중량 숫자 결합: `5 900 kg` → `5,900 kg` (kg 근처만)
- 날짜 suffix 분리: `2026-02-02-00004` → `2026-02-02 doc_seq:00004`
- 불명확 꼬리 보존: `2026-02-02 0016` → `2026-02-02 raw_tail:0016`
- 값 필드 오염 분리: `5405 입고` → `5405 구분:입고`

**제외:**
- 중량이 총/차/실인지 판단
- 날짜/시간 확정
- 데이터 유효성 판단

**설계 근거:**
- 전처리 단계에서 의미 확정 시 오탐 위험
- **Extractor가 일관된 입력을 받도록 돕는 역할**에 집중

**출력:**
```python
PreprocessedDocument(
    raw_text: str,
    normalized_text: str,
    applied_rules: List[str],
    warnings: List[str]
)
```

---

## 3. Extractor

**역할:** 정규화된 텍스트에서 **구조화된 필드 후보**를 추출

**추출 대상:**
- 날짜, 시간, 차량번호
- 총중량, 차중량, 실중량
- (선택) 구분, 계량횟수, 좌표

**추출 전략:**

### 3.1 라벨 기반 추출 (우선)
```python
# 중량 예시
for field, tokens in [("gross_weight_kg", ["총중량", "총 중량"]), ...]:
    if token in line:
        value = extract_weight_after_token(line, token)
        add_candidate(field, value, method="label", score=90)
```

**특징:**
- 라벨 토큰 발견 시 같은 줄/다음 줄에서 값 추출
- 라벨이 있으면 전형 패턴 불일치해도 후보로 수집
- 높은 신뢰도 점수 (85-95)

### 3.2 패턴 기반 추출 (fallback)
```python
# 라벨 없을 때 정규식 패턴으로 추출
for match in DATE_PATTERN.finditer(line):
    add_candidate("date", match.group(0), method="pattern", score=50)
```

**특징:**
- 라벨 누락/순서 변경 대비
- 낮은 신뢰도 점수 (20-50)
- 역할 미확정 중량은 `weight_kg`로 분류

**설계 원칙:**
- **값을 확정하지 않고 후보 형태로 수집**
- 불확실성을 `meta` 데이터로 명시
- 최종 확정은 Resolver/Validator에서 판단

**제외:**
- 데이터 정상/비정상 판정
- 범위 기반 유효성 판단

**출력:**
```python
ExtractedCandidates(
    raw_text: str,
    normalized_text: str,
    candidates: List[Candidate],
    warnings: List[str]
)

Candidate(
    field: str,              
    value_raw: str,
    source_line: str,
    method: str,             
    score: int,             
    meta: Dict              
)
```

---

## 4. Resolver

**역할:** 후보들 중 **최적 후보를 선택**

**선택 정책:**
1. **method 우선순위:** `label` > `pattern`
2. **score 내림차순**
3. **line_index 오름차순** (앞쪽 우선)

**특수 처리:**
- 라벨 토큰이 같은 줄에 있으면 가산점(+15)
- 동점 시 `ambiguous_candidate` 경고 생성

**출력:**
```python
ResolvedFields(
    date_raw: Optional[str],
    time_raw: Optional[str],
    vehicle_no_raw: Optional[str],
    gross_weight_raw: Optional[str],
    tare_weight_raw: Optional[str],
    net_weight_raw: Optional[str],
    evidence: Dict,      
    warnings: List[str]
)
```

---

## 5. Normalizer

**역할:** 문자열을 **의미 있는 타입**으로 변환

**정규화 함수:**

```python
normalize_weight_kg(raw: str) -> Optional[int]

normalize_time(raw: str) -> Optional[str]

normalize_date(raw: str) -> Tuple[Optional[str], Optional[str]]

```

**특징:**
- 실패 시 `None` 반환 + 경고 생성
- 원본 문자열은 보존 (evidence에 기록)

---

## 6. Validator

**역할:** 논리적 **타당성 검증** 및 **자동 복구**

**검증 규칙:**
1. **필수 필드:** `date`, `vehicle_no`
2. **중량 범위:** 음수 불가, 100톤 초과 불가
3. **중량 관계:** 
   - `총중량 >= 차중량`
   - `실중량 ≈ 총중량 - 차중량` (허용 오차: max(10kg, 2%))

**복구 정책:**

### 6.1 실중량 자동 계산
```python
if gross and tare and not net:
    net = gross - tare
    imputation_notes.append("imputed:net_weight={net}")
```

### 6.2 중량 불일치 복구
```python
# 후보 풀에서 올바른 조합 탐색
if weight_mismatch:
    new_gross, new_tare, new_net = try_recover_by_candidates(
        gross, tare, net, weight_candidates_kg
    )
```

**복구 우선순위:**
1. gross, tare 고정 → net 후보로 맞추기
2. gross, net 고정 → tare 후보로 맞추기
3. tare, net 고정 → gross 후보로 맞추기
4. gross 고정 → (tare, net) 쌍 탐색
5. net 고정 → (gross, tare) 쌍 탐색
6. tare 고정 → (gross, net) 쌍 탐색

**설계 근거:**
- "실패를 줄이되, 근거 없이 확정하지 않는다"
- 복구는 `imputation_notes`에 명시적 기록

**출력:**
```python
ValidationResult(
    is_valid: bool,
    net_weight_kg: Optional[int],
    validation_errors: List[str],
    imputation_notes: List[str]
)
```

---

## 단계 분리의 핵심 철학

### 1. "의미 확정은 최대한 뒤로 미룬다"
- OCR 입력은 불완전
- 애매한 값을 초기에 확정하면 오탐 되돌리기 어려움
- 따라서:
  - **Preprocessor:** 분리/보존
  - **Extractor:** 후보 추출
  - **Resolver:** 선택
  - **Validator:** 확정/거부

### 2. "삭제보다 기록"
- `raw_tail`, `doc_seq`, `warnings` 남김
- 실패 케이스도 규칙 개선의 근거 데이터

### 3. "추적 가능성"
- 모든 처리 과정 기록
  - `applied_rules`: 적용된 전처리 규칙
  - `warnings`: 애매한 상황 경고
  - `evidence`: 선택 근거
  - `imputation_notes`: 복구 이력

### 4. "테스트 가능성"
- 각 단계는 순수 함수 중심
- 입력만으로 출력 결정
- 부작용(side effect) 최소화

---

## 에러 처리 전략

### ErrorHandler
```python
class ErrorHandler:
    - handle_error(error, context, recoverable, recovery_action)
    - get_error_summary() → Dict
    - has_critical_errors() → bool
    - generate_error_report() → str
```

**에러 분류:**
- **복구 가능:** 경고 로그, 처리 계속
- **치명적:** 에러 기록, 해당 파일 실패 처리

**유틸리티:**
- `safe_execute()`: 기본값 반환
- `retry_on_error()`: 재시도 로직

---

## 로깅 및 진행 표시

### Logger
- 컬러 콘솔 출력
- 파일 로깅 (타임스탬프 포함)
- 컨텍스트 기반 로깅 (`log_step`)

### Progress
- 프로그레스 바
- 상태 심볼 (✓/✗/!)
- 섹션 헤더

---

## 출력 시스템

### Output Formatters
각 파일당 **7개 산출물** 생성:
1. `_raw.txt` - 원문
2. `_normalized.txt` - 정규화 텍스트
3. `_preprocess_log.json` - 전처리 로그
4. `_candidates.json` - 후보 목록
5. `_extract_log.json` - 추출 로그
6. `_resolved.json` - 후보 선택 결과
7. `_parsed.json` - 최종 파싱 결과

**전체 요약:**
8. `summary.csv` - 전체 파일 요약

---

## 데이터 흐름 예시

```
[입력] sample_01.json
  └─> {"text": "계량일자: 2026-02-02 0016\n05:26:18 12,480 kg\n..."}

[Loader]
  └─> RawDocument(raw_text="계량일자: 2026-02-02 0016\n...")

[Preprocessor]
  └─> PreprocessedDocument(
        normalized_text="날짜: 2026-02-02 raw_tail:0016\n05:26:18 12,480 kg\n...",
        applied_rules=["standardized_labels", "preserved_ambiguous_tail", ...],
        warnings=["found_ambiguous_date_tail"]
      )

[Extractor]
  └─> ExtractedCandidates(
        candidates=[
          Candidate(field="date", value_raw="2026-02-02", method="label", score=90),
          Candidate(field="gross_weight_kg", value_raw="12,480 kg", method="pattern", score=50),
          ...
        ]
      )

[Resolver]
  └─> ResolvedFields(
        date_raw="2026-02-02",
        gross_weight_raw="12,480 kg",
        tare_weight_raw="7,470 kg",
        net_weight_raw="5,010 kg"
      )

[Normalizer]
  └─> date="2026-02-02"
      gross_weight_kg=12480
      tare_weight_kg=7470
      net_weight_kg=5010

[Validator]
  └─> ValidationResult(
        is_valid=True,
        net_weight_kg=5010,
        validation_errors=[],
        imputation_notes=[]
      )

[Output]
  └─> sample_01_parsed.json, summary.csv
```

---

## 확장성

### 새 전처리 규칙 추가
1. `preprocessor.py`에 규칙 함수 추가
2. `config.PreprocessRules.EXECUTION_ORDER`에 등록
3. 테스트 작성

### 새 필드 추가
1. `LabelTokens`에 토큰 추가
2. `extractor.py`에 추출 로직 추가
3. `schema.py`에 필드 추가
4. 테스트 작성

### 새 검증 규칙 추가
1. `validators.py`에 검증 로직 추가
2. 에러 코드 정의
3. 테스트 작성

---

## 설계 의사결정 요약

| 의사결정 | 근거 |
|---------|------|
| 파이프라인 분리 | 책임 명확화, 테스트 용이성 |
| 원문 보존 | 디버깅, 규칙 개선 근거 |
| 후보 기반 추출 | 의미 확정 지연, 오탐 방지 |
| 분리/보존 우선 | 정보 손실 방지 |
| 명시적 메타데이터 | 추적 가능성, 신뢰도 표현 |
| 자동 복구 | Robustness 향상 (단, 기록 필수) |

---