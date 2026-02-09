# 테스트 실행 가이드

## 테스트 환경 설정

```bash
# 테스트 의존성 설치
pip install -r requirements-test.txt
```

## 테스트 실행

### 전체 테스트 실행
```bash
pytest tests/
```

### 특정 파일만 테스트
```bash
pytest tests/test_normalizers.py
pytest tests/test_validators.py
pytest tests/test_utils.py
pytest tests/test_config.py
pytest tests/test_preprocessor.py
```

### 특정 테스트 클래스만 실행
```bash
pytest tests/test_normalizers.py::TestNormalizeWeightKg
pytest tests/test_validators.py::TestValidateAndRecover
```

### 특정 테스트 함수만 실행
```bash
pytest tests/test_normalizers.py::TestNormalizeWeightKg::test_simple_integer
```

### 상세 출력 모드
```bash
pytest -v
```

### 실패한 테스트만 재실행
```bash
pytest --lf
```

### 커버리지 리포트 생성
```bash
pytest --cov=src --cov-report=html
```

커버리지 리포트는 `htmlcov/index.html`에서 확인 가능합니다.

## 테스트 구조

```
tests/
├── __init__.py
├── conftest.py            # 공통 fixture
├── test_normalizers.py    # 정규화 함수 테스트 🔥
├── test_validators.py     # 검증 로직 테스트 🔥
├── test_utils.py          # 유틸리티 함수 테스트 🟡
├── test_preprocessor.py   # 전처리 엔진 테스트 🟡
└── test_config.py         # 설정/정책 테스트 🟢

pytest.ini                 # pytest 설정 (루트)
requirements-test.txt      # 테스트 의존성 (루트)
```

## 테스트 작성 가이드

### 1. 명명 규칙
- 테스트 파일: `test_<module_name>.py`
- 테스트 클래스: `Test<FunctionName>`
- 테스트 함수: `test_<scenario>`

### 2. 테스트 구조
```python
class TestMyFunction:
    """MyFunction 테스트"""
    
    def test_normal_case(self):
        """정상 케이스"""
        result = my_function("input")
        assert result == "expected"
    
    def test_edge_case(self):
        """엣지 케이스"""
        result = my_function("")
        assert result is None
    
    def test_invalid_input(self):
        """유효하지 않은 입력"""
        with pytest.raises(ValueError):
            my_function(None)
```

### 3. Fixture 사용
```python
def test_with_fixture(sample_candidates_list):
    """공통 fixture 사용"""
    result = process(sample_candidates_list)
    assert result is not None
```

## 현재 테스트 커버리지

| 모듈 | 테스트 대상 | 테스트 개수 | 우선순위 |
|------|------------|------------|---------|
| `normalizers.py` | 정규화 함수 | 30+ | 🔥 High |
| `validators.py` | 검증/복구 로직 | 15+ | 🔥 High |
| `utils.py` | 유틸리티 함수 | 15+ | 🟡 Medium |
| `preprocessor.py` | 전처리 엔진 | 15+ | 🟡 Medium |
| `config.py` | 설정/정책 | 10+ | 🟢 Low |

**총 테스트 개수: 85+**

## 주요 테스트 시나리오

### normalizers.py
-  중량 정규화 (쉼표, 공백, 괄호, kg 접미사)
-  시간 정규화 (HH:MM, 한글 시간, 괄호)
-  날짜 정규화 (다양한 구분자, suffix, 유효성)

### validators.py
-  필수 필드 검증
-  중량 범위 검증 (음수, 비현실적 값)
-  중량 관계 검증 (총-차=실, 허용 오차)
-  실중량 자동 계산/복구
-  후보 기반 중량 복구

### utils.py
-  중량 포맷팅
-  후보 요약 통계
-  중량 관계식 요약

### preprocessor.py
-  빈 줄 제거
-  공백/괄호/문장부호 정규화
-  전각→반각 변환
-  연결된 필드 분리
-  OCR 아티팩트 정규화
-  규칙 실행 순서 추적

### config.py
-  검증 정책 (허용 오차 계산)
-  라벨 토큰 정의
-  정규식 패턴