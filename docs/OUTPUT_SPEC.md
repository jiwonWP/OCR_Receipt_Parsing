# 출력 파일 명세서

## 개요

OCR 데이터 처리 파이프라인은 각 입력 파일(`sample_XX.json`)에 대해 **7개의 산출물**과 **1개의 요약 CSV**를 생성합니다.

---

## 파일명 규칙

### 개별 파일 산출물

| 산출물 | 파일명 패턴 | 예시 |
|--------|------------|------|
| 원문 텍스트 | `{stem}_raw.txt` | `sample_01_raw.txt` |
| 정규화 텍스트 | `{stem}_normalized.txt` | `sample_01_normalized.txt` |
| 전처리 로그 | `{stem}_preprocess_log.json` | `sample_01_preprocess_log.json` |
| 후보 목록 | `{stem}_candidates.json` | `sample_01_candidates.json` |
| 추출 로그 | `{stem}_extract_log.json` | `sample_01_extract_log.json` |
| 후보 선택 결과 | `{stem}_resolved.json` | `sample_01_resolved.json` |
| 최종 파싱 결과 | `{stem}_parsed.json` | `sample_01_parsed.json` |

### 전체 요약

| 산출물 | 파일명 | 설명 |
|--------|--------|------|
| 요약 CSV | `summary.csv` | 전체 파일의 최종 결과 요약 |

---

## JSON 스키마

### 1. 전처리 로그 (`*_preprocess_log.json`)

```json
{
  "source": "sample_01.json",
  "applied_rules": [
    "remove_empty_lines",
    "normalize_whitespace",
    "normalize_parentheses"
  ],
  "warnings": [],
  "raw_line_count": 45,
  "normalized_line_count": 38
}
```

**필드 설명:**
- `source`: 원본 파일명
- `applied_rules`: 적용된 전처리 규칙 목록
- `warnings`: 전처리 중 발생한 경고
- `raw_line_count`: 원문 줄 수
- `normalized_line_count`: 정규화 후 줄 수

---

### 2. 후보 목록 (`*_candidates.json`)

```json
{
  "source": "sample_01.json",
  "candidates": [
    {
      "field": "date",
      "value_raw": "2026-02-02",
      "value_normalized": "2026-02-02",
      "method": "label",
      "score": 90,
      "confidence": "high",
      "source_line": "날짜: 2026-02-02",
      "meta": {
        "line_index": 3,
        "label_token": "날짜"
      }
    },
    {
      "field": "gross_weight_kg",
      "value_raw": "12,480 kg",
      "value_normalized": 12480,
      "method": "pattern",
      "score": 50,
      "confidence": "medium",
      "source_line": "총중량 12,480 kg",
      "meta": {
        "line_index": 15
      }
    }
  ]
}
```

**필드 설명:**
- `field`: 필드 종류 (`date`, `time`, `vehicle_no`, `gross_weight_kg`, 등)
- `value_raw`: 추출된 원본 값
- `value_normalized`: 정규화된 값 (타입 변환 포함)
- `method`: 추출 방법 (`label`, `pattern`, `heuristic`)
- `score`: 신뢰도 점수 (0-100)
- `confidence`: 신뢰도 레벨 (`high`, `medium`, `low`)
- `source_line`: 값이 발견된 원본 줄
- `meta`: 메타데이터 (줄 번호, 라벨 토큰 등)

---

### 3. 추출 로그 (`*_extract_log.json`)

```json
{
  "source": "sample_01.json",
  "warnings": [],
  "candidate_summary": {
    "total": 25,
    "by_field": {
      "date": 3,
      "time": 2,
      "vehicle_no": 1,
      "gross_weight_kg": 7,
      "tare_weight_kg": 6,
      "net_weight_kg": 6
    },
    "by_method": {
      "label": 5,
      "pattern": 15,
      "heuristic": 5
    }
  }
}
```

**필드 설명:**
- `warnings`: 추출 중 발생한 경고
- `candidate_summary.total`: 총 후보 개수
- `candidate_summary.by_field`: 필드별 후보 개수
- `candidate_summary.by_method`: 추출 방법별 후보 개수

---

### 4. 후보 선택 결과 (`*_resolved.json`)

```json
{
  "source": "sample_01.json",
  "resolved_fields": {
    "date_raw": "2026-02-02",
    "time_raw": "09:12",
    "vehicle_no_raw": "8713",
    "gross_weight_raw": "12,480 kg",
    "tare_weight_raw": "7,470 kg",
    "net_weight_raw": "5,010 kg"
  },
  "evidence": {
    "date": {
      "field": "date",
      "selected_value": "2026-02-02",
      "selected_method": "label",
      "selected_score": 90,
      "runner_up_value": "2026-02-03",
      "runner_up_score": 50,
      "score_gap": 40
    }
  },
  "warnings": []
}
```

