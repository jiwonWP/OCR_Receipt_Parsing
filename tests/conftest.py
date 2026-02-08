import pytest
from typing import List, Dict, Any

# ExtractedCandidates.candidates 샘플 데이터
@pytest.fixture
def sample_candidates_list() -> List[Dict[str, Any]]:
    # 후보 항목 샘플 데이터
    return [
        {
            "field": "date",
            "value_raw": "2026-02-02",
            "method": "label",
            "score": 10,
            "source_line": "날짜: 2026-02-02"
        },
        {
            "field": "date",
            "value_raw": "2026-02-01",
            "method": "pattern",
            "score": 5,
            "source_line": "2026-02-01 11:55:35"
        },
        {
            "field": "gross_weight_kg",
            "value_raw": "12,480 kg",
            "method": "label",
            "score": 10,
            "source_line": "총중량: 12,480 kg"
        },
        {
            "field": "tare_weight_kg",
            "value_raw": "7,470 kg",
            "method": "label",
            "score": 10,
            "source_line": "차중량: 7,470 kg"
        },
        {
            "field": "net_weight_kg",
            "value_raw": "5,010 kg",
            "method": "label",
            "score": 10,
            "source_line": "실중량: 5,010 kg"
        },
    ]


@pytest.fixture
def sample_weight_candidates_kg() -> List[int]:
    # 중량 후보 샘플 데이터
    return [12480, 7470, 5010, 14080, 13950, 130]


@pytest.fixture
def sample_preprocessed_text() -> str:
    return """날짜: 2026-02-02
차량번호: 80구8713
총중량: 02:07 13,460 kg
차중량: 02:13 7,560 kg
실중량: 5,900 kg
2026-02-02 02:14:23
37.718114,126.844940"""


@pytest.fixture
def sample_raw_ocr_text() -> str:
    return """날 짜: 2026-02-02-00004
차번호: 80구8713
구 분: 입고
총중량: 02 : 07 13 460 kg
차중량: 02 : 13 7 560 kg
실중량: 5 900 kg
2026-02-02 02:14:23
37.718114, 126.844940"""