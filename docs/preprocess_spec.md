# Preprocess Spec — Loader → Preprocessor 정규화 함수 명세
샘플 4개 JSON 기반으로 작성

## 0. 목적과 범위

본 문서는 OCR 결과(JSON)의 `text`를 대상으로 하는 **Loader → Preprocessor** 단계의 정규화(전처리) 함수 명세서이다.

- 목적
  - Extractor가 안정적으로 라벨/숫자/시간 패턴을 인식할 수 있도록 **입력 텍스트의 형태를 통일**한다.
  - OCR 특유의 불확실성(불명확한 꼬리 숫자, 날짜 suffix 등)은 **삭제하지 않고 분리/보존**하여 데이터 손실을 방지한다.
- 범위
  - Loader: JSON 로드 및 원문 보존(정규화 금지)
  - Preprocessor: 형태 통일, 분리/보존, 최소한의 노이즈 제거
- 제외(Preprocessor가 하지 않는 것)
  - 총/차/실 중량 역할 확정
  - 데이터 유효성 판정(Validator 책임)
  - 결과 저장(Exporter 책임)

---

## 1. 핵심 설계 원칙

### 1) Loader는 원문을 변형하지 않는다
- 이유: 원문은 디버깅/재현/규칙 개선의 근거 데이터이며, Loader에서 변형되면 검증이 어렵다.
- 결과: Loader는 **읽기만 수행**하고 `raw_text`를 그대로 보관한다.

### 2) Preprocessor는 “보수적 정규화”를 지향한다
- 이유: OCR 텍스트에 대해 전역 치환을 과도하게 수행하면 날짜/문서번호/기타 필드가 손상될 수 있다.
- 전략:
  - 숫자 결합은 `kg` 근처에서만 수행(과치환 방지)
  - 날짜 suffix는 삭제가 아니라 분리/보존
  - 애매한 꼬리 숫자는 raw_tail로 보존

### 3) 의미 확정은 최대한 뒤로 미룬다
- Preprocessor는 “형태 통일”까지만 수행한다.
- 어떤 중량이 총/차인지 판단은 Extractor + Validator에서 정합성(총-차=실)로 확정한다.

---

## 2. 데이터 모델

### 2.1 RawDocument
- `source_path: str`
- `raw_text: str`  # 원문
- `meta: dict`     

### 2.2 PreprocessedDocument
- `raw_text: str`
- `normalized_text: str`
- `applied_rules: list[str]`  # 적용된 정규화 규칙 이름 기록
- `warnings: list[str]`       # 애매한 패턴/주의 요소 기록(예시: raw_tail 발견)

## 2.3 ExtractionMetadata (추적 가능성/감사 로그용 메타데이터)

PreprocessedDocument 수준의 applied_rules/warnings는 "문서 전체가 어떤 전처리를 거쳤는지"는 보여주지만,
본 프로젝트가 목표로 하는 추적 가능성은
**"특정 필드(예: 총중량, 실중량)가 어떤 근거/전략으로 결정되었는지"**까지 설명 가능해야 한다.

따라서 Extractor 단계에서 모든 추출 결과는 아래 메타데이터를 함께 보유한다.

### ExtractionMetadata (필드 단위)
- `field: str`
  - 예: `date`, `vehicle_no`, `gross_weight`, `tare_weight`, `net_weight`, `category`, `weigh_count`, `coordinates`

- `strategy_used: str`
  - 값: `label_match` | `pattern_fallback` | `computed_imputation`
  - 의미:
    - `label_match`: 라벨 기반(예: "총중량:", "실중량:")으로 직접 매칭
    - `pattern_fallback`: 라벨이 없거나 깨져서 패턴/휴리스틱으로 보완 추출
    - `computed_imputation`: 다른 필드를 기반으로 계산해 생성(Validator/Recovery 포함)

- `raw_match: str | None`
  - 정규식/패턴에 실제로 걸린 원문 조각(가능하면 원문 그대로)
  - 예: `"05:26:18 12,480 kg"`, `"총중량: 02:07 13 460 kg"`

- `normalized_match: str | None`
  - 전처리 후 기반이 된 문자열 조각(있으면 기록)

- `source_line_index: int | None`
  - 텍스트 라인 기반 처리 시, 근거가 된 라인 번호(0-based 권장)

- `confidence: float | None`
  - 자체 휴리스틱 confidence(0~1). OCR confidence가 없다면 추출 근거 강도라도 기록

- `is_imputed: bool`
  - 값이 계산/복구로 채워졌는지 여부

- `notes: str | None`
  - 특이 케이스(예: raw_tail 존재, doc_seq 존재, 라벨 손상 등) 자유 기록