**필드 설명:**
- `resolved_fields`: 각 필드별로 선택된 원본 값
- `evidence`: 선택 근거 (최고점 후보 vs 차순위 후보)
- `warnings`: 선택 중 발생한 경고

---

### 5. 최종 파싱 결과 (`*_parsed.json`)

```json
{
  "source": "sample_01.json",
  "date": "2026-02-02",
  "time": "09:12",
  "vehicle_no": "8713",
  "gross_weight_kg": 12480,
  "tare_weight_kg": 7470,
  "net_weight_kg": 5010,
  "parse_warnings": [],
  "validation_errors": [],
  "imputation_notes": [],
  "is_valid": true
}
```

**필드 설명:**
- `date`: 정규화된 날짜 (YYYY-MM-DD)
- `time`: 정규화된 시간 (HH:MM)
- `vehicle_no`: 정규화된 차량번호
- `gross_weight_kg`: 총중량 (정수, kg 단위)
- `tare_weight_kg`: 차중량 (정수, kg 단위)
- `net_weight_kg`: 실중량 (정수, kg 단위)
- `parse_warnings`: 파싱 중 발생한 경고
- `validation_errors`: 검증 오류 목록
- `imputation_notes`: 자동 복구/계산 기록
- `is_valid`: 검증 통과 여부 (`true` / `false`)

---

## CSV 형식 (`summary.csv`)

### 컬럼 정의

| 컬럼명 | 타입 | 설명 | 예시 |
|--------|------|------|------|
| `filename` | string | 원본 파일명 | `sample_01.json` |
| `date` | string | 날짜 | `2026-02-02` |
| `time` | string | 시간 | `09:12` |
| `vehicle_no` | string | 차량번호 | `8713` |
| `gross_weight_kg` | string | 총중량 | `12480` |
| `tare_weight_kg` | string | 차중량 | `7470` |
| `net_weight_kg` | string | 실중량 | `5010` |
| `is_valid` | string | 검증 통과 여부 | `TRUE` / `FALSE` |
| `validation_errors` | string | 검증 오류 (세미콜론 구분) | `missing_field:date; weight_mismatch` |
| `parse_warnings` | string | 파싱 경고 (세미콜론 구분) | `ambiguous_date_tail` |
| `imputation_notes` | string | 자동 복구 기록 (세미콜론 구분) | `imputed:net_weight=5010` |

### CSV 예시

```csv
filename,date,time,vehicle_no,gross_weight_kg,tare_weight_kg,net_weight_kg,is_valid,validation_errors,parse_warnings,imputation_notes
sample_01.json,2026-02-02,09:12,8713,12480,7470,5010,TRUE,,,
sample_02.json,2026-02-02,09:11,0580,13460,7560,5900,TRUE,,,
sample_03.json,2026-02-02,09:20,0580,13460,7560,,TRUE,,,"recovered:net_weight=5900 from candidates"
sample_04.json,,,8713,,,,,FALSE,missing_required_field:date; missing_required_field:vehicle_no,,
```

---

## 텍스트 파일 형식

### 원문 텍스트 (`*_raw.txt`)

- 원본 JSON에서 추출한 OCR 텍스트 그대로
- 인코딩: UTF-8
- 줄바꿈: LF (`\n`)

### 정규화 텍스트 (`*_normalized.txt`)

- 전처리 규칙이 적용된 텍스트
- 인코딩: UTF-8
- 줄바꿈: LF (`\n`)
- 변경사항:
  - 빈 줄 제거
  - 연속 공백 정규화
  - 전각 문자 → 반각 변환
  - OCR 아티팩트 수정

---

## 파일 출력 순서

```
1. {stem}_raw.txt
2. {stem}_normalized.txt
3. {stem}_preprocess_log.json
4. {stem}_candidates.json
5. {stem}_extract_log.json
6. {stem}_resolved.json
7. {stem}_parsed.json
8. summary.csv (전체 파일 처리 후)
```

---

## 검증 규칙

### 필수 필드
- `date`: 필수
- `vehicle_no`: 필수

### 중량 검증
- 음수 불가
- 100톤(100,000kg) 초과 불가
- 총중량 >= 차중량
- 실중량 = 총중량 - 차중량 (허용 오차: max(10kg, 2%))

### 자동 복구
1. 실중량 누락 시 → 계산으로 채움
2. 중량 불일치 시 → 후보 풀에서 복구 시도
3. 복구 내역은 `imputation_notes`에 기록

---