#  OCR TEXT Parsing

계근지(차량의 총중량/공차/실중량 등을 포함한 영수증 형태)의 OCR 결과 텍스트를 입력으로 받아, 
**원문 보존을 전제로 전처리(정규화)** 하는 프로젝트입니다.

> 설계 의도, 단계별 책임 범위, 전처리 규칙 명세, 샘플 전수 분석 등  
> **상세한 근거/설명은 `docs/` 폴더에 모두 정리되어 있습니다.**

특히 다음 문서를 중심으로 확인할 수 있습니다.

- `docs/architecture.md`
- `docs/preprocess_spec.md`
- `docs/data_audit.md`
- `docs/sprint.md`
- `docs/README_docs.md`

---

# 실행 방법

## 1️. 가상환경 생성 및 활성화

```bash
python -m venv venv
source venv/Scripts/activate   # Windows (Git Bash)
```
## 2. 의존성 설치
```bash
pip install -r requirements.txt
```

## 3. 전처리 실행 
```bash
python -m src.main
```

# 입출력
## 입력 데이터
- OCR 원문 JSON 파일
- Loader 단계에서 **원문 그대로 보존** 후 처리

## 출력 데이터 (`data/processed/`)
| 파일명 | 설명 |
|------------------------------|----------------------------------|
| sample_0X_raw.txt | OCR 원문 텍스트 (원문 그대로 보존) |
| sample_0X_normalized.txt | 전처리(정규화) 완료 텍스트 |
| sample_0X_preprocess_log.json | 적용 규칙(`applied_rules`) 및 경고(`warnings`) 로그 |
| sample_0X_candidates.json | 추출된 후보 목록 |  
| sample_0X_extract_log.json | 추출 단계 로그 | 
| sample_0X_resolved.json | 후보 선택 결과 |
| sample_0X_parsed.json | 최종 파싱 결과 (검증 완료) | 
| summary.csv | 전체 샘플 요약 (CSV) | 

---

# 의존성 / 실행 환경

## 실행 환경

| 항목 | 요구 사항 |
|--------|----------------|
| Python | 3.10 이상 |
| OS | Windows 10/11 (개발 기준) |
| 실행 방식 | `python -m src.main` |

---

## 설치 라이브러리
- pip install -r requirements.txt
    - Pydantic 
    - pytest
    - regex
    - python-dateutil
    - pandas

---

## 폴더 구조
```bash
root/
├── data/
│   ├── raw/                    # 원본 OCR JSON 샘플
│   └── processed/              # 전처리/중간 산출물
├── docs/
│   ├── data_audit.md           # 샘플 Json 전수 조사
│   ├── architecture.md         # 파이프라인 아키텍처 설계 문서
│   ├── sprint.md               # sprint 단위 작업 문서
│   ├── preprocess_spec.md      # Loader -> Preprocessor 정규화 함수 명세
│   └── README_docs.md          # docs 인덱스
├── src/
│   ├── __init__.py
│   ├── main.py                 # 실행 엔트리(실행은 python -m src.main 권장)
│   ├── pipeline.py             # Loader→Preprocess→Extract→Validate→Export 흐름
│   ├── loader.py
│   ├── preprocessor.py         # 전처리(공백/오타/시각혼동 문자 보정 등)
│   ├── extractor.py            # 다중 전략(label_match/pattern_fallback)
│   ├── normalizer.py           # 타입 변환(int, ISO date/time 등)
│   ├── validator.py            # Validation & Recovery(imputation 포함)
│   ├── exporter.py             # JSON/CSV 출력
│   ├── schema.py               # Pydantic 모델(ExtractionMetadata 포함)
│   └── constants.py            # fuzzy map, regex pattern 상수
├── tests/
│   ├── test_preprocess.py
│   ├── test_extract.py
│   └── test_validate.py
├── outputs/
├── requirements.txt
├── README.md
└── .gitignore
```
---

# 설계 및 주요 가정

### Loader
- JSON 원문을 **절대 변형하지 않음**
- `text` → `raw_text` 그대로 보존
- 디버깅 / 재현 / 규칙 개선의 기준 데이터 역할
- Loader 단계에서 정규화/치환 금지

---

### Preprocessor
- 목표: **의미 해석이 아닌 형태 통일**
- 날짜 suffix → 삭제 ❌ / `doc_seq` 분리 ⭕
- 날짜 뒤 숫자 꼬리 → 시간 단정 ❌ / `raw_tail` 보존 ⭕
- 총/차/실 중량 의미 확정은 이후 단계(Extractor/Validator)에서 처리

=>  **"형태만 정규화, 의미는 건드리지 않는다" 원칙**

---

### 보수적 정규화 전략 (과치환 방지)
- 숫자 결합은 전역 처리 ❌ → `kg` 근처에서만 제한적으로 수행
- OCR 문맥을 고려한 최소 치환 전략 적용
- 적용된 규칙만 `applied_rules`에 기록하여 추적 가능성 유지

상세 규칙 및 Before/After 예시는  
`docs/preprocess_spec.md` 참고

---

# 문서(상세 근거) 안내

| 문서 | 내용 |
|----------------------|----------------------------------------------|
| architecture.md | 단계별 책임/비책임 범위 및 파이프라인 설계 |
| preprocess_spec.md | 전처리 규칙 명세 (순서, Before/After, 로그 정책 포함) |
| data_audit.md | 샘플 OCR 전수 조사 및 노이즈 유형 분석 |
| sprint.md | Sprint 계획 및 진행 맥락 |
| README_docs.md | 문서 인덱스 |
