# tests/ 디렉토리

OCR 파싱 파이프라인 단위 테스트 모음

## 테스트 파일

| 파일 | 테스트 대상 | 우선순위 | 테스트 수 |
|------|------------|---------|----------|
| `test_normalizers.py` | 정규화 함수 (중량, 시간, 날짜) | 🔥 High | 30+ |
| `test_validators.py` | 도메인 검증 및 복구 로직 | 🔥 High | 15+ |
| `test_utils.py` | 유틸리티 함수 | 🟡 Medium | 15+ |
| `test_preprocessor.py` | 전처리 엔진 | 🟡 Medium | 15+ |
| `test_config.py` | 설정 및 정책 | 🟢 Low | 10+ |

## 실행 방법

```bash
# 전체 테스트
pytest tests/

# 특정 파일
pytest tests/test_normalizers.py

# 커버리지 포함
pytest --cov=src tests/
```

자세한 내용은 루트의 `README_TEST.md` 참조.