### ExtractedField
- `value: Any`
- `metadata: ExtractionMetadata`

> 이 구조를 통해 "이 값이 왜 이렇게 나왔는지"를 로그/리포트에서 설명 가능해진다.

---

#### Fuzzy Keyword Map (샘플/관측 기반 오타 보정 사전)

OCR에서 관측된 "치명적 오타/유사 형태"는 상수 맵으로 명시적으로 관리한다.
본 맵은 전역 치환이 아니라, **라벨/키워드 탐지 맥락에서만** 적용하는 것을 원칙으로 한다.

| observed (OCR) | normalized | 비고 |
|---|---|---|
| 계그표 | 계량표 | 문서 유형 키워드 |
| 곰욕환경 | 공육환경 | 도메인 텍스트(예시) |
| 품종명랑 | 품명 | 라벨/항목명 오인식 |
| 날 짜 | 날짜 | 라벨 내부 공백/오인식 |
| 실 중 량 | 실중량 | 라벨 내부 공백/오인식 |
| 총 중 량 | 총중량 | 라벨 내부 공백/오인식 |
| 차 량 번 호 | 차량번호 | 라벨 내부 공백/오인식 |

---

## 3. 처리 파이프라인(Preprocessor 실행 순서)

>앞 단계에서 형태를 정리할수록 뒤 단계의 매칭/치환이 안정적이다.

1. `normalize_whitespace`
2. `normalize_punctuation_spacing`
3. `normalize_character_visual_noise`
4. `normalize_label_variants`
5. `normalize_korean_time_format`
6. `normalize_number_grouping_before_unit`
7. `normalize_date_suffix`
8. `normalize_datetime_trailing_garbage`
9. `normalize_vehicle_value_noise`
10. `normalize_coordinates`
11. `normalize_line_noise`

---

## 4. 함수 명세(정의 / 입력-출력 / 규칙 / 예시 / 로그)

아래 모든 함수는 기본적으로 `text: str -> str` 형태를 가정한다.  
(필요 시 line 기반 처리로 확장 가능)

---

### 4.1 `normalize_whitespace(text) -> str`

#### 목적
- OCR 텍스트에서 불규칙 공백/탭/줄 끝 공백을 정리하여 후속 매칭을 안정화한다.

#### 규칙
- 탭/연속 공백을 단일 공백으로 축소
- 각 라인의 좌우 공백 trim
- 줄 구조(개행)는 유지

#### 예시 (샘플 기반)
- Before: `총 중 량 : 11시 33분 14,080 kg `  
  After:  `총 중 량 : 11시 33분 14,080 kg`

#### applied_rules
- `collapsed_whitespace`

---

### 4.2 `normalize_punctuation_spacing(text) -> str`

#### 목적
- 구두점 주변 공백 때문에 시간/좌표/괄호 패턴이 깨지는 문제를 방지한다.

#### 규칙
- `\s*:\s*` → `:`  (시간)
- `\s*,\s*` → `,`  (좌표/숫자)
- `\s*\(\s*` → `(`, `\s*\)\s*` → `)`  (괄호)

#### 예시 (샘플 기반)
- Before: `차중량: 02 : 13 7 560 kg`  
  After:  `차중량: 02:13 7 560 kg`
- Before: `37.718114, 126.844940`  
  After:  `37.718114,126.844940`

#### 주의
- 하이픈(`-`)은 날짜 suffix와 결합되어 등장하므로 여기서 임의로 붙이지 않는다.

#### applied_rules
- `normalized_punctuation_spacing`

---
### 4.3 `normalize_character_visual_noise(text) -> str`

#### 목적
- OCR에서 시각적으로 유사한 문자 혼동(O↔0, I/l↔1 등)을 보정하여
  날짜/시간/중량과 같은 숫자 중심 필드의 파싱 실패를 줄인다.

#### 적용 원칙(보수적)
- 전역 치환은 위험하므로, **숫자가 올 것으로 예상되는 맥락**에서만 치환한다.
  - 날짜: `YYYY-MM-DD` 주변
  - 시간: `HH:MM` 또는 `HH:MM:SS` 주변
  - 중량: `kg` 주변 숫자 토큰
  - 계량횟수: `계량횟수` 라벨 근처 숫자 토큰

#### 규칙(예: 정책)
- 숫자 토큰 내부에서만 치환:
  - `O`/`o` → `0`
  - `I`/`l` → `1`
- 숫자 토큰의 정의:
  - `[\dOlI,.\s]+` 같은 후보를 잡되,
  - 최종적으로 숫자/구분자/단위 패턴을 만족할 때만 확정 치환

