# 문서 인덱스

##  문서 개요

본 프로젝트의 문서는 **설계 → 명세 → 실행 → 테스트** 흐름에 따라 구성되어 있습니다.

---

##  문서 목록

### 1. 시스템 설계 문서

#### **architecture.md**
- **목적**: 전체 시스템 아키텍처 설계
- **내용**:
  - 4단계 파이프라인 (Loader → Preprocessor → Extractor → Resolver → Validator)
  - 모듈별 책임과 역할
  - 데이터 흐름
  - 설계 원칙
- **읽어야 할 때**: 시스템 전체 구조를 이해하고 싶을 때

---

#### **PROJECT_STRUCTURE.md**
- **목적**: 프로젝트 폴더 구조 및 파일 설명
- **내용**:
  - 디렉토리 구조
  - 모듈별 책임 분리
  - 테스트 구조
  - Sprint 5 성과
- **읽어야 할 때**: 어떤 파일이 어디에 있는지 찾을 때

---

#### **data_audit.md**
- **목적**: OCR 샘플 전수 조사 결과
- **내용**:
  - 샘플 4개 분석 결과
  - 공통 노이즈 유형
  - 기술적 가정 및 근거
  - Preprocessor 설계 근거
- **읽어야 할 때**: 왜 이런 전처리 규칙이 필요한지 이해하고 싶을 때

---

### 2. 상세 명세 문서

#### **preprocess_spec.md**
- **목적**: 전처리 규칙 상세 명세
- **내용**:
  - 11가지 전처리 규칙
  - 실행 순서
  - Before/After 예시
  - 구현 코드 예시
  - 테스트 케이스
- **읽어야 할 때**: 전처리 규칙을 추가하거나 수정할 때

---

#### **OUTPUT_SPEC.md**
- **목적**: 출력 파일 형식 명세
- **내용**:
  - 파일명 규칙
  - JSON 스키마
  - CSV 형식
  - 검증 규칙
- **읽어야 할 때**: 출력 파일 형식을 확인하거나 변경할 때

---

### 3. 실행 가이드 문서

#### **CLI_GUIDE.md**
- **목적**: CLI 실행 및 사용 가이드
- **내용**:
  - 실행 방법
  - 실행 흐름
  - 상태 심볼
  - 로그 레벨
  - 에러 처리
  - 문제 해결
- **읽어야 할 때**: 파이프라인을 실행하거나 로그를 확인할 때

---

#### **README_TEST.md**
- **목적**: 테스트 실행 가이드
- **내용**:
  - 테스트 환경 설정
  - 테스트 실행 방법
  - 테스트 구조
  - 커버리지
  - 테스트 작성 가이드
- **읽어야 할 때**: 테스트를 실행하거나 작성할 때

---

### 4. 계획 문서

#### **sprint.md**
- **목적**: Sprint 계획 및 진행 상황
- **내용**:
  - Sprint 1-6 계획
  - 각 Sprint 목표 및 작업
  - 산출물
- **읽어야 할 때**: 프로젝트 진행 계획을 확인할 때

---

##  폴더 구조

```
docs/
├── architecture.md           # 시스템 아키텍처
├── CLI_GUIDE.md              # CLI 사용 가이드
├── data_audit.md             # OCR 샘플 전수 조사
├── OUTPUT_SPEC.md            # 출력 파일 명세
├── preprocess_spec.md        # 전처리 규칙 명세
├── PROJECT_STRUCTURE.md      # 프로젝트 구조
├── README_docs.md            # 문서 인덱스 (본 파일)
├── README_TEST.md            # 테스트 가이드
└── sprint.md                 # Sprint 계획
```

---

## 🔍 상황별 문서 찾기

### "어떻게 실행하나요?"
→ [CLI_GUIDE.md](CLI_GUIDE.md)

### "전처리 규칙이 뭐가 있나요?"
→ [preprocess_spec.md](preprocess_spec.md)

### "출력 파일은 어떤 형식인가요?"
→ [OUTPUT_SPEC.md](OUTPUT_SPEC.md)

### "전체 시스템 구조를 알고 싶어요"
→ [architecture.md](architecture.md)

### "어떤 파일이 어디에 있나요?"
→ [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)

### "왜 이런 전처리가 필요한가요?"
→ [data_audit.md](data_audit.md)

### "테스트는 어떻게 실행하나요?"
→ [README_TEST.md](README_TEST.md)

### "프로젝트 계획이 궁금해요"
→ [sprint.md](sprint.md)

---

##  주요 참조 경로

### 설계 흐름
```
data_audit.md → preprocess_spec.md → architecture.md
```

### 실행 흐름
```
PROJECT_STRUCTURE.md → CLI_GUIDE.md → OUTPUT_SPEC.md
```

### 개발 흐름
```
architecture.md → preprocess_spec.md → README_TEST.md
```

---

##  빠른 시작

```bash
# 1. 프로젝트 구조 확인
cat docs/PROJECT_STRUCTURE.md

# 2. 실행 방법 확인
cat docs/CLI_GUIDE.md

# 3. 실행
python -m src.main

# 4. 결과 확인
cat outputs/summary.csv
```

---