#### 예시
- Before: `실중량: 5,O10 kg`
- After:  `실중량: 5,010 kg`
- Before: `날짜: 2026-O2-O2`
- After:  `날짜: 2026-02-02`

#### warnings
- `found_visual_noise_correction`

#### applied_rules
- `normalized_character_visual_noise`

---

### 4.4 `normalize_label_variants(text) -> str`

#### 목적
- 라벨 표기 불일치/라벨 내부 공백 삽입을 흡수하여 “표준 라벨”로 통일한다.

#### 표준 라벨
- 날짜: `날짜`
- 차량번호: `차량번호`
- 총중량: `총중량`
- 차중량(공차중량 포함): `차중량` (또는 정책적으로 `공차중량`)
- 실중량: `실중량`
- 구분: `구분`
- 계량횟수: `계량횟수`

#### 치환 규칙
- `날\s*짜` / `계량\s*일자` / `일\s*시` → `날짜`
- `차량\s*번호` / `차번호` / `차량\s*No\.?` → `차량번호`
- `총\s*중\s*량` → `총중량`
- `공차\s*중량` / `차\s*중량` → `차중량`
- `실\s*중\s*량` → `실중량`
- `구\s*분` → `구분`

#### 예시 (샘플 기반)
- Before: `날 짜: 2026-02-02-00004`  
  After:  `날짜: 2026-02-02-00004`
- Before: `차량 No. 0580`  
  After:  `차량번호 0580`
- Before: `실 중 량: 5,010 kg`  
  After:  `실중량: 5,010 kg`

#### 주의
- 과치환 방지를 위해 라인 단위 처리 또는 `:` 주변 맥락을 활용하는 방식이 안전하다.

#### applied_rules
- `standardized_labels`

---

### 4.5 `normalize_korean_time_format(text) -> str`

#### 목적
- 한글 시간 표현을 `HH:MM` 형태로 통일한다.

#### 규칙
- `(\d{1,2})\s*시\s*(\d{1,2})\s*분` → `HH:MM`
- 1자리 분은 2자리로 패딩
  - 예: `11시 3분` → `11:03`

#### 예시 (샘플 기반)
- Before: `총 중 량 : 11시 33분 14,080 kg`  
  After:  `총 중 량 : 11:33 14,080 kg`

#### applied_rules
- `converted_korean_time_to_colon_format`

---

### 4.6 `normalize_number_grouping_before_unit(text) -> str`

#### 목적
- OCR에서 천 단위 구분이 공백으로 인식되는 문제를 보정하여 중량 파싱 실패를 방지한다.

#### 핵심 전략
- “모든 숫자 공백 결합”은 위험하므로,
  **단위(`kg`) 바로 앞 숫자에 한정해서 결합**한다.

#### 규칙(예시)
- `(\d{1,3})\s+(\d{3})\s*(kg)` → `\1,\2 kg`
- 필요 시 반복 적용(예: `1 234 567 kg` 형태까지 확장 가능)

#### 예시 (샘플 기반)
- Before: `실중량: 5 900 kg`  
  After:  `실중량: 5,900 kg`
- Before: `총중량: 02:07 13 460 kg`  
  After:  `총중량: 02:07 13,460 kg`

#### applied_rules
- `merged_split_numbers_before_kg`

---

### 4.7 `normalize_date_suffix(text) -> str`

#### 목적
- 날짜가 `YYYY-MM-DD-<digits>` 형태로 결합된 경우, 날짜와 suffix(문서번호/시퀀스)를 분리하여 보존한다.

#### 규칙
- `(\d{4}-\d{2}-\d{2})-(\d+)` → `\1 doc_seq:\2`

#### 예시 (샘플 기반)
- Before: `날짜: 2026-02-02-00004`  
  After:  `날짜: 2026-02-02 doc_seq:00004`

#### 설계 근거
- 날짜 표준 형식과 불일치
- 삭제하면 정보 손실(문서 식별자 가능)

#### warnings
- `found_date_suffix_doc_seq`

#### applied_rules
- `split_date_suffix_to_doc_seq`

---

### 4.8 `normalize_datetime_trailing_garbage(text) -> str`

#### 목적
- 날짜 뒤에 붙은 콜론 없는 숫자 꼬리(`0016`, `5` 등)를 시간으로 단정하지 않고 분리/보존한다.

#### 규칙(정책)
- 날짜 뒤에 공백 + `digits-only(1~4자리)`가 붙는 경우:
  - `(\d{4}-\d{2}-\d{2})\s+(\d{1,4})(?!:)` → `\1 raw_tail:\2`
- 단, 정상 시간(콜론 포함)은 대상에서 제외해야 함
  - 예: `2026-02-02 05:37:55`는 변경 금지

#### 예시 (샘플 기반)
- Before: `날짜: 2026-02-02 0016`  
  After:  `날짜: 2026-02-02 raw_tail:0016`
- Before: `날짜: 2026-02-01 5`  
  After:  `날짜: 2026-02-01 raw_tail:5`

#### 설계 근거
- OCR 불완전 인식 가능성이 높음
- 초기에 시간으로 확정하면 오탐 위험

#### warnings
- `found_ambiguous_date_tail`

#### applied_rules
- `preserved_ambiguous_date_tail_as_raw_tail`

---

### 4.9 `normalize_vehicle_value_noise(text) -> str`

#### 목적
- 차량번호 값에 `입고/출고` 같은 구분 키워드가 결합되는 “값 오염”을 분리한다.

#### 규칙(예시 정책)
- `차량번호:` 라인에서 값 뒤에 `입고|출고`가 있으면 구분 토큰을 별도로 삽입
  - `차량번호:\s*(\S+)\s*(입고|출고)` → `차량번호: \1 구분:\2`

#### 예시 (샘플 기반)
- Before: `차량 번호: 5405 입고`  
  After:  `차량번호: 5405 구분:입고`

#### 주의
- 실제 차량번호 형식 확정(예: `80구8713`)은 Extractor 책임
- Preprocessor는 “키워드 분리”까지만 수행

#### applied_rules
- `split_vehicle_tail_keyword_as_category`

---

### 4.10 `normalize_coordinates(text) -> str`

#### 목적
- 좌표를 `lat,lon` 형태로 통일해 추출 패턴을 단순화한다.

#### 규칙
- `(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)` → `\1,\2`
- 콤마 주변 공백 제거는 4.2에서 이미 처리되므로 보조적으로 적용

#### 예시 (샘플 기반)
- Before: `37.105317, 127.375673`  
  After:  `37.105317,127.375673`

#### applied_rules
- `normalized_coordinates`

---

### 4.11 `normalize_line_noise(text) -> str`

#### 목적
- 의미 없는 “기호-only 라인”을 제거하여 핵심 라벨 라인의 밀도를 높인다.

#### 규칙(예시)
- 라인이 다음 조건이면 삭제:
  - 공백 제거 후 길이가 0
  - 공백 제거 후 `·` 또는 `,` 또는 반복 특수문자만 존재
- 주소/전화 등 의미 있는 텍스트는 삭제하지 않는다(데이터 손실 방지)

#### 예시 (샘플 기반)
- Before: `·`  
  After:  (삭제)
- Before: `,`  
  After:  (삭제)

#### applied_rules
- `removed_symbol_only_lines`


---

## 5. Sprint1 기준 테스트 케이스

> Sprint2 구현 시 아래 항목을 기준으로 전처리 결과를 검증한다.

### 5.1 해야 하는 변환(필수)
- `02 : 13` → `02:13`
- `11시 33분` → `11:33`
- `5 900 kg` → `5,900 kg` (단, kg 앞에서만)
- `날 짜` → `날짜`
- `차량 No.` → `차량번호`
- `2026-02-02-00004` → `2026-02-02 doc_seq:00004`
- `2026-02-02 0016` → `2026-02-02 raw_tail:0016`
- `차량 번호: 5405 입고` → `차량번호: 5405 구분:입고`
- `37.718114, 126.844940` → `37.718114,126.844940`
- 기호-only 라인(`·`, `,`) 삭제

### 5.2 하면 안 되는 변환(금지 / 과치환 방지)
- 정상 시간 `2026-02-02 05:37:55`를 raw_tail로 바꾸면 안 됨
- 날짜 suffix `-00004`를 삭제하면 안 됨(분리+보존)
- 모든 숫자 공백을 무작정 결합하면 안 됨(날짜/문서번호 오염 가능)

---

## 6. 적용 로그(applied_rules / warnings) 기록 정책

### applied_rules
- 전처리 함수가 실제로 텍스트를 변경했다면, 해당 규칙명을 1회 이상 기록한다.
- 예시:
  - `collapsed_whitespace`
  - `normalized_punctuation_spacing`
  - `standardized_labels`
  - `converted_korean_time_to_colon_format`
  - `merged_split_numbers_before_kg`
  - `split_date_suffix_to_doc_seq`
  - `preserved_ambiguous_date_tail_as_raw_tail`
  - `split_vehicle_tail_keyword_as_category`
  - `normalized_coordinates`
  - `removed_symbol_only_lines`

### warnings
- 변환을 수행했거나 변환 후보를 발견했지만 “애매함”이 남는 경우 기록한다.
- 예시:
  - `found_ambiguous_date_tail`
  - `found_date_suffix_doc_seq`